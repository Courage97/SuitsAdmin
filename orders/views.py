from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer
from users.permissions import IsCashierUser, IsAdminUser

class OrderListCreateView(generics.ListCreateAPIView):
    """
    List all orders or create a new one.
    """
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsCashierUser]

    @transaction.atomic
    def perform_create(self, serializer):
        order = serializer.save(created_by=self.request.user)
        order.update_total_amount()  # ✅ Ensure total updates after order creation

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific order.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_update(self, serializer):
        """
        Automatically send an invoice when the order is marked as completed.
        """
        order = serializer.save()
