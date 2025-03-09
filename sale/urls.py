from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, InvoiceViewSet, SalesReportViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),  # ✅ Include existing router for sales & invoices

    # ✅ Sale Invoice Generation
    path('sales/<int:pk>/invoice/', SaleViewSet.as_view({'get': 'generate_invoice'}), name='generate-invoice'),

    # ✅ Monthly Sales Report (manual path)
    path('sales-reports/monthly/', SalesReportViewSet.as_view({'get': 'monthly_report'}), name='monthly-sales-report'),

    # ✅ Export Sales Report to PDF
    path('sales-reports/export-pdf/', SalesReportViewSet.as_view({'get': 'export_pdf'}), name='export-sales-report-pdf'),
]