from django.db import models
from django.conf import settings
from django.conf import settings
from sale.models import Sale

class Table(models.Model):
    STATUS_CHOICES = [
        ("free", "Free"),
        ("occupied", "Occupied"),
        ("reserved", "Reserved"),
    ]
    
    table_number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="free")
    
    def __str__(self):
        return f"Table {self.table_number} - {self.status}"

class Reservation(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255)
    reservation_time = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ("table", "reservation_time")  # ✅ Prevents double booking


class BillSplit(models.Model):
    """
    Stores details of bill splits among customers.
    """
    order = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="bill_splits")
    customer_name = models.CharField(max_length=255)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50, 
        choices=[("cash", "Cash"), ("card", "Card"), ("mobile", "Mobile Payment")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} paid {self.amount_paid} for Order {self.order.id}"

class SaleItem(models.Model):
    CATEGORY_CHOICES = [
        ("food", "Food"),
        ("drink", "Drink"),
    ]
    
    order = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        related_name="order_items"  # Changed from default
    )
    product = models.ForeignKey(
        "inventory.Product", 
        on_delete=models.CASCADE, 
        related_name="product_orders"  # Changed from default
    )
    quantity = models.PositiveIntegerField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default="food")
    routed_to = models.CharField(max_length=20, choices=[("kitchen", "Kitchen"), ("bar", "Bar")], blank=True)

    def save(self, *args, **kwargs):
        self.routed_to = "kitchen" if self.category == "food" else "bar"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.order.id} - {self.routed_to})"
