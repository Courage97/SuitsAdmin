from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, InvoiceViewSet, SalesReportViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    # ✅ Register ViewSets
    path('', include(router.urls)),
    
    # ✅ Sale Invoice Generation
    path('sales/<int:pk>/invoice/', SaleViewSet.as_view({'get': 'generate_invoice'}), name='generate-invoice'),

    # ✅ Monthly Sales Report
    path('sales-reports/monthly/', SalesReportViewSet.as_view({'get': 'monthly_report'}), name='monthly-sales-report'),
]
