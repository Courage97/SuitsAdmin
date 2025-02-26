from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Product, StockMovement, Category
from .serializers import ProductSerializer, StockMovementSerializer, CategorySerializer
from users.permissions import IsAdminUser, IsCashierUser
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter  # ✅ Use the custom filter

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [IsAuthenticated()]

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class StockMovementCreateView(generics.CreateAPIView):
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def perform_create(self, serializer):
        with transaction.atomic():
            stock_movement = serializer.save(created_by=self.request.user)
            product = Product.objects.select_for_update().get(id=stock_movement.product.id)

            if stock_movement.movement_type == "add":
                # First update the quantity
                product.quantity_in_stock = F("quantity_in_stock") + stock_movement.quantity
                product.save()
                
                # Refresh from database to get the actual value
                product.refresh_from_db()
                
                # Now check the condition with the actual value
                if product.quantity_in_stock > product.reorder_point:
                    product.low_stock_alert_sent = False
                    product.save()
            
            if stock_movement.movement_type == "remove":
                if product.quantity_in_stock < stock_movement.quantity:
                    raise serializers.ValidationError(
                    f"Not enough stock! Current: {product.quantity_in_stock}, Requested: {stock_movement.quantity}")
                    
            elif stock_movement.movement_type == "remove":
                current_stock = product.quantity_in_stock  # Get current value
                if current_stock >= stock_movement.quantity:
                    product.quantity_in_stock = F("quantity_in_stock") - stock_movement.quantity
                    product.save()
                else:
                    raise serializers.ValidationError(
                        f"Not enough stock available! Current stock: {current_stock}, Requested: {stock_movement.quantity}"
                    )