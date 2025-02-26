import requests
import os
from django.conf import settings
from ..billing.models import Invoice
from ..billing.utils import generate_seniat_invoice_xml, sign_seniat_invoice

SENIAT_API_URL = "https://api.seniat.gob.ve/invoice/transmit"  # Replace with actual endpoint

def send_invoice_to_seniat(invoice_id):
    """
    Transmit a digitally signed invoice to SENIAT's API.
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id)

        # ✅ Generate & Sign XML Invoice
        xml_path = generate_seniat_invoice_xml(invoice_id)
        signature_path = sign_seniat_invoice(xml_path)

        if not xml_path or not os.path.exists(xml_path):
            return {"error": "XML invoice file not found"}

        if not signature_path or not os.path.exists(signature_path):
            return {"error": "Digital signature file not found"}

        # ✅ Read XML & Signature
        with open(xml_path, "rb") as xml_file:
            xml_data = xml_file.read()

        with open(signature_path, "rb") as sig_file:
            signature_data = sig_file.read()

        # ✅ Prepare API Payload
        payload = {
            "invoice_number": invoice.invoice_number,
            "customer_name": invoice.customer_name,
            "total_amount": str(invoice.total_amount),
            "currency": invoice.currency,
        }
        files = {
            "invoice_xml": ("invoice.xml", xml_data, "application/xml"),
            "signature": ("signature.sig", signature_data, "application/octet-stream"),
        }

        headers = {
            "Authorization": f"Bearer {settings.SENIAT_API_KEY}",  # Authentication Key
            "Accept": "application/json",
        }

        # ✅ Send Request
        response = requests.post(SENIAT_API_URL, data=payload, files=files, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            invoice.seniat_control_code = response_data.get("control_code")
            invoice.transmission_status = "sent"
            invoice.seniat_response = str(response_data)
            invoice.save()
            return {"success": "Invoice transmitted successfully", "control_code": invoice.seniat_control_code}
        else:
            invoice.transmission_status = "failed"
            invoice.seniat_response = response.text
            invoice.save()
            return {"error": "Failed to transmit invoice", "response": response.text}

    except Invoice.DoesNotExist:
        return {"error": "Invoice not found"}
    except Exception as e:
        return {"error": str(e)}
