from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Sale, SaleItem, Invoice
from .serializers import SaleSerializer, InvoiceSerializer
from .utils import generate_invoice
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions


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

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def generate_invoice(self, request, pk=None):
        """
        Generate an invoice for a completed sale.
        """
        sale = get_object_or_404(Sale, pk=pk)

        if sale.status != "completed":
            return Response({"error": "Invoice can only be generated for completed sales."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if an invoice already exists
        invoice, created = Invoice.objects.get_or_create(sale=sale)

        if created or not invoice.pdf_file:
            try:
                invoice_url = generate_invoice(sale.id)
                invoice.pdf_file = invoice_url
                invoice.save()
            except Exception as e:
                return Response({"error": f"Failed to generate invoice: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_200_OK)

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
    permission_classes = [permissions.IsAuthenticated]  # ✅ Restrict reports

    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        """
        Generate a monthly sales report.
        """
        try:
            report_data = Sale.objects.get_monthly_report()
            return Response(report_data, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"error": "Monthly report generation failed. Check your model."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)