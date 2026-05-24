from django.urls import path
from .views import (
    GetCartView, AddToCartView, UpdateCartItemView,
    RemoveFromCartView, ClearCartView, CartSummaryView
)

urlpatterns = [
    path('', GetCartView.as_view(), name='cart'),
    path('add/', AddToCartView.as_view(), name='add-to-cart'),
    path('update/<int:item_id>/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('remove/<int:item_id>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('clear/', ClearCartView.as_view(), name='clear-cart'),
    path('summary/', CartSummaryView.as_view(), name='cart-summary'),
]