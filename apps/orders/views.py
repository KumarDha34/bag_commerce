from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, CreateOrderSerializer, 
    UpdateOrderStatusSerializer, OrderItemSerializer
)
from apps.payments.models import Payment
from apps.carts.models import Cart, CartItem
from datetime import timedelta

class CreateOrderView(APIView):
    """
    Create order from cart
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=CreateOrderSerializer,
        operation_description="Create a new order from cart",
        responses={201: OrderSerializer()},
        tags=['Orders']
    )
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Cart is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not cart.items.exists():
            return Response({
                'success': False,
                'error': 'Cart is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate totals
        subtotal = cart.subtotal
        discount_amount = cart.total_discount
        shipping_charge = 0  # Free shipping
        total_amount = subtotal
        
        # Check stock before creating order
        for cart_item in cart.items.all():
            if cart_item.bag.stock < cart_item.quantity:
                return Response({
                    'success': False,
                    'error': f'Insufficient stock for {cart_item.bag.name}. Only {cart_item.bag.stock} available.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method = serializer.validated_data['payment_method']
        
        # Create order - REMOVED city, state, pincode, landmark, payment_method
        order = Order.objects.create(
            user=request.user,
            full_name=serializer.validated_data['full_name'],
            email=serializer.validated_data['email'],
            phone=serializer.validated_data['phone'],
            address=serializer.validated_data['address'],
            subtotal=subtotal,
            discount_amount=discount_amount,
            shipping_charge=shipping_charge,
            total_amount=total_amount,
            payment_status='pending',
            order_status='pending'
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.bag,
                product_name=cart_item.bag.name,
                product_sku=cart_item.bag.sku,
                product_price=cart_item.bag_price,
                quantity=cart_item.quantity,
                total_price=cart_item.total_price
            )
            
            # Reduce stock
            cart_item.bag.stock -= cart_item.quantity
            cart_item.bag.save()
        
        # Clear cart
        cart.items.all().delete()
        
        # Handle payment methods
        if payment_method == 'cod':
            order.order_status = 'confirmed'
            order.payment_status = 'pending'
            order.save()
            Payment.objects.create(
                order=order,
                user=request.user,
                amount=order.total_amount,
                payment_method='cod',
                status='pending',
                transaction_id=f'COD-{order.order_number}'
            )
        elif payment_method == 'bank_qr':
            order.order_status = 'pending'
            order.payment_status = 'pending'
            order.save()
        
        order_serializer = OrderSerializer(order)
        
        return Response({
            'success': True,
            'message': 'Order created successfully',
            'order': order_serializer.data,
            'payment_action': {
                'method': payment_method,
                'order_id': order.id,
                'order_number': order.order_number,
                'amount': float(total_amount)
            }
        }, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    """
    Get user's orders
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        # Manually build orders with items
        orders_data = []
        for order in orders:
            # Get order items
            items = OrderItem.objects.filter(order=order).select_related('product')
            items_data = []
            for item in items:
                items_data.append({
                    'id': item.id,
                    'product_name': item.product_name,
                    'product_sku': item.product_sku,
                    'quantity': item.quantity,
                    'product_price': float(item.product_price),
                    'total_price': float(item.total_price),
                    'product_details': {
                        'image': item.product.image.url if item.product and item.product.image else None
                    } if item.product else None
                })
            
            # Get payment method from Payment model
            payment_method = 'cod'
            try:
                payment = Payment.objects.get(order=order)
                payment_method = payment.payment_method
            except Payment.DoesNotExist:
                pass
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'full_name': order.full_name,
                'email': order.email,
                'phone': order.phone,
                'address': order.address,
                'subtotal': float(order.subtotal),
                'discount_amount': float(order.discount_amount),
                'shipping_charge': float(order.shipping_charge),
                'total_amount': float(order.total_amount),
                'order_status': order.order_status,
                'payment_status': order.payment_status,
                'payment_method': payment_method,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': items_data
            })
        
        return Response({
            'success': True,
            'count': orders.count(),
            'orders': orders_data
        })

class OrderDetailView(APIView):
    """
    Get order details - accessible by order owner or admin
    """
    
    def get_permissions(self):
        # Allow both authenticated users and admin
        return [IsAuthenticated()]
    
    def get(self, request, order_id):
        # Check if user is admin
        is_admin = request.user.is_staff or request.user.is_superuser
        
        try:
            if is_admin:
                # Admin can view any order
                order = Order.objects.get(id=order_id)
            else:
                # Regular user can only view their own orders
                order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get order items with product details
        items = OrderItem.objects.filter(order=order).select_related('product')
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'quantity': item.quantity,
                'product_price': float(item.product_price),
                'total_price': float(item.total_price),
                'product_details': {
                    'image': item.product.image.url if item.product and item.product.image else None
                } if item.product else None
            })
        
        # Get payment method from Payment model
        payment_method = 'cod'
        try:
            payment = Payment.objects.get(order=order)
            payment_method = payment.payment_method
        except Payment.DoesNotExist:
            # Determine from order status
            if order.order_status == 'confirmed':
                payment_method = 'cod'
            else:
                payment_method = 'bank_qr'
        
        return Response({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'full_name': order.full_name,
                'email': order.email,
                'phone': order.phone,
                'address': order.address,
                'subtotal': float(order.subtotal),
                'discount_amount': float(order.discount_amount),
                'shipping_charge': float(order.shipping_charge),
                'total_amount': float(order.total_amount),
                'order_status': order.order_status,
                'payment_status': order.payment_status,
                'payment_method': payment_method,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': items_data
            }
        })

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if order.order_status not in ['pending', 'confirmed']:
            return Response({
                'success': False,
                'error': f'Order cannot be cancelled. Current status: {order.order_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()
        
        order.order_status = 'cancelled'
        if order.payment_status == 'completed':
            order.payment_status = 'refunded'
        order.save()
        
        return Response({
            'success': True,
            'message': 'Order cancelled successfully',
            'order': OrderSerializer(order).data
        })

class TrackOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get order items
        items = OrderItem.objects.filter(order=order).select_related('product')
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'product_name': item.product_name,
                'quantity': item.quantity,
                'product_price': float(item.product_price),
                'total_price': float(item.total_price),
                'product_details': {
                    'image': item.product.image.url if item.product and item.product.image else None
                } if item.product else None
            })
        
        # Get payment method from Payment record
        payment_method = 'cod'  # Default
        try:
            payment = Payment.objects.get(order=order)
            payment_method = payment.payment_method
        except Payment.DoesNotExist:
            # If no payment record, determine from order status
            if order.order_status == 'confirmed':
                payment_method = 'cod'
            else:
                payment_method = 'bank_qr'
        
        return Response({
            'success': True,
            'order': {
                'order_number': order.order_number,
                'status': order.order_status,
                'payment_status': order.payment_status,
                'payment_method': payment_method,  
                'total_amount': float(order.total_amount),
                'subtotal': float(order.subtotal),
                'discount_amount': float(order.discount_amount),
                'full_name': order.full_name,
                'email': order.email,
                'phone': order.phone,
                'address': order.address,
                'created_at': order.created_at,
                'estimated_delivery': order.created_at + timedelta(days=7),
                'items': items_data
            },
            'timeline': {
                'pending': {'status': 'Pending', 'completed': order.order_status != 'pending'},
                'confirmed': {'status': 'Confirmed', 'completed': order.order_status in ['confirmed', 'processing', 'shipped', 'delivered']},
                'processing': {'status': 'Processing', 'completed': order.order_status in ['processing', 'shipped', 'delivered']},
                'shipped': {'status': 'Shipped', 'completed': order.order_status in ['shipped', 'delivered']},
                'delivered': {'status': 'Delivered', 'completed': order.order_status == 'delivered'}
            }
        })
# Admin Views
class AdminOrderListView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        orders = Order.objects.all().order_by('-created_at')
        orders_data = []
        for order in orders:
            # Get payment method from Payment model
            payment_method = None
            try:
                payment = Payment.objects.get(order=order)
                payment_method = payment.payment_method
            except Payment.DoesNotExist:
                # If no payment record, try to determine from order status
                if order.order_status == 'confirmed':
                    payment_method = 'cod'
                else:
                    payment_method = 'bank_qr'
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'full_name': order.full_name,
                'email': order.email,
                'phone': order.phone,
                'address': order.address,
                'subtotal': float(order.subtotal),
                'discount_amount': float(order.discount_amount),
                'shipping_charge': float(order.shipping_charge),
                'total_amount': float(order.total_amount),
                'order_status': order.order_status,
                'payment_status': order.payment_status,
                'payment_method': payment_method,  # ← ADD THIS LINE
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'items': []
            })
        
        return Response({
            'success': True,
            'count': orders.count(),
            'orders': orders_data
        })

class AdminUpdateOrderStatusView(APIView):
    permission_classes = [IsAdminUser]
    
    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UpdateOrderStatusSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['order_status']
        order.order_status = new_status
        
        if new_status == 'delivered':
            from django.utils import timezone
            order.delivered_at = timezone.now()
        
        order.save()
        
        return Response({
            'success': True,
            'message': f'Order status updated to {new_status}',
            'order': OrderSerializer(order).data
        })