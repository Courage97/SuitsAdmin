from django.db import models
from users.models import User

class SalesReport(models.Model):
    """
    Stores monthly sales reports, including total orders and revenue.
    """
    month = models.CharField(unique=True, max_length=50)
    total_orders = models.PositiveIntegerField(null=True, blank=True, default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    best_selling_products = models.JSONField(null=True, blank=True, default=list)
    pdf_report = models.FileField(upload_to="reports/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sales Report - {self.month}"

class Invoice(models.Model):
    """
    Stores finalized invoices.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    TRANSMISSION_STATUS_CHOICES = [
        ("pending_manual_submission", "Pending Manual Submission"),
        ("submitted", "Submitted to SENIAT"),
    ]

    invoice_number = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Cashier/Admin
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=[("USD", "US Dollar"), ("Bs", "Bolívares"), ("EUR", "Euro")],
        default="USD"
    )
    converted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    # SENIAT Compliance Fields
    seniat_xml_file = models.FileField(upload_to="invoices/", null=True, blank=True)
    seniat_signature_file = models.FileField(upload_to="invoices/", null=True, blank=True)
    transmission_status = models.CharField(
        max_length=30, choices=TRANSMISSION_STATUS_CHOICES, default="pending_manual_submission"
    )

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.transmission_status}"

class ExchangeRate(models.Model):
    """
    Stores currency exchange rates.
    """
    base_currency = models.CharField(max_length=3, choices=[("USD", "US Dollar")], default="USD")
    target_currency = models.CharField(max_length=3, choices=[("Bs", "Bolívares"), ("EUR", "Euro")])
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"1 {self.base_currency} = {self.rate} {self.target_currency}"
