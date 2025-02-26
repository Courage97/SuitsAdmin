from django.db import models
from django.db.models import Sum, F
from django.conf import settings
from inventory.models import Product

class Order(models.Model):
    """
    Stores customer orders, linked to multiple products.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    customer_name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def update_total_amount(self):
        """
        Updates the total amount based on linked order items.
        """
        total = self.items.aggregate(
            total=Sum(F("product__price") * F("quantity"))
        )["total"] or 0
        self.total_amount = total
        self.save(update_fields=["total_amount"])

class OrderItem(models.Model):
    """
    Stores individual products linked to an order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ New field

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.order.id})"
