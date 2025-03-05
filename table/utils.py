import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.timezone import now
from .models import Table, TableInvoice
from sale.models import Sale


def generate_table_invoice(table_id):
    """
    Generate a PDF invoice for a given table and save it to the media folder.
    """
    table = Table.objects.get(id=table_id)
    sales = Sale.objects.filter(table=table, status="completed")

    if not sales.exists():
        raise ValueError("No completed sales found for this table.")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Invoice_Table_{table.table_number}")

    # Invoice Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "TABLE INVOICE (SENIAT COMPLIANT)")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 770, f"Table: {table.table_number}")
    pdf.drawString(50, 750, f"Date: {now().strftime('%Y-%m-%d')}")
    pdf.drawString(400, 750, f"Invoice No: INV-T{table.table_number}-{table.id}")

    # Table Headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Product")
    pdf.drawString(250, 700, "Quantity")
    pdf.drawString(350, 700, "Price")
    pdf.drawString(450, 700, "Subtotal")
    pdf.line(50, 695, 550, 695)

    # Order Items
    y_position = 670
    total = 0
    tax_total = 0
    tax_details = {}

    for sale in sales:
        for item in sale.items.all():
            subtotal = item.quantity * item.price_at_sale
            tax_amount = subtotal * (item.product.tax_rate / 100)
            total += subtotal
            tax_total += tax_amount

            # Collect tax breakdown
            tax_label = f"{item.product.tax_rate}% Tax"
            tax_details[tax_label] = tax_details.get(tax_label, 0) + tax_amount

            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, y_position, item.product.name)
            pdf.drawString(250, y_position, str(item.quantity))
            pdf.drawString(350, y_position, f"${item.price_at_sale:.2f}")
            pdf.drawString(450, y_position, f"${subtotal:.2f}")
            y_position -= 20

            # Handle page breaks
            if y_position <= 50:
                pdf.showPage()
                y_position = 770
                pdf.setFont("Helvetica", 12)

    # Total and Taxes
    pdf.line(50, y_position - 10, 550, y_position - 10)
    pdf.setFont("Helvetica-Bold", 12)

    for tax_label, amount in tax_details.items():
        y_position -= 30
        pdf.drawString(300, y_position, tax_label + ":")
        pdf.drawString(450, y_position, f"${amount:.2f}")

    pdf.drawString(300, y_position - 40, "Total:")
    pdf.drawString(450, y_position - 40, f"${total + tax_total:.2f}")

    # Save PDF
    pdf.save()
    buffer.seek(0)

    # Save invoice file
    invoice_filename = f"invoice_table_{table.id}.pdf"
    invoice_path = os.path.join(settings.MEDIA_ROOT, "invoices", invoice_filename)

    try:
        with open(invoice_path, "wb") as f:
            f.write(buffer.getvalue())
    except IOError as e:
        raise IOError(f"Failed to save invoice PDF: {str(e)}")

    # Save invoice model
    invoice, created = TableInvoice.objects.update_or_create(
        table=table,
        defaults={
            "total_amount": total + tax_total,
            "invoice_number": f"INV-T{table.table_number}-{table.id}-{now().strftime('%Y%m%d%H%M%S')}",
            "tax_details": tax_details,
            "pdf_file": invoice_path,
        }
    )

    # Generate control code
    invoice.generate_control_code()
    invoice.calculate_total()

    return invoice

def send_invoice_email(invoice_id, recipient_email):
    """
    Send the generated invoice to the customer via email.
    """
    invoice = TableInvoice.objects.get(id=invoice_id)
    subject = f"Your Invoice - Table {invoice.table.table_number}"
    message = f"""
    Dear Customer,

    Thank you for dining with us! 
    Attached is your invoice for Table {invoice.table.table_number}.

    Invoice No: {invoice.invoice_number}
    Total Amount: ${invoice.total_amount:.2f}

    SENIAT Control Code: {invoice.control_code}

    Regards,
    The Restaurant Team
    """

    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
    email.attach_file(invoice.pdf_file.path)
    email.send()
