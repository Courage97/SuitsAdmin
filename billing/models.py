from django.db import models
from django.conf import settings
from orders.models import Order

class ProformaInvoice(models.Model):
    """
    Stores estimated invoices before finalization.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="proforma_invoices")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(
        max_length=3,
        choices=[("USD", "US Dollar"), ("Bs", "Bolívares"), ("EUR", "Euro")],
        default="USD"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finalized = models.BooleanField(default=False)  # Becomes True when converted to a real invoice

    def __str__(self):
        return f"Proforma Invoice {self.id} - Order {self.order.id} ({'Finalized' if self.finalized else 'Pending'})"
