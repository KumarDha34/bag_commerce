from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Cart, CartItem
from .serializers import (
    CartSerializer, AddToCartSerializer, 
    UpdateCartItemSerializer, CartItemSerializer
)
from apps.products.models import Bag

class GetCartView(APIView):
    """
    Get current user's cart
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user's shopping cart",
        responses={200: CartSerializer()},
        tags=['Cart']
    )
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'cart': serializer.data
        })


class AddToCartView(APIView):
    """
    Add a product to cart
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=AddToCartSerializer,
        operation_description="Add a bag to shopping cart",
        responses={
            200: CartSerializer(),
            400: 'Validation error',
            404: 'Product not found'
        },
        tags=['Cart']
    )
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        bag_id = serializer.validated_data['bag_id']
        quantity = serializer.validated_data['quantity']
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Get product
        try:
            bag = Bag.objects.get(id=bag_id, is_active=True)
        except Bag.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check stock
        if bag.stock < quantity:
            return Response({
                'success': False,
                'error': f'Only {bag.stock} items available in stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            bag=bag,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Check if new quantity exceeds stock
            new_quantity = cart_item.quantity + quantity
            if bag.stock < new_quantity:
                return Response({
                    'success': False,
                    'error': f'Cannot add {quantity} more. Only {bag.stock - cart_item.quantity} available'
                }, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # Update cart timestamp
        cart.save()
        
        cart_serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'message': f'{bag.name} added to cart',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    """
    Update cart item quantity
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=UpdateCartItemSerializer,
        operation_description="Update quantity of a cart item",
        responses={
            200: CartSerializer(),
            400: 'Validation error',
            404: 'Item not found'
        },
        tags=['Cart']
    )
    def put(self, request, item_id):
        serializer = UpdateCartItemSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_quantity = serializer.validated_data['quantity']
        
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Cart not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except CartItem.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Item not found in cart'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check stock
        if cart_item.bag.stock < new_quantity:
            return Response({
                'success': False,
                'error': f'Only {cart_item.bag.stock} items available'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
        
        cart_serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'message': 'Cart updated successfully',
            'cart': cart_serializer.data
        })


class RemoveFromCartView(APIView):
    """
    Remove item from cart
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Remove an item from shopping cart",
        responses={
            200: CartSerializer(),
            404: 'Item not found'
        },
        tags=['Cart']
    )
    def delete(self, request, item_id):
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            bag_name = cart_item.bag.name
            cart_item.delete()
        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Cart not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except CartItem.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Item not found in cart'
            }, status=status.HTTP_404_NOT_FOUND)
        
        cart_serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'message': f'{bag_name} removed from cart',
            'cart': cart_serializer.data
        })

class ClearCartView(APIView):
    """
    Clear entire cart
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Remove all items from shopping cart",
        responses={
            200: 'Cart cleared',
            404: 'Cart not found'
        },
        tags=['Cart']
    )
    def delete(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Cart not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'Cart cleared successfully'
        })

class CartSummaryView(APIView):
    """
    Get cart summary with totals
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get cart summary with totals",
        responses={200: CartSerializer()},
        tags=['Cart']
    )
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        return Response({
            'success': True,
            'summary': {
                'total_items': cart.total_items,
                'subtotal': float(cart.subtotal),
                'total_discount': float(cart.total_discount),
                'total': float(cart.total),
                'shipping_charge': 0,
                'grand_total': float(cart.total)
            },
            'items': CartItemSerializer(cart.items.all(), many=True).data
        })