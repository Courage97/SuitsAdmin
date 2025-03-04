import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.conf import settings
from django.core.mail import EmailMessage
from .models import Sale

def generate_invoice(sale_id):
    """
    Generate a PDF invoice for a given sale and save it to the media folder.
    """
    sale = Sale.objects.get(id=sale_id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Invoice_{sale.id}")

    # Invoice Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "INVOICE")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 770, f"Sale ID: {sale.id}")
    pdf.drawString(50, 750, f"Customer: {sale.customer_name}")
    pdf.drawString(50, 730, f"Date: {sale.created_at.strftime('%Y-%m-%d')}")

    # Table Headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Product")
    pdf.drawString(300, 700, "Quantity")
    pdf.drawString(400, 700, "Price")

    pdf.line(50, 695, 550, 695)

    # Sale Items
    y_position = 670
    total = 0

    for item in sale.items.all():
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y_position, item.product.name)
        pdf.drawString(300, y_position, str(item.quantity))
        pdf.drawString(400, y_position, f"${item.price_at_sale:.2f}")
        total += item.quantity * item.price_at_sale
        y_position -= 20

    # Total Amount
    pdf.line(50, y_position - 10, 550, y_position - 10)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(300, y_position - 30, "Total:")
    pdf.drawString(400, y_position - 30, f"${total:.2f}")

    # Save PDF
    pdf.save()
    buffer.seek(0)

    # Save invoice file
    invoice_filename = f"invoice_{sale.id}.pdf"
    invoice_path = os.path.join(settings.MEDIA_ROOT, "invoices", invoice_filename)

    # Ensure the media path is correct
    if not os.path.exists(os.path.dirname(invoice_path)):
        os.makedirs(os.path.dirname(invoice_path))

    with open(invoice_path, "wb") as f:
        f.write(buffer.getvalue())

    # Return the correct media URL
    return f"/invoices/{invoice_filename}"


def send_invoice_email(sale_id):
    """
    Send an invoice email with a PDF attachment to the customer.
    """
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        print(f"❌ Sale {sale_id} not found.")
        return False

    if not sale.customer_email:
        print(f"❌ No email found for Sale {sale.id}. Skipping email sending.")
        return False

    # Generate invoice
    invoice_url = generate_invoice(sale_id)
    if not invoice_url:
        print(f"❌ Invoice generation failed for Sale {sale.id}.")
        return False

    # Get the absolute file path
    invoice_path = os.path.join(settings.MEDIA_ROOT, "invoices", f"invoice_{sale.id}.pdf")

    if not os.path.exists(invoice_path):
        print(f"❌ Invoice file not found: {invoice_path}")
        return False

    # Email content
    subject = f"Invoice for Sale {sale.id}"
    message = f"""
    Dear {sale.customer_name},

    Thank you for your purchase! Your sale (ID: {sale.id}) has been completed.
    Please find your invoice attached.

    Regards,
    SuitAdmin Team
    """

    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [sale.customer_email])

    # Attach the PDF invoice
    try:
        email.attach_file(invoice_path)
        email.send()
        print(f"✅ Invoice email sent for Sale {sale.id} to {sale.customer_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False
