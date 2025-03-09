from django.db.models import Sum, Count, Value, FloatField
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from .models import Sale, SaleItem
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import FileResponse

def generate_sales_report(start_date=None, end_date=None):
    """
    Generate a sales report with optional date filters.
    """
    try:
        sales_query = Sale.objects.filter(status="completed")

        # Apply date filtering if provided
        if start_date and end_date:
            sales_query = sales_query.filter(created_at__range=[start_date, end_date])

        # Total Sales & Revenue
        total_sales = sales_query.count()
        total_revenue = sales_query.aggregate(
            total=Coalesce(Sum("total_amount", output_field=FloatField()), Value(0.00))
        )["total"]

        # Best-Selling Products
        best_selling_products = SaleItem.objects.filter(sale__status="completed", sale__created_at__range=[start_date, end_date]) \
            .values("product__name") \
            .annotate(total_quantity=Sum("quantity")) \
            .order_by("-total_quantity")[:5]

        # Sales by Status
        sales_status_counts = sales_query.values("status").annotate(count=Count("id"))

        # Revenue by Currency
        revenue_by_currency = sales_query.values("currency") \
            .annotate(total_revenue=Sum("total_amount", output_field=FloatField()))

        return {
            "total_sales": total_sales,
            "total_revenue": float(total_revenue),
            "best_selling_products": list(best_selling_products),
            "sales_status_counts": list(sales_status_counts),
            "revenue_by_currency": list(revenue_by_currency),
        }

    except Exception as e:
        return {"error": str(e)}

def export_sales_report_to_pdf(start_date=None, end_date=None):
    """
    Generate a PDF file for the sales report.
    """
    report_data = generate_sales_report(start_date, end_date)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("Sales Report")

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "Sales Report")

    # Date Range
    pdf.setFont("Helvetica", 12)
    if start_date and end_date:
        pdf.drawString(50, 780, f"Date Range: {start_date} to {end_date}")

    # Total Sales & Revenue
    pdf.drawString(50, 750, f"Total Sales: {report_data['total_sales']}")
    pdf.drawString(50, 730, f"Total Revenue: ${report_data['total_revenue']:.2f}")

    # Best-Selling Products
    pdf.drawString(50, 700, "Best-Selling Products:")
    y = 680
    for item in report_data["best_selling_products"]:
        pdf.drawString(70, y, f"- {item['product__name']}: {item['total_quantity']} units")
        y -= 20

    # Sales by Status
    pdf.drawString(50, y - 20, "Sales Status Breakdown:")
    y -= 40
    for status in report_data["sales_status_counts"]:
        pdf.drawString(70, y, f"- {status['status']}: {status['count']} sales")
        y -= 20

    # Revenue by Currency
    pdf.drawString(50, y - 20, "Revenue Breakdown by Currency:")
    y -= 40
    for currency in report_data["revenue_by_currency"]:
        pdf.drawString(70, y, f"- {currency['currency']}: ${currency['total_revenue']:.2f}")
        y -= 20

    pdf.save()
    buffer.seek(0)

    return buffer
