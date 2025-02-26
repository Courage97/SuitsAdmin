import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.conf import settings
from .models import Order
from django.core.mail import EmailMessage

def generate_invoice(order_id):
    """
    Generate a PDF invoice for a given order and save it to the media folder.
    """
    order = Order.objects.get(id=order_id)
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

    # Table Headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Product")
    pdf.drawString(300, 700, "Quantity")
    pdf.drawString(400, 700, "Price")

    pdf.line(50, 695, 550, 695)

    # Order Items
    y_position = 670
    total = 0

    for item in order.items.all():
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y_position, item.product.name)
        pdf.drawString(300, y_position, str(item.quantity))
        pdf.drawString(400, y_position, f"${item.price_at_purchase:.2f}")  # ✅ Use price at purchase
        total += item.quantity * item.price_at_purchase  # ✅ Use correct price
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
    invoice_filename = f"invoice_{order.id}.pdf"
    invoice_path = os.path.join(settings.MEDIA_ROOT, "invoices", invoice_filename)

    with open(invoice_path, "wb") as f:
        f.write(buffer.getvalue())

    return f"{settings.MEDIA_URL}invoices/{invoice_filename}"

def send_invoice_email(order_id):
    """
    Send an invoice email with a PDF attachment to the customer.
    """
    order = Order.objects.get(id=order_id)
    
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
