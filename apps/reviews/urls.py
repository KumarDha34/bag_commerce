from django.urls import path
from .views import (
    CreateReviewView, UpdateReviewView, DeleteReviewView,
    ProductReviewsView, UserReviewsView, CanReviewProductView,
)

urlpatterns = [
    # User endpoints
    path('create/', CreateReviewView.as_view(), name='create-review'),
    path('update/<int:review_id>/', UpdateReviewView.as_view(), name='update-review'),
    path('delete/<int:review_id>/', DeleteReviewView.as_view(), name='delete-review'),
    path('product/<slug:product_slug>/', ProductReviewsView.as_view(), name='product-reviews'),
    path('my-reviews/', UserReviewsView.as_view(), name='my-reviews'),
    path('can-review/<int:product_id>/', CanReviewProductView.as_view(), name='can-review'),
    
    # # Admin endpoints
    # path('admin/pending/', AdminPendingReviewsView.as_view(), name='admin-pending-reviews'),
    # path('admin/approve/<int:review_id>/', AdminApproveReviewView.as_view(), name='admin-approve-review'),
    # path('admin/all/', AdminAllReviewsView.as_view(), name='admin-all-reviews'),
]