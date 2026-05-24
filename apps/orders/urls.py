from django.urls import path
from .views import (
    CreateOrderView, OrderListView, OrderDetailView,
    CancelOrderView, TrackOrderView,
    AdminOrderListView, AdminUpdateOrderStatusView
)

urlpatterns = [
    # User endpoints
    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('track/<str:order_number>/', TrackOrderView.as_view(), name='track-order'),

    
    # Admin endpoints
    path('admin/all/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/<int:order_id>/update-status/', AdminUpdateOrderStatusView.as_view(), name='update-order-status'),
]