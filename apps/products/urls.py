from django.urls import path
from .views import (
    CategoryListCreateView, CategoryDetailView,
    BagListCreateView, BagDetailView,
    FeaturedBagsView, CategoryProductsView,
    BulkImportCategoriesView,
    BulkImportProductsView
)

urlpatterns = [
    # Category endpoints
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    
    # Bag endpoints
    path('bags/featured/', FeaturedBagsView.as_view(), name='featured-bags'),  # This must come first!

    path('bags/', BagListCreateView.as_view(), name='bag-list'),
    path('bags/<slug:slug>/', BagDetailView.as_view(), name='bag-detail'),
    
    # Special endpoints
    path('categories/<slug:category_slug>/products/', CategoryProductsView.as_view(), name='category-products'),


    path('api/admin/import-categories/', BulkImportCategoriesView.as_view(), name='import-categories'),
    path('api/admin/import-products/', BulkImportProductsView.as_view(), name='import-products'),
]