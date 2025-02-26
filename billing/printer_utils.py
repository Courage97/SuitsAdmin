        # Physical printer testing.

# from escpos.printer import Usb
# from .models import Invoice

# # ✅ Printer Configuration (Ensure these match your actual device)
# USB_VENDOR_ID = 0x04b8  # Example: Epson Vendor ID
# USB_PRODUCT_ID = 0x0202  # Example: Epson TM-T20II Product ID

# def print_invoice(invoice_id):
#     """
#     Print an invoice using an ESC/POS compatible thermal printer.
#     """
#     try:
#         # ✅ Attempt to connect to the printer
#         try:
#             printer = Usb(USB_VENDOR_ID, USB_PRODUCT_ID)
#         except Exception as e:
#             return {"error": f"Printer connection failed: {str(e)}"}

#         # ✅ Fetch the invoice
#         invoice = Invoice.objects.get(id=invoice_id)

#         # ✅ Print Header
#         printer.set(align="center", bold=True, double_height=True, double_width=True)
#         printer.text("SUITADMIN SYSTEM\n")
#         printer.text("======================\n")

#         # ✅ Print Invoice Details
#         printer.set(align="left", bold=False, double_height=False, double_width=False)
#         printer.text(f"Invoice No: {invoice.invoice_number}\n")
#         printer.text(f"Customer: {invoice.customer_name}\n")
#         printer.text(f"Date: {invoice.created_at.strftime('%Y-%m-%d')}\n")
#         printer.text(f"Total Amount: {invoice.total_amount} {invoice.currency}\n")
#         printer.text("======================\n")

#         # ✅ Print Footer
#         printer.text("Thank you for your purchase!\n")
#         printer.text("Visit Again!\n\n")

#         # ✅ Cut Receipt
#         printer.cut()

#         return {"success": "Receipt printed successfully"}
    
#     except Invoice.DoesNotExist:
#         return {"error": "Invoice not found"}
#     except Exception as e:
#         return {"error": str(e)}


# virtual printer testing.

import os
from escpos.printer import File
from django.conf import settings
from transactions.models import Invoice

def print_invoice(invoice_id):
    """
    Simulate printing an invoice by saving it as a text file (ASCII format).
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id)

        # ✅ Define file path
        file_path = os.path.join(settings.MEDIA_ROOT, f"receipts/invoice_{invoice_id}.txt")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # ✅ Open a file in **text mode** to ensure correct encoding
        with open(file_path, "w", encoding="ascii", errors="ignore") as file:
            file.write("========== SUITADMIN SYSTEM ==========\n")
            file.write(f"Invoice No: {invoice.invoice_number}\n")
            file.write(f"Customer: {invoice.customer_name}\n")
            file.write(f"Date: {invoice.created_at.strftime('%Y-%m-%d')}\n")
            file.write(f"Total Amount: {invoice.total_amount} {invoice.currency}\n")
            file.write("=====================================\n")
            file.write("Thank you for your purchase!\n")
            file.write("Visit Again!\n\n")

        return {"success": f"Receipt printed to file: {file_path}"}

    except Invoice.DoesNotExist:
        return {"error": "Invoice not found"}
    except Exception as e:
        return {"error": str(e)}
