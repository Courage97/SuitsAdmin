from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ✅ User authentication routes
    path("api/users/", include("users.urls")),
    
    # ✅ App-specific routes
    path('api/billing/', include('billing.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/sale/', include('sale.urls')),          # Sale app
    path('api/table/', include("table.urls")),
    path('api/logs/', include("logs.urls")),
    path('api/transactions/', include("transactions.urls")),
]

# ✅ Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
