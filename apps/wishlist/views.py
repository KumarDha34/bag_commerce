from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Wishlist, WishlistItem
from .serializers import (
    WishlistSerializer, AddToWishlistSerializer, WishlistItemSerializer
)
from apps.products.models import Bag


class GetWishlistView(APIView):
    """
    Get current user's wishlist
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user's wishlist",
        responses={200: WishlistSerializer()},
        tags=['Wishlist']
    )
    def get(self, request):
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistSerializer(wishlist)
        return Response({
            'success': True,
            'wishlist': serializer.data
        })

class AddToWishlistView(APIView):
    """
    Add a product to wishlist
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=AddToWishlistSerializer,
        operation_description="Add a bag to wishlist",
        responses={
            200: WishlistSerializer(),
            400: 'Validation error',
            404: 'Product not found'
        },
        tags=['Wishlist']
    )
    def post(self, request):
        serializer = AddToWishlistSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        bag_id = serializer.validated_data['bag_id']
        
        # Get or create wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Get product
        try:
            bag = Bag.objects.get(id=bag_id, is_active=True)
        except Bag.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already in wishlist
        if WishlistItem.objects.filter(wishlist=wishlist, bag=bag).exists():
            return Response({
                'success': False,
                'error': 'Product already in wishlist'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add to wishlist
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            bag=bag
        )
    
        serializer = WishlistSerializer(wishlist)
        return Response({
            'success': True,
            'message': f'{bag.name} added to wishlist',
            'wishlist': serializer.data
        }, status=status.HTTP_201_CREATED)

class RemoveFromWishlistView(APIView):
    """
    Remove a product from wishlist
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Remove a bag from wishlist",
        responses={
            200: WishlistSerializer(),
            404: 'Item not found'
        },
        tags=['Wishlist']
    )
    def delete(self, request, bag_id):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, bag_id=bag_id)
            bag_name = wishlist_item.bag.name
            wishlist_item.delete()
        except Wishlist.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Wishlist not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except WishlistItem.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Item not found in wishlist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WishlistSerializer(wishlist)
        return Response({
            'success': True,
            'message': f'{bag_name} removed from wishlist',
            'wishlist': serializer.data
        })


class ClearWishlistView(APIView):
    """
    Clear entire wishlist
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Remove all items from wishlist",
        responses={
            200: 'Wishlist cleared',
            404: 'Wishlist not found'
        },
        tags=['Wishlist']
    )
    def delete(self, request):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist.items.all().delete()
        except Wishlist.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Wishlist not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'Wishlist cleared successfully'
        })


class MoveToCartView(APIView):
    """
    Move a product from wishlist to cart
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Move a bag from wishlist to cart",
        responses={
            200: 'Moved to cart',
            400: 'Out of stock',
            404: 'Item not found'
        },
        tags=['Wishlist']
    )
    def post(self, request, bag_id):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_item = WishlistItem.objects.get(wishlist=wishlist, bag_id=bag_id)
            bag = wishlist_item.bag
        except Wishlist.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Wishlist not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except WishlistItem.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Item not found in wishlist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check stock
        if bag.stock < 1:
            return Response({
                'success': False,
                'error': 'Product is out of stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create cart
        from apps.carts.models import Cart, CartItem
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Add to cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            bag=bag,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        # Remove from wishlist
        wishlist_item.delete()
        
        return Response({
            'success': True,
            'message': f'{bag.name} moved to cart successfully'
        })


class CheckIfInWishlistView(APIView):
    """
    Check if a product is in user's wishlist
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check if a product is in wishlist",
        responses={200: 'Check result'},
        tags=['Wishlist']
    )
    def get(self, request, bag_id):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            in_wishlist = WishlistItem.objects.filter(wishlist=wishlist, bag_id=bag_id).exists()
        except Wishlist.DoesNotExist:
            in_wishlist = False
        
        return Response({
            'success': True,
            'bag_id': bag_id,
            'in_wishlist': in_wishlist
        })