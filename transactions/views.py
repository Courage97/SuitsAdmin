from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, FileResponse
from transactions.models import Invoice, ExchangeRate, SalesReport  # ✅ Fixed imports
from transactions.serializers import SalesReportSerializer, InvoiceSerializer, ExchangeRateSerializer
from users.permissions import IsAdminUser  # ✅ Ensure this exists in `users/permissions.py`
from transactions.utils import (  # ✅ Make sure these functions exist in `transactions/utils.py`
    generate_invoice, send_invoice_email, generate_monthly_sales_report,
    generate_sales_report_pdf, generate_sales_report, fetch_live_exchange_rates,
    generate_seniat_invoice_xml, sign_seniat_invoice, send_invoice_to_seniat
)
from billing.printer_utils import print_invoice  # ✅ Fixed import path
import os
from rest_framework.permissions import IsAuthenticated


# ✅ SALES REPORT VIEWS
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def monthly_sales_report(request):
    """
    Retrieve the sales report for the current month.
    Only Admins can access this.
    """
    report = generate_monthly_sales_report()
    return Response(report)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def download_sales_report(request):
    """
    Generate and return a sales report PDF.
    Only Admins can access this.
    """
    report_url = generate_sales_report_pdf()
    if not report_url:
        return Response({"error": "Sales report generation failed."}, status=500)
    return JsonResponse({"report_url": request.build_absolute_uri(report_url)})


class SalesReportListView(generics.ListAPIView):
    """
    List all stored sales reports.
    """
    queryset = SalesReport.objects.all().order_by("-created_at")
    serializer_class = SalesReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def generate_sales_report_view(request):
    """
    Generate and return a new monthly sales report.
    """
    report = generate_sales_report()
    if not report or not report.pdf_report:
        return Response({"error": "Sales report generation failed."}, status=500)

    return JsonResponse({
        "message": "Sales report generated successfully",
        "report_month": report.month,
        "report_url": request.build_absolute_uri(report.pdf_report.url),
    })


# ✅ INVOICE MANAGEMENT VIEWS
class InvoiceViewSet(viewsets.ModelViewSet):
    """
    View and manage invoices.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["customer_name", "status"]
    ordering_fields = ["created_at", "total_amount"]

    def get_permissions(self):
        """
        Assign permissions dynamically based on action:
        - Cashiers can create invoices.
        - Admins can view, update, or delete invoices.
        """
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]  # ✅ Only Admins Can Modify Invoices
        else:
            permission_classes = [IsAdminUser]  # ✅ Restrict Deletions
        return [perm() for perm in permission_classes]


# ✅ EXCHANGE RATE MANAGEMENT
class ExchangeRateViewSet(viewsets.ModelViewSet):
    """
    View and manage exchange rates.
    """
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]


class FetchExchangeRateView(APIView):
    """
    Fetch and update exchange rates using an external API.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        success = fetch_live_exchange_rates()
        if success:
            return Response({"message": "Exchange rates updated successfully"}, status=200)
        return Response({"error": "Failed to fetch exchange rates"}, status=500)


# ✅ SENIAT INVOICE MANAGEMENT
class GenerateSeniatInvoiceView(APIView):
    """
    API view to generate a SENIAT-compliant XML invoice.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request, invoice_id, *args, **kwargs):
        xml_path = generate_seniat_invoice_xml(invoice_id)

        if not xml_path or not os.path.exists(xml_path):
            return Response({"error": "Invoice not found"}, status=404)

        # Digitally sign the XML invoice
        signature_path = sign_seniat_invoice(xml_path)
        if not signature_path:
            return Response({"error": "Failed to sign invoice"}, status=500)

        return FileResponse(open(xml_path, "rb"), content_type="application/xml")


class TransmitInvoiceToSeniatView(APIView):
    """
    API endpoint to transmit an invoice to SENIAT.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, invoice_id, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(id=invoice_id)

            if invoice.transmission_status == "submitted":
                return Response({"error": "Invoice already transmitted"}, status=400)

            response = send_invoice_to_seniat(invoice_id)
            return Response(response)

        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)  # ✅ Handle Unexpected Errors


# ✅ PRINT INVOICE
class PrintInvoiceView(APIView):
    """
    API view to print an invoice using a thermal printer.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invoice_id, *args, **kwargs):
        result = print_invoice(invoice_id)
        if "success" in result:
            return Response({"message": result["success"]}, status=200)
        return Response({"error": result["error"]}, status=400)
    
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def generate_order_invoice(request, order_id):
    """
    Generate and return an invoice for a specific order.
    """
    invoice_url = generate_invoice(order_id)

    if invoice_url is None:
        return Response({"error": "Order not found"}, status=404)  # ✅ Prevent crashing

    return Response({"invoice_url": request.build_absolute_uri(invoice_url)})

