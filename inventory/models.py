from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid  # Import for generating unique SKU

def generate_unique_sku():
    """Generate a unique SKU for products."""
    return str(uuid.uuid4())[:8]  # Shorten UUID to 8 characters


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True, default=generate_unique_sku)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=5)
    reorder_point = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products_created'
    )

    def __str__(self):
        return f"{self.name} - {self.quantity_in_stock} in stock"

    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_point

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('add', 'Addition'),
        ('remove', 'Removal')
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField()
    low_stock_alert_sent = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return f"{self.movement_type} {self.quantity} {self.product.name}"