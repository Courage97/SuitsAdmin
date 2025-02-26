from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F
from .models import Product

@shared_task
def check_low_stock():
    """
    Check for products that are low in stock and send email alerts.
    Resets the alert flag if stock is replenished.
    """
    # 1️⃣ Get products that are low in stock and haven't been alerted yet
    low_stock_products = Product.objects.filter(
        quantity_in_stock__lte=F('reorder_point'), 
        low_stock_alert_sent=False
    )

    if low_stock_products.exists():
        product_list = "\n".join([
            f"{p.name} - {p.quantity_in_stock} left (Minimum: {p.minimum_stock})"
            for p in low_stock_products
        ])

        send_mail(
            "⚠ Low Stock Alert",
            f"The following products are running low on stock:\n\n{product_list}",
            settings.DEFAULT_FROM_EMAIL,
            settings.INVENTORY_ALERT_EMAILS,
            fail_silently=False,
        )

        # ✅ Mark products as "alert sent" to prevent duplicate emails
        low_stock_products.update(low_stock_alert_sent=True)

    # 2️⃣ Reset `low_stock_alert_sent` if stock is replenished
    replenished_products = Product.objects.filter(
        quantity_in_stock__gt=F('reorder_point'), 
        low_stock_alert_sent=True  # Only reset those that were alerted before
    )

    if replenished_products.exists():
        replenished_products.update(low_stock_alert_sent=False)  # ✅ Correct reset logic
