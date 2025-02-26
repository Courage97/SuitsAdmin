from django.urls import path
from .views import (
    TableListCreateView, TableDetailView,
    ReservationListCreateView, ReservationDetailView, 
    BillSplitCreateView, KitchenOrderListView, BarOrderListView

)

urlpatterns = [
    path("tables/", TableListCreateView.as_view(), name="table-list"),
    path("tables/<int:pk>/", TableDetailView.as_view(), name="table-detail"),
    path("reservations/", ReservationListCreateView.as_view(), name="reservation-list"),
    path("reservations/<int:pk>/", ReservationDetailView.as_view(), name="reservation-detail"),
    path("orders/<int:order_id>/split-bill/", BillSplitCreateView.as_view(), name="split-bill"),
    path("kitchen-orders/", KitchenOrderListView.as_view(), name="kitchen-orders"),
    path("bar-orders/", BarOrderListView.as_view(), name="bar-orders")
]
