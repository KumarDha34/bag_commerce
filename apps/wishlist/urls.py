from django.urls import path
from .views import (
    GetWishlistView, AddToWishlistView, RemoveFromWishlistView,
    ClearWishlistView, MoveToCartView, CheckIfInWishlistView
)

urlpatterns = [
    path('', GetWishlistView.as_view(), name='wishlist'),
    path('add/', AddToWishlistView.as_view(), name='add-to-wishlist'),
    path('remove/<int:bag_id>/', RemoveFromWishlistView.as_view(), name='remove-from-wishlist'),
    path('clear/', ClearWishlistView.as_view(), name='clear-wishlist'),
    path('move-to-cart/<int:bag_id>/', MoveToCartView.as_view(), name='move-to-cart'),
    path('check/<int:bag_id>/', CheckIfInWishlistView.as_view(), name='check-in-wishlist'),
]