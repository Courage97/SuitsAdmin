from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from transactions.models import Invoice
import os
from transactions.models import ExchangeRate
import requests


def generate_invoice_pdf(invoice_id):
    """
    Generate a PDF invoice and save it to the media folder.
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        file_path = os.path.join(settings.MEDIA_ROOT, "invoices", f"invoice_{invoice.invoice_number}.pdf")

        c = canvas.Canvas(file_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, f"Invoice: {invoice.invoice_number}")
        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Customer: {invoice.customer_name}")
        c.drawString(100, 710, f"Total Amount: {invoice.total_amount} {invoice.currency}")
        c.drawString(100, 690, f"Status: {invoice.status}")
        c.drawString(100, 670, f"Date: {invoice.created_at.strftime('%Y-%m-%d')}")

        c.showPage()
        c.save()

        return file_path  # Return file path for download
    except Invoice.DoesNotExist:
        return None


def send_invoice_email(invoice_id):
    """
    Generate an invoice PDF and email it to the customer.
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        pdf_path = generate_invoice_pdf(invoice_id)

        if not pdf_path or not os.path.exists(pdf_path):
            return False, "PDF file not found"

        subject = f"Invoice {invoice.invoice_number} - Payment Details"
        message = f"""
        Dear {invoice.customer_name},

        Please find your invoice attached.

        Total: {invoice.total_amount} {invoice.currency}
        Status: {invoice.status}

        Best Regards,
        Your Company
        """

        email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [invoice.user.email])
        email.attach_file(pdf_path)
        email.send()

        return True, "Email sent successfully"
    except Invoice.DoesNotExist:
        return False, "Invoice not found"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"


