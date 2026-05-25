from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Avg
from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer
from apps.products.models import Bag
from apps.orders.models import OrderItem


class CreateReviewView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=CreateReviewSerializer,
        operation_description="Create a product review",
        responses={201: ReviewSerializer()},
        tags=['Reviews']
    )
    def post(self, request):
        serializer = CreateReviewSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        product = serializer.validated_data['product']
        
        has_purchased_and_delivered = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__order_status='delivered'  # Must be delivered
        ).exists()
        
        if not has_purchased_and_delivered:
            return Response({
                'success': False,
                'error': 'You can only review products you have purchased and received (delivered).'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if already reviewed
        if Review.objects.filter(user=request.user, product=product).exists():
            return Response({
                'success': False,
                'error': 'You have already reviewed this product.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create review (requires admin approval in real-world)
        review = Review.objects.create(
            user=request.user,
            product=product,
            rating=serializer.validated_data['rating'],
            comment=serializer.validated_data['comment'],
            is_approved=False  # Admin must approve
        )
        
        return Response({
            'success': True,
            'message': 'Review submitted successfully. It will appear after admin approval.',
            'review': ReviewSerializer(review).data
        }, status=status.HTTP_201_CREATED)


class UpdateReviewView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=CreateReviewSerializer,
        operation_description="Update your review",
        responses={200: ReviewSerializer()},
        tags=['Reviews']
    )
    def put(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id, user=request.user)
        except Review.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CreateReviewSerializer(review, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Review updated successfully',
                'review': ReviewSerializer(review).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DeleteReviewView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Delete your review",
        responses={200: 'Review deleted'},
        tags=['Reviews']
    )
    def delete(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id, user=request.user)
            review.delete()
            return Response({
                'success': True,
                'message': 'Review deleted successfully'
            })
        except Review.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ProductReviewsView(APIView):
    permission_classes = []
    
    @swagger_auto_schema(
        operation_description="Get all reviews for a product",
        responses={200: ReviewSerializer(many=True)},
        tags=['Reviews']
    )
    def get(self, request, product_slug):
        try:
            product = Bag.objects.get(slug=product_slug, is_active=True)
        except Bag.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        reviews = Review.objects.filter(product=product, is_approved=True)
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        serializer = ReviewSerializer(reviews, many=True)
        
        return Response({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'slug': product.slug
            },
            'rating_summary': {
                'average_rating': round(avg_rating, 1) if avg_rating else 0,
                'total_reviews': reviews.count()
            },
            'reviews': serializer.data
        })


class UserReviewsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get all your reviews",
        responses={200: ReviewSerializer(many=True)},
        tags=['Reviews']
    )
    def get(self, request):
        reviews = Review.objects.filter(user=request.user)
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'success': True,
            'count': reviews.count(),
            'reviews': serializer.data
        })


class CanReviewProductView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check if you can review this product",
        responses={200: 'Can review status'},
        tags=['Reviews']
    )
    def get(self, request, product_id):
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product_id=product_id,
            order__order_status='delivered'
        ).exists()
        
        already_reviewed = Review.objects.filter(
            user=request.user,
            product_id=product_id
        ).exists()
        
        return Response({
            'success': True,
            'can_review': has_purchased and not already_reviewed,
            'has_purchased': has_purchased,
            'already_reviewed': already_reviewed
        })


class AdminPendingReviewsView(APIView):
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get pending reviews (Admin only)",
        responses={200: ReviewSerializer(many=True)},
        tags=['Admin - Reviews']
    )
    def get(self, request):
        reviews = Review.objects.filter(is_approved=False)
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'success': True,
            'pending_count': reviews.count(),
            'reviews': serializer.data
        })


class AdminApproveReviewView(APIView):
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Approve a review (Admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve', 'reject']),
            }
        ),
        responses={200: 'Review approved/rejected'},
        tags=['Admin - Reviews']
    )
    def post(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        action = request.data.get('action')
        
        if action == 'approve':
            review.is_approved = True
            review.save()
            message = 'Review approved successfully'
        elif action == 'reject':
            review.delete()
            message = 'Review rejected and deleted'
        else:
            return Response({
                'success': False,
                'error': 'Invalid action. Use "approve" or "reject"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': message
        })


class AdminAllReviewsView(APIView):
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get all reviews (Admin only)",
        responses={200: ReviewSerializer(many=True)},
        tags=['Admin - Reviews']
    )
    def get(self, request):
        reviews = Review.objects.all().order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'success': True,
            'total_reviews': reviews.count(),
            'reviews': serializer.data
        })