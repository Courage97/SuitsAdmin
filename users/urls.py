from django.urls import path
from .views import RegisterView, LoginView, UserListView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # User registration endpoint
    path("register/", RegisterView.as_view(), name="register"),

    # User login endpoint
    path("login/", LoginView.as_view(), name="login"),

    # JWT token refresh endpoint
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # users list endpoint
     path("users/", UserListView.as_view(), name="user-list"), 
]