import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    is_low_stock = django_filters.BooleanFilter(method="filter_low_stock")  # ✅ Custom filter

    class Meta:
        model = Product
        fields = ["category"]  # ✅ Do not include `is_low_stock` here

    def filter_low_stock(self, queryset, name, value):
        """
        Filter products based on whether they are low in stock.
        """
        if value:
            return queryset.filter(quantity_in_stock__lte=models.F("reorder_point"))
        return queryset
