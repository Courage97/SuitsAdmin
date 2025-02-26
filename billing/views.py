from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse
from .models import ProformaInvoice
from .serializers import ProformaInvoiceSerializer  # ✅ Correct Import for ProformaInvoice
from transactions.serializers import InvoiceSerializer, ExchangeRateSerializer  # ✅ Import Serializers from Transactions
from transactions.utils import generate_invoice_pdf, send_invoice_email  # ✅ Ensure these functions exist in Transactions
import os


class ProformaInvoiceCreateView(generics.CreateAPIView):
    """
    Create a new proforma invoice.
    """
    queryset = ProformaInvoice.objects.all()
    serializer_class = ProformaInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProformaInvoiceListView(generics.ListAPIView):
    """
    Retrieve all proforma invoices.
    """
    queryset = ProformaInvoice.objects.all()
    serializer_class = ProformaInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]


class ConvertProformaToInvoiceView(generics.UpdateAPIView):
    """
    Convert a proforma invoice into a final invoice.
    """
    queryset = ProformaInvoice.objects.all()
    serializer_class = ProformaInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        proforma = self.get_object()

        if proforma.finalized:
            return Response({"error": "Proforma Invoice has already been finalized."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a real invoice
        invoice = Invoice.objects.create(
            invoice_number=f"INV-{Invoice.objects.count() + 1:04d}",
            customer_name=proforma.order.customer_name,
            user=proforma.created_by,
            total_amount=proforma.total_amount,
            currency=proforma.currency,
            status="pending",
        )

        proforma.finalized = True
        proforma.save()

        return Response({
            "message": "Proforma Invoice converted to Final Invoice",
            "invoice_id": invoice.id
        }, status=status.HTTP_200_OK)


class GenerateInvoicePDFView(APIView):
    """
    API view to generate and return a PDF invoice.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invoice_id, *args, **kwargs):
        pdf_path = generate_invoice_pdf(invoice_id)

        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(open(pdf_path, "rb"), content_type="application/pdf")
        return Response({"error": "Invoice not found"}, status=404)


class SendInvoiceEmailView(APIView):
    """
    API view to send an invoice PDF via email.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invoice_id, *args, **kwargs):
        success, message = send_invoice_email(invoice_id)

        if success:
            return Response({"message": message}, status=200)
        return Response({"error": message}, status=400)
