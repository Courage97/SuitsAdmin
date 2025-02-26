from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvoiceViewSet, ExchangeRateViewSet, FetchExchangeRateView, 
    GenerateSeniatInvoiceView, TransmitInvoiceToSeniatView, 
    PrintInvoiceView, generate_order_invoice, 
    monthly_sales_report, generate_sales_report_view, 
    download_sales_report, SalesReportListView
)

# ✅ Register ViewSets
router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename="invoices")
router.register(r'exchange-rates', ExchangeRateViewSet, basename="exchange-rates")

urlpatterns = [
    path("", include(router.urls)),  # ✅ Include registered routes
    path("fetch-exchange-rates/", FetchExchangeRateView.as_view(), name="fetch-exchange-rates"),
    path("generate-seniat-invoice/<int:invoice_id>/", GenerateSeniatInvoiceView.as_view(), name="generate-seniat-invoice"),
    path("transmit-invoice/<int:invoice_id>/", TransmitInvoiceToSeniatView.as_view(), name="transmit-invoice"),
    path("print-invoice/<int:invoice_id>/", PrintInvoiceView.as_view(), name="print-invoice"),

    # ✅ Order Invoice Route
    path("orders/<int:order_id>/invoice/", generate_order_invoice, name="generate-invoice"),

    # ✅ Sales Report Routes
    path("sales-reports/", SalesReportListView.as_view(), name="sales-reports"),
    path("sales-reports/generate/", generate_sales_report_view, name="generate-sales-report"),
    path("sales-reports/monthly/", monthly_sales_report, name="monthly-sales-report"),
    path("sales-reports/download/", download_sales_report, name="download-sales-report"),
]
