from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TableListCreateView, TableDetailView,
    ReservationListCreateView, ReservationDetailView, 
    BillSplitCreateView, BillSplitListView,
    KitchenOrderListView, BarOrderListView,
    TableInvoiceViewSet, TableViewSet,
)

# Use a router for ViewSets
router = DefaultRouter()
router.register(r'tables', TableViewSet, basename='table')
router.register(r'tables/invoices', TableInvoiceViewSet, basename='table-invoice')

urlpatterns = [
    # 🟩 Table URLs
    path("tables/", TableListCreateView.as_view(), name="table-list"),
    path("tables/<int:pk>/", TableDetailView.as_view(), name="table-detail"),
    path("tables/<int:pk>/reset/", TableViewSet.as_view({'post': 'reset_table'}), name="reset-table"),

    # 🟩 Reservation URLs
    path("reservations/", ReservationListCreateView.as_view(), name="reservation-list"),
    path("reservations/<int:pk>/", ReservationDetailView.as_view(), name="reservation-detail"),
    
    # 🟩 Bill Split URLs
    path("sales/<int:sale_id>/split-bill/", BillSplitCreateView.as_view(), name="split-bill"),
    path("sales/<int:sale_id>/bill-splits/", BillSplitListView.as_view(), name="bill-split-list"),
    
    # 🟩 Kitchen & Bar Order URLs
    path("kitchen-orders/", KitchenOrderListView.as_view(), name="kitchen-orders"),
    path("bar-orders/", BarOrderListView.as_view(), name="bar-orders"),

    # 🟩 Table Invoice URLs
    path("tables/<int:pk>/generate-invoice/", TableInvoiceViewSet.as_view({'get': 'generate_invoice'}), name="generate-table-invoice"),
]

# Add router-generated URLs
urlpatterns += router.urls
