from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Table, Reservation, BillSplit
from sale.models import SaleItem
from .serializers import TableSerializer, ReservationSerializer, BillSplitSerializer
from sale.serializers import SaleItemSerializer
from sale.models import Sale
from decimal import Decimal

# Table Views
class TableListCreateView(generics.ListCreateAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]


class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]


# Reservation Views
class ReservationListCreateView(generics.ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]


class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]


# Bill Split Views
class BillSplitCreateView(generics.CreateAPIView):
    serializer_class = BillSplitSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        order_id = self.kwargs.get("order_id")
        order = get_object_or_404(Sale, id=order_id)

        total_paid = sum(BillSplit.objects.filter(order=order).values_list("amount_paid", flat=True))
        amount_requested = Decimal(str(request.data.get("amount_paid", 0)))  

        if total_paid + amount_requested > order.total_amount:
            return Response({"error": "Total bill split exceeds order total!"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(order=order)  # ✅ Attach order to serializer
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# Kitchen and Bar Order Views
class KitchenOrderListView(generics.ListAPIView):
    """
    Fetches all orders assigned to the kitchen.
    """
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SaleItem.objects.filter(routed_to="kitchen")


class BarOrderListView(generics.ListAPIView):
    """
    Fetches all orders assigned to the bar.
    """
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SaleItem.objects.filter(routed_to="bar")


# Save Method for OrderItem Model (Place this in the OrderItem model)
def save(self, *args, **kwargs):
    if not self.routed_to:  # Only set if not already assigned
        self.routed_to = "kitchen" if self.category == "food" else "bar"
    super().save(*args, **kwargs)