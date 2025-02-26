from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProformaInvoiceCreateView, ProformaInvoiceListView, ConvertProformaToInvoiceView
)
from transactions.views import InvoiceViewSet, ExchangeRateViewSet  # ✅ Ensure transactions/views.py has these

# ✅ Register ViewSets
router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename="invoices")  
router.register(r'exchange-rates', ExchangeRateViewSet, basename="exchange-rates")

urlpatterns = [
    path("", include(router.urls)),  # ✅ Includes registered routes for invoices & exchange rates
    path("proforma-invoices/", ProformaInvoiceListView.as_view(), name="proforma-invoice-list"),
    path("proforma-invoices/create/", ProformaInvoiceCreateView.as_view(), name="proforma-invoice-create"),
    path("proforma-invoices/<int:pk>/finalize/", ConvertProformaToInvoiceView.as_view(), name="convert-proforma"),
]
