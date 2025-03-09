from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Sale, SaleItem, Invoice
from .serializers import SaleSerializer, InvoiceSerializer
from .utils import generate_invoice
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from .report import generate_sales_report, export_sales_report_to_pdf


class SaleViewSet(viewsets.ModelViewSet):
    """
    Handle creating, retrieving, updating, and deleting sales.
    """
    queryset = Sale.objects.all().order_by('-created_at')
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]  # ✅ Protect API

    def create(self, request, *args, **kwargs):
        """
        Create a new sale with item validation and stock deduction.
        """
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            sale = serializer.save(created_by=request.user)
            sale.update_total_amount()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def generate_invoice(self, request, pk=None):
        """
        Generate an invoice for a completed sale.
        """
        sale = self.get_object()
        
        # Make sure the sale is completed before generating an invoice
        if sale.status != 'completed':
            return Response({"error": "Invoice can only be generated for completed sales."}, status=400)
        
        # Try to generate or fetch the invoice
        invoice, created = Invoice.objects.get_or_create(sale=sale)
        if created or not invoice.pdf_file:
            try:
                invoice_url = generate_invoice(sale.id)
                invoice.pdf_file = invoice_url
                invoice.save()
            except Exception as e:
                return Response({"error": f"Failed to generate invoice: {str(e)}"}, status=500)
        
        invoice_serializer = InvoiceSerializer(invoice)
        return Response(invoice_serializer.data, status=200)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View and retrieve invoices.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]  # ✅ Restrict access

class SalesReportViewSet(viewsets.ViewSet):
    """
    View sales reports.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        """
        Generate a comprehensive sales report with optional date filtering.
        """
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        try:
            report_data = generate_sales_report(start_date, end_date)
            return Response(report_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """
        Generate and return a PDF version of the sales report.
        """
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        try:
            pdf_buffer = export_sales_report_to_pdf(start_date, end_date)
            response = FileResponse(pdf_buffer, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
