from django.db import models
from django.db.models import Sum, F, Value
from django.conf import settings
from inventory.models import Product
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from django.utils.crypto import get_random_string



class Sale(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    customer_name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def update_total_amount(self):
        """
        Calculate total amount based on items.
        """
        total = self.items.aggregate(total=Sum(F("price_at_sale") * F("quantity")))['total'] or 0
        self.total_amount = total
        self.save(update_fields=["total_amount"])

    # @classmethod
    # def get_monthly_report(cls):
    #     """
    #     Get a summary of sales for the current month with comprehensive error handling.
    #     """
    #     try:
    #         from django.db.models import Sum, F, Value
    #         from django.db.models.functions import Coalesce
    #         from inventory.models import Product  # Ensure this import is correct
    #         from .models import SaleItem  # Relative import of SaleItem

    #         # Get current month and year
    #         current_month = now().month
    #         current_year = now().year

    #         # Filter sales for current month and year
    #         sales = cls.objects.filter(
    #             created_at__month=current_month, 
    #             created_at__year=current_year,
    #             status='completed'  # Optional: only count completed sales
    #         )

    #         # Count total sales
    #         total_sales = sales.count()

    #         # Calculate total revenue
    #         total_revenue = sales.aggregate(
    #             total=Coalesce(Sum('total_amount'), Value(0.00))
    #         )['total']

    #         # Find best-selling product
    #         best_selling_product = SaleItem.objects.filter(
    #             sale__created_at__month=current_month,
    #             sale__created_at__year=current_year,
    #             sale__status='completed'  # Match sales status
    #         ).values('product__name').annotate(
    #             total_quantity=Sum('quantity')
    #         ).order_by('-total_quantity').first()

    #         return {
    #             "month": now().strftime("%B %Y"),
    #             "total_sales": total_sales,
    #             "total_revenue": float(total_revenue),
    #             "best_selling_product": best_selling_product['product__name'] if best_selling_product else "N/A"
    #         }
        
    #     except ImportError as ie:
    #         return {"error": f"Import error: {str(ie)}"}
    #     except Exception as e:
    #         import traceback
    #         return {
    #             "error": "Monthly report generation failed.",
    #             "details": str(e),
    #             "traceback": traceback.format_exc()
    #         }
    
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """
        Deduct stock when item is added.
        """
        if self.product.quantity_in_stock < self.quantity:
            raise ValueError(f"Not enough stock for {self.product.name}")
        self.product.quantity_in_stock -= self.quantity
        self.product.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Sale {self.sale.id})"


class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3, default="USD")
    target_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"1 {self.base_currency} = {self.rate} {self.target_currency}"


class Invoice(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    pdf_file = models.FileField(upload_to="invoices/")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{get_random_string(8).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} for Sale {self.sale.id}"