from django.urls import path
from .views import (
    CategoryListCreateView,
    ProductListCreateView,
    ProductDetailView,
    StockMovementCreateView
)

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('products/', ProductListCreateView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('stock-movement/', StockMovementCreateView.as_view(), name='stock-movement-create'),
]