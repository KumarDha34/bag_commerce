"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import TemplateView
# Swagger/OpenAPI Schema Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Bag E-commerce API",
        default_version='v1.0.0',
        description="""
        # 🛍️ Bag E-commerce API Documentation
        
        ## Authentication Endpoints
        * Register new user
        * Login with email/password
        * Get/Update profile
        * Change password
        * Forgot password with OTP
        
        ## Security
        * JWT Token Authentication
        * Password validation
        * OTP verification for password reset
        """,
        contact=openapi.Contact(email="support@bagecommerce.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    
    # Swagger UI Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API Endpoints
    path('api/auth/', include('apps.accounts.urls')),  # Authentication APIs
    # Add more as you build them:
    path('api/products/', include('apps.products.urls')),  # Products API
    path('api/cart/', include('apps.carts.urls')),          # Shopping Cart API
    path('api/wishlist/', include('apps.wishlist.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/reviews/', include('apps.reviews.urls')),


    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('collections/', TemplateView.as_view(template_name='collections.html'), name='collections'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('forgot-password/', TemplateView.as_view(template_name='forgot_password.html'), name='forgot-password'),    
    path('reset-password-sent/', TemplateView.as_view(template_name='reset_password_sent.html'), name='reset-password-sent'),
    path('verify-otp/', TemplateView.as_view(template_name='verify_otp.html'), name='verify-otp'),
    path('reset-password/', TemplateView.as_view(template_name='reset_password_done.html'), name='reset-password-done'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('shop/', TemplateView.as_view(template_name='shop.html'), name='shop'),
    path('user/cart/', TemplateView.as_view(template_name='user/cart.html'), name='cart'),
    
    # User Dashboard
    path('user/dashboard/', TemplateView.as_view(template_name='user/dashboard.html'), name='user_dashboard'),
    path('user/profile/', TemplateView.as_view(template_name='user/profile.html'), name='user_profile'),
    path('user/orders/', TemplateView.as_view(template_name='user/orders.html'), name='user_orders'),
    path('user/wishlist/', TemplateView.as_view(template_name='user/wishlist.html'), name='user_wishlist'),
    path('user/checkout/', TemplateView.as_view(template_name='user/checkout.html'), name='user_checkout'),
    path('user/order-confirmation/<str:order_number>/', TemplateView.as_view(template_name='user/order_confirmation.html'), name='order-confirmation-page'),
    path('user/track-order/<str:order_number>/', TemplateView.as_view(template_name='user/track_order.html'), name='order-track'),
    
    # Admin Dashboard
    path('admin-dashboard/', TemplateView.as_view(template_name='admin/dashboard.html'), name='admin_dashboard'),
    path('admin-orders/', TemplateView.as_view(template_name='admin/orders.html'), name='admin_orders'),
    path('admin-products/', TemplateView.as_view(template_name='admin/products.html'), name='admin_products'),
    path('admin-categories/', TemplateView.as_view(template_name='admin/categories.html'), name='admin_categories'),
    path('admin-users/', TemplateView.as_view(template_name='admin/users.html'), name='admin_users'),
    path('admin-payments/', TemplateView.as_view(template_name='admin/payments.html'), name='admin_payments'),
    path('admin-update-qr/', TemplateView.as_view(template_name='admin/update_qr.html'), name='update-qr'),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)