import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.conf import settings
from django.db.models import Sum, Count
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import TruncDate
from sale.models import  Sale, SaleItem
from .models import SalesReport
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist

from django.conf import settings
from .models import ExchangeRate

from lxml import etree
from cryptography.hazmat.primitives import serialization  # ✅ Fix the import path
from cryptography.hazmat.primitives.asymmetric import padding  # ✅ Keep padding separate
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
from transactions.models import Invoice
from celery import shared_task


def generate_monthly_sales_report():
    """
    Generate a sales report for the current month.
    """
    today = now().date()
    first_day_of_month = today.replace(day=1)

    # Get all completed orders for the current month
    orders = Sale.objects.filter(status="completed", created_at__date__gte=first_day_of_month)

    total_orders = orders.count()
    total_revenue = orders.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

    # Get best-selling products
    best_selling_products = (
        SaleItem.objects
        .filter(order__status="completed", order__created_at__date__gte=first_day_of_month)
        .values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    # Get daily order breakdown
    daily_orders = (
        orders.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(order_count=Count("id"), revenue=Sum("total_amount"))
        .order_by("date")
    )

    report = {
        "month": today.strftime("%B %Y"),
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "best_selling_products": list(best_selling_products),
        "daily_orders": list(daily_orders),
    }

    return report

def generate_sales_report_pdf():
    """
    Generate a monthly sales report as a PDF and save it to the media folder.
    """
    today = now().date()
    first_day_of_month = today.replace(day=1)

    # Get sales data
    orders = Sale.objects.filter(status="completed", created_at__date__gte=first_day_of_month)
    total_orders = orders.count()
    total_revenue = orders.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

    # Get best-selling products
    best_selling_products = (
        SaleItem.objects
        .filter(order__status="completed", order__created_at__date__gte=first_day_of_month)
        .values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    # Create a PDF file
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Sales_Report_{today.strftime('%B_%Y')}")

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, f"Sales Report - {today.strftime('%B %Y')}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 770, f"Total Orders: {total_orders}")
    pdf.drawString(50, 750, f"Total Revenue: ${total_revenue:.2f}")

    # Best-Selling Products
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 720, "Best-Selling Products:")
    y_position = 700

    for product in best_selling_products:
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y_position, f"{product['product__name']} - {product['total_sold']} sold")
        y_position -= 20

    # Save PDF
    pdf.save()
    buffer.seek(0)

    # Save report file
    report_filename = f"sales_report_{today.strftime('%B_%Y')}.pdf"
    report_path = os.path.join(settings.MEDIA_ROOT, "reports", report_filename)

    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "wb") as f:
        f.write(buffer.getvalue())

    return f"{settings.MEDIA_URL}reports/{report_filename}"

def generate_invoice(order_id):
    """
    Generate a PDF invoice for a given order and save it to the media folder.
    """
    try:
        order = Sale.objects.get(id=order_id)
    except ObjectDoesNotExist:
        return None  # Return None instead of crashing

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Invoice_{order.id}")

    # Invoice Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "INVOICE")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 770, f"Order ID: {order.id}")
    pdf.drawString(50, 750, f"Customer: {order.customer_name}")
    pdf.drawString(50, 730, f"Date: {order.created_at.strftime('%Y-%m-%d')}")

    # Save PDF
    pdf.save()
    buffer.seek(0)

    # Save invoice file
    invoice_filename = f"invoice_{order.id}.pdf"
    invoice_path = os.path.join(settings.MEDIA_ROOT, "invoices", invoice_filename)

    with open(invoice_path, "wb") as f:
        f.write(buffer.getvalue())

    return f"{settings.MEDIA_URL}invoices/{invoice_filename}"

def send_invoice_email(order_id):
    """
    Send an invoice email with a PDF attachment to the customer.
    """
    order = Sale.objects.get(id=order_id)
    
    if not order:
        print(f"❌ Order {order_id} not found.")
        return False

    # Generate invoice if it doesn't exist
    invoice_url = generate_invoice(order_id)

    # Get the absolute file path
    invoice_path = os.path.join(settings.MEDIA_ROOT, "invoices", f"invoice_{order.id}.pdf")

    # Email content
    subject = f"Invoice for Order {order.id}"
    message = f"""
    Dear {order.customer_name},

    Thank you for your purchase! Your order (ID: {order.id}) has been completed.
    Please find your invoice attached.

    Regards,
    SuitAdmin Team
    """
    recipient_list = [order.customer_email] if order.customer_email else []
    if not recipient_list:
        print(f"❌ No email found for Order {order.id}. Skipping email sending.")
        return False

    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    
    # Attach the PDF invoice
    if os.path.exists(invoice_path):
        email.attach_file(invoice_path)
    else:
        print(f"❌ Invoice file not found: {invoice_path}")
        return False

    # Send email
    email.send()
    print(f"✅ Invoice email sent for Order {order.id}")
    return True

def generate_sales_report():
    """
    Generate a sales report for the current month, save it in the database, and generate a PDF.
    """
    print("🔍 Generating sales report...")  # ✅ Debugging
    today = now().date()
    first_day_of_month = today.replace(day=1)
    month_name = today.strftime("%B %Y")  # e.g., "February 2025"

    try:
        # ✅ Check if the report already exists for this month
        report, created = SalesReport.objects.get_or_create(month=month_name)
        print("✅ Report exists:", created)  # ✅ Debugging

        # ✅ Get sales data
        orders = Sale.objects.filter(status="completed", created_at__date__gte=first_day_of_month)
        total_orders = orders.count()
        total_revenue = orders.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

        # ✅ Get best-selling products
        best_selling_products = (
            SaleItem.objects
            .filter(order__status="completed", order__created_at__date__gte=first_day_of_month)
            .values("product__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        best_selling_products_list = list(best_selling_products)
        print("✅ Best-selling products:", best_selling_products_list)  # ✅ Debugging

        # ✅ Save sales data in the database
        report.total_orders = total_orders or 0
        report.total_revenue = total_revenue or 0.00
        report.best_selling_products = best_selling_products_list

        # ✅ Generate PDF report
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle(f"Sales_Report_{month_name}")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, 800, f"Sales Report - {month_name}")

        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, 770, f"Total Orders: {total_orders}")
        pdf.drawString(50, 750, f"Total Revenue: ${total_revenue:.2f}")

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 720, "Best-Selling Products:")
        y_position = 700

        for product in best_selling_products_list:
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, y_position, f"{product['product__name']} - {product['total_sold']} sold")
            y_position -= 20

        pdf.save()
        buffer.seek(0)

        # ✅ Save PDF file
        report_filename = f"sales_report_{month_name}.pdf"
        report_path = os.path.join(settings.MEDIA_ROOT, "reports", report_filename)

        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, "wb") as f:
            f.write(buffer.getvalue())

        report.pdf_report.name = f"reports/{report_filename}"
        report.save()
        print("✅ Sales report saved successfully!")  # ✅ Debugging

        return report

    except Exception as e:
        print("❌ Error generating sales report:", str(e))  # ✅ Debugging
        return None

def generate_invoice_pdf(invoice_id):
    """
    Generate a PDF invoice and return its file path.
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_path = os.path.join(settings.MEDIA_ROOT, "invoices", pdf_filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Generate PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, f"Invoice: {invoice.invoice_number}")
        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Customer: {invoice.customer_name}")
        c.drawString(100, 710, f"Total Amount: {invoice.total_amount} {invoice.currency}")
        c.drawString(100, 690, f"Status: {invoice.status}")
        c.drawString(100, 670, f"Date: {invoice.created_at.strftime('%Y-%m-%d')}")

        c.showPage()
        c.save()

        return pdf_path
    except Invoice.DoesNotExist:
        return None

def generate_seniat_invoice_xml(invoice):
    """
    Generate an XML invoice following SENIAT's electronic invoicing standard.
    """
    try:
        root = etree.Element("Invoice")
        etree.SubElement(root, "InvoiceNumber").text = invoice.invoice_number
        etree.SubElement(root, "CustomerName").text = invoice.customer_name
        etree.SubElement(root, "TotalAmount").text = str(invoice.total_amount)
        etree.SubElement(root, "Currency").text = invoice.currency
        etree.SubElement(root, "Status").text = invoice.status
        etree.SubElement(root, "CreatedAt").text = invoice.created_at.strftime("%Y-%m-%d")

        # Tax Information
        tax_info = etree.SubElement(root, "TaxInformation")
        etree.SubElement(tax_info, "VAT").text = "16%"  
        etree.SubElement(tax_info, "TaxAmount").text = f"{float(invoice.total_amount) * 0.16:.2f}"

        # ✅ Save XML file
        xml_filename = f"invoice_{invoice.invoice_number}.xml"
        xml_path = os.path.join(settings.MEDIA_ROOT, "invoices", xml_filename)

        os.makedirs(os.path.dirname(xml_path), exist_ok=True)

        with open(xml_path, "wb") as xml_file:
            xml_file.write(etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8"))

        invoice.seniat_xml_file.name = f"invoices/{xml_filename}"
        invoice.save()

        return xml_path
    except Exception as e:
        print(f"Error generating XML: {e}")
        return None


def sign_seniat_invoice(xml_path):
    """
    Digitally sign an XML invoice using a private key.
    """
    try:
        private_key_path = os.path.join(settings.BASE_DIR, "private_key.pem")

        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

        with open(xml_path, "rb") as xml_file:
            data = xml_file.read()

        signature = private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        signature_path = xml_path.replace(".xml", "_signature.sig")
        with open(signature_path, "wb") as sig_file:
            sig_file.write(signature)

        return signature_path
    except Exception as e:
        print(f"Error signing invoice: {e}")
        return None

EXCHANGE_RATE_API_URL = "https://v6.exchangerate-api.com/v6/{}/latest/USD"

@shared_task
def fetch_live_exchange_rates():
    """
    Celery task to fetch live exchange rates and update the database.
    """
    api_key = settings.EXCHANGE_RATE_API_KEY
    url = EXCHANGE_RATE_API_URL.format(api_key)

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and "conversion_rates" in data:
            rates = data["conversion_rates"]

            # Update exchange rates for Bolívares and Euros
            for currency in ["Bs", "EUR"]:
                if currency in rates:
                    exchange_rate, created = ExchangeRate.objects.update_or_create(
                        target_currency=currency,
                        defaults={"rate": rates[currency]}
                    )
                    print(f"Updated {currency} rate: {exchange_rate.rate}")
            return True
        else:
            print(f"Error fetching exchange rates: {data}")
            return False
    except Exception as e:
        print(f"Failed to fetch exchange rates: {e}")
        return False
    
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
            invoice.transmission_status = "submitted"
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
