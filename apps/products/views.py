from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly,IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Category, Bag
from .serializers import (
    CategorySerializer, CategoryCreateUpdateSerializer,
    BagSerializer, BagCreateUpdateSerializer
)
from django.utils.text import slugify
from rest_framework.views import APIView
from .permissions import IsAdminOrReadOnly
import pandas as pd
import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# ==================== CATEGORY MANAGEMENT ====================

class CategoryListCreateView(generics.ListCreateAPIView):
    """
    List all categories or create a new category
    
    **GET**: List all active categories (anyone can view)
    **POST**: Create a new category (Admin only)
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        
        # Include inactive categories for admin
        if self.request.user and self.request.user.is_staff:
            is_active = self.request.query_params.get('is_active')
            if is_active is None:
                queryset = Category.objects.all()
            else:
                queryset = Category.objects.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CategoryCreateUpdateSerializer
        return CategorySerializer
    
    @swagger_auto_schema(
        operation_description="Get all categories with optional filtering",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Search by name or description'),
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Filter by active status (admin only)'),
        ],
        responses={
            200: CategorySerializer(many=True),
            201: 'Category created successfully',
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin access required'
        }
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new category (Admin only)",
        request_body=CategoryCreateUpdateSerializer,
        responses={
            201: CategorySerializer(),
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin access required'
        }
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a category
    
    **GET**: Get category details (anyone)
    **PUT/PATCH**: Update category (Admin only)
    **DELETE**: Delete category (Admin only)
    """
    queryset = Category.objects.all()
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return CategoryCreateUpdateSerializer
        return CategorySerializer
    
    @swagger_auto_schema(
        operation_description="Get category details by slug",
        responses={
            200: CategorySerializer(),
            404: 'Category not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update category (Admin only)",
        request_body=CategoryCreateUpdateSerializer,
        responses={
            200: CategorySerializer(),
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin access required',
            404: 'Category not found'
        }
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete category (Admin only)",
        responses={
            204: 'Category deleted',
            401: 'Authentication required',
            403: 'Admin access required',
            404: 'Category not found'
        }
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

# ==================== BAG MANAGEMENT ====================

class BagListCreateView(generics.ListCreateAPIView):
    """
    List all bags or create a new bag
    
    **GET**: List all bags with filtering options (anyone)
    **POST**: Create a new bag (Admin only)
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categories__slug', 'is_active', 'featured']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'name', 'stock']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Bag.objects.filter(is_active=True)
        
        # Include inactive products for admin
        if self.request.user and self.request.user.is_staff:
            is_active = self.request.query_params.get('is_active')
            if is_active is None:
                queryset = Bag.objects.all()
            else:
                queryset = Bag.objects.filter(is_active=is_active.lower() == 'true')

        category_ids = self.request.query_params.get('category_ids')
        if category_ids:
            cat_ids = [int(id) for id in category_ids.split(',')]
            queryset = queryset.filter(categories__id__in=cat_ids).distinct()
        
        # Filter by single category (for backward compatibility)
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by featured
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(featured=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BagCreateUpdateSerializer
        return BagSerializer
    
    @swagger_auto_schema(
        operation_description="Get all bags with filtering, searching and pagination",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Search by name, description or SKU'),
            openapi.Parameter('category', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by category slug'),
            openapi.Parameter('min_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description='Minimum price'),
            openapi.Parameter('max_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, description='Maximum price'),
            openapi.Parameter('featured', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Show only featured products'),
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Filter by active status (admin only)'),
            openapi.Parameter('ordering', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Order by: price, -price, created_at, -created_at, name'),
        ],
        responses={
            200: BagSerializer(many=True),
            201: 'Bag created successfully',
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin access required'
        }
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new bag product (Admin only)",
        request_body=BagCreateUpdateSerializer,
        responses={
            201: BagSerializer(),
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin access required'
        }
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class BagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a bag
    
    **GET**: Get bag details (anyone)
    **PUT/PATCH**: Update bag (Admin only)
    **DELETE**: Delete bag (Admin only)
    """
    queryset = Bag.objects.all()
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return BagCreateUpdateSerializer
        return BagSerializer
    
    @swagger_auto_schema(
        operation_description="Get bag details by slug",
        responses={
            200: BagSerializer(),
            404: 'Bag not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update bag product (Admin only)",
        request_body=BagCreateUpdateSerializer,
        responses={
            200: BagSerializer(),
            400: 'Validation error',
            401: 'Authentication required',
            403: 'Admin access required',
            404: 'Bag not found'
        }
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete bag product (Admin only)",
        responses={
            204: 'Bag deleted',
            401: 'Authentication required',
            403: 'Admin access required',
            404: 'Bag not found'
        }
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

# ==================== SPECIAL ENDPOINTS ====================

class FeaturedBagsView(generics.ListAPIView):
    """
    Get featured bags for homepage display
    """
    serializer_class = BagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Bag.objects.filter(is_active=True, featured=True)[:10]
    
    @swagger_auto_schema(
        operation_description="Get featured bags (limit 10)",
        responses={200: BagSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class CategoryProductsView(generics.ListAPIView):
    """
    Get all bags in a specific category
    """
    serializer_class = BagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        return Bag.objects.filter(categories__slug=category_slug, is_active=True)
    
    @swagger_auto_schema(
        operation_description="Get all products in a specific category",
        responses={200: BagSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    



# Bulk data importing at a time
class BulkImportCategoriesView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Read Excel or CSV file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Expected columns: name, slug, description, image_url, is_active
            categories_created = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    category, created = Category.objects.get_or_create(
                        slug=row.get('slug', row['name'].lower().replace(' ', '-')),
                        defaults={
                            'name': row['name'],
                            'description': row.get('description', ''),
                            'image': row.get('image_url', ''),
                            'is_active': row.get('is_active', True)
                        }
                    )
                    categories_created.append({
                        'name': category.name,
                        'created': created
                    })
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'success': True,
                'total_processed': len(categories_created),
                'categories': categories_created,
                'errors': errors
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkImportProductsView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Read Excel or CSV file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            products_created = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Handle multiple category IDs (comma-separated)
                    category_ids = []
                    
                    # Check for different possible column names
                    if 'category_ids' in row and row['category_ids']:
                        cat_values = str(row['category_ids']).split(',')
                        for cat_val in cat_values:
                            cat_val = cat_val.strip()
                            category = Category.objects.filter(id=cat_val).first()
                            if not category:
                                category = Category.objects.filter(slug=cat_val).first()
                            if not category:
                                category = Category.objects.filter(name__iexact=cat_val).first()
                            if category:
                                category_ids.append(category.id)
                            else:
                                errors.append(f"Row {index + 1}: Category '{cat_val}' not found")
                    
                    elif 'category_slug' in row and row['category_slug']:
                        category = Category.objects.filter(slug=row['category_slug']).first()
                        if category:
                            category_ids = [category.id]
                        else:
                            errors.append(f"Row {index + 1}: Category '{row['category_slug']}' not found")
                            continue
                    
                    elif 'categories' in row and row['categories']:
                        cat_values = str(row['categories']).split(',')
                        for cat_val in cat_values:
                            cat_val = cat_val.strip()
                            category = Category.objects.filter(slug=cat_val).first()
                            if not category:
                                category = Category.objects.filter(name__iexact=cat_val).first()
                            if category:
                                category_ids.append(category.id)
                            else:
                                errors.append(f"Row {index + 1}: Category '{cat_val}' not found")
                    
                    if not category_ids:
                        errors.append(f"Row {index + 1}: No valid categories found")
                        continue
                    
                    # FIXED: Generate slug using Django's slugify
                    slug = row.get('slug')
                    if not slug:
                        slug = slugify(row['name'])  # Use slugify instead of manual regex
                    
                    # Parse boolean values
                    is_active = True
                    if 'is_active' in row and row['is_active']:
                        active_val = str(row['is_active']).lower()
                        is_active = active_val in ['true', 'yes', '1', 'active']
                    
                    is_featured = False
                    if 'featured' in row and row['featured']:
                        featured_val = str(row['featured']).lower()
                        is_featured = featured_val in ['true', 'yes', '1', 'featured']
                    
                    # Parse price and stock
                    price = float(row['price'])
                    discount_price = float(row['discount_price']) if row.get('discount_price') and pd.notna(row['discount_price']) else None
                    stock = int(row.get('stock', 10))
                    sku = row.get('sku', f"BAG-{index+1:04d}")
                    description = row.get('description', '')
                    image_url = row.get('image_url', '')
                    
                    # Create product
                    product, created = Bag.objects.get_or_create(
                        slug=slug,
                        defaults={
                            'name': row['name'],
                            'description': description,
                            'price': price,
                            'discount_price': discount_price,
                            'stock': stock,
                            'sku': sku,
                            'image': image_url,
                            'is_active': is_active,
                            'featured': is_featured
                        }
                    )
                    
                    # If product already exists, update it
                    if not created:
                        product.name = row['name']
                        product.description = description
                        product.price = price
                        product.discount_price = discount_price
                        product.stock = stock
                        product.sku = sku
                        product.image = image_url
                        product.is_active = is_active
                        product.featured = is_featured
                        product.save()
                    
                    # Set multiple categories (many-to-many)
                    product.categories.set(category_ids)
                    
                    products_created.append({
                        'name': product.name,
                        'created': created,
                        'categories': category_ids
                    })
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return Response({
                'success': True,
                'total_processed': len(products_created),
                'products': products_created,
                'errors': errors
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)