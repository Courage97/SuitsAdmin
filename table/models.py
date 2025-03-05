from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Table(models.Model):
    """
    Represents tables in the restaurant.
    """
    STATUS_CHOICES = [
        ("free", "Free"),
        ("occupied", "Occupied"),
        ("reserved", "Reserved"),
    ]

    table_number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="free")

    def mark_as_occupied(self):
        """Mark the table as occupied."""
        self.status = "occupied"
        self.save()

    def mark_as_free(self):
        """Mark the table as free."""
        self.status = "free"
        self.save()

    def __str__(self):
        return f"Table {self.table_number} - {self.status}"


class Reservation(models.Model):
    """
    Handles table reservations.
    """
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="reservations")
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True, null=True)
    reservation_time = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("table", "reservation_time")

    def __str__(self):
        return f"Reservation for {self.customer_name} at {self.reservation_time} (Table {self.table.table_number})"


class BillSplit(models.Model):
    """
    Stores details of bill splits among customers.
    """
    sale = models.ForeignKey('sale.Sale', on_delete=models.CASCADE, related_name="bill_splits")
    customer_name = models.CharField(max_length=255)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ("cash", "Cash"), 
            ("card", "Card"), 
            ("mobile", "Mobile Payment"),
            ("bs", "Bolívares"),
            ("usd", "US Dollars"),
            ("eur", "Euros"),
        ],
    )
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} paid {self.amount_paid} {self.payment_method} for Sale {self.sale.id}"


class TableInvoice(models.Model):
    """
    Stores invoice details for a restaurant table with SENIAT compliance.
    """
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="invoices")
    sale = models.ForeignKey('sale.Sale', on_delete=models.CASCADE, null=True, blank=True)
    invoice_number = models.CharField(max_length=20, unique=True)
    control_code = models.CharField(max_length=100, blank=True, null=True)  # SENIAT control code
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_details = models.JSONField(blank=True, null=True)  # Store tax breakdown
    pdf_file = models.FileField(upload_to="invoices/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} for Table {self.table.table_number}"

    def calculate_total(self):
        """
        Calculate total amount for the invoice based on sale items.
        """
        if self.sale:
            total = self.sale.items.aggregate(
                total=models.Sum(models.F("price_at_sale") * models.F("quantity"))
            )["total"] or 0
            self.total_amount = total
            self.save()

    def generate_control_code(self):
        """
        Generate SENIAT-compliant control code.
        """
        self.control_code = f"SEN-{self.id}-{self.table.table_number}"
        self.save()
