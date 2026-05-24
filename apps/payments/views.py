from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import BankQR, Payment
from .serializers import (
    BankQRSerializer, PaymentSerializer, 
    SubmitPaymentSerializer, VerifyPaymentSerializer
)
from apps.orders.models import Order

class GetBankQRView(APIView):
    """
    Get shop's bank QR code for payment
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get shop's bank QR code for payment",
        responses={200: BankQRSerializer()},
        tags=['Payments']
    )
    def get(self, request):
        # Get active bank QR code
        bank_qr = BankQR.objects.filter(is_active=True).first()
        
        if not bank_qr:
            return Response({
                'success': False,
                'error': 'Bank QR code not configured. Please contact support.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BankQRSerializer(bank_qr)
        
        return Response({
            'success': True,
            'bank_qr': serializer.data,
            'payment_instructions': {
                'step1': 'Open your banking app (Google Pay, PhonePe, Paytm, or Bank App)',
                'step2': 'Scan the QR code below',
                'step3': 'Enter the exact amount shown in your order',
                'step4': 'Make the payment',
                'step5': 'Save the transaction ID or take a screenshot',
                'step6': 'Submit the payment details using the submit-payment endpoint'
            }
        })

class GetBankQRImageView(APIView):
    """
    Get QR code image directly
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get QR code image file",
        responses={200: 'PNG image'},
        tags=['Payments']
    )
    def get(self, request):
        bank_qr = BankQR.objects.filter(is_active=True).first()
        
        if not bank_qr or not bank_qr.qr_code_image:
            return Response({
                'success': False,
                'error': 'QR code not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'qr_image_url': bank_qr.qr_code_image.url
        })

class SubmitPaymentView(APIView):
    """
    Submit payment proof after scanning QR
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=SubmitPaymentSerializer,
        operation_description="Submit payment proof (transaction ID or screenshot)",
        responses={200: 'Payment submitted'},
        tags=['Payments']
    )
    def post(self, request):
        serializer = SubmitPaymentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order_id = serializer.validated_data['order_id']
        
        # Get order
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if order can be paid
        if order.order_status not in ['pending', 'awaiting_verification']:
            return Response({
                'success': False,
                'error': f'Payment cannot be submitted. Order status: {order.order_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if payment already exists
        payment, created = Payment.objects.get_or_create(
            order=order,
            user=request.user,
            defaults={
                'amount': order.total_amount,
                'payment_method': serializer.validated_data['payment_method'],
                'status': 'awaiting_verification'
            }
        )
        
        if not created and payment.status == 'verified':
            return Response({
                'success': False,
                'error': 'Payment already verified for this order'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update payment details
        if serializer.validated_data.get('transaction_id'):
            payment.transaction_id = serializer.validated_data['transaction_id']
        
        if serializer.validated_data.get('payment_screenshot'):
            payment.payment_screenshot = serializer.validated_data['payment_screenshot']
        
        payment.payment_method = serializer.validated_data['payment_method']
        payment.status = 'awaiting_verification'
        payment.save()
        
        # Update order status
        order.order_status = 'awaiting_verification'
        order.payment_status = 'awaiting_verification'
        order.save()
        
        return Response({
            'success': True,
            'message': 'Payment proof submitted successfully. Admin will verify your payment.',
            'payment': {
                'id': payment.id,
                'order_number': order.order_number,
                'amount': float(payment.amount),
                'status': payment.status,
                'submitted_at': payment.payment_date
            }
        })

class PaymentStatusView(APIView):
    """
    Check payment status for an order
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check payment status for an order",
        responses={200: 'Payment status'},
        tags=['Payments']
    )
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            payment = Payment.objects.get(order=order)
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment not submitted yet'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'payment': {
                'order_number': order.order_number,
                'amount': float(payment.amount),
                'status': payment.status,
                'submitted_at': payment.payment_date,
                'verified_at': payment.verified_at,
                'order_status': order.order_status
            }
        })

# ==================== ADMIN VIEWS ====================

class AdminBankQRManageView(APIView):
    """
    Upload and manage bank QR code (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Upload bank QR code (Admin only)",
        request_body=BankQRSerializer,
        responses={201: 'QR Code uploaded'},
        tags=['Admin - Payments']
    )
    def post(self, request):
        serializer = BankQRSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Bank QR code uploaded successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Get all bank QR codes (Admin only)",
        responses={200: BankQRSerializer(many=True)},
        tags=['Admin - Payments']
    )
    def get(self, request):
        qr_codes = BankQR.objects.all()
        serializer = BankQRSerializer(qr_codes, many=True)
        return Response({
            'success': True,
            'qr_codes': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Update bank QR code (Admin only)",
        responses={200: 'QR Code updated'},
        tags=['Admin - Payments']
    )
    def put(self, request, qr_id):
        try:
            bank_qr = BankQR.objects.get(id=qr_id)
        except BankQR.DoesNotExist:
            return Response({
                'success': False,
                'error': 'QR code not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BankQRSerializer(bank_qr, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'QR code updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Delete bank QR code (Admin only)",
        responses={204: 'QR Code deleted'},
        tags=['Admin - Payments']
    )
    def delete(self, request, qr_id):
        try:
            bank_qr = BankQR.objects.get(id=qr_id)
            bank_qr.delete()
            return Response({
                'success': True,
                'message': 'QR code deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except BankQR.DoesNotExist:
            return Response({
                'success': False,
                'error': 'QR code not found'
            }, status=status.HTTP_404_NOT_FOUND)

class AdminPendingPaymentsView(APIView):
    """
    Get all pending payments for verification (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get pending payments awaiting verification (Admin only)",
        responses={200: 'Pending payments'},
        tags=['Admin - Payments']
    )
    def get(self, request):
        payments = Payment.objects.filter(status='awaiting_verification')
        
        data = []
        for payment in payments:
            data.append({
                'id': payment.id,
                'order_number': payment.order.order_number,
                'customer_name': payment.order.full_name,
                'customer_email': payment.order.email,
                'customer_phone': payment.order.phone,
                'amount': float(payment.amount),
                'transaction_id': payment.transaction_id,
                'payment_screenshot': payment.payment_screenshot.url if payment.payment_screenshot else None,
                'submitted_at': payment.payment_date,
                'order_details': {
                    'address': payment.order.address,
                    'city': payment.order.city,
                    'state': payment.order.state,
                    'pincode': payment.order.pincode,
                    'items_count': payment.order.items.count()
                }
            })
        
        return Response({
            'success': True,
            'pending_count': len(data),
            'payments': data
        })

class AdminVerifyPaymentView(APIView):
    """
    Verify or reject customer payment (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        request_body=VerifyPaymentSerializer,
        operation_description="Verify or reject payment (Admin only)",
        responses={200: 'Payment verified'},
        tags=['Admin - Payments']
    )
    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_id = serializer.validated_data['payment_id']
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        order = payment.order
        
        if action == 'verify':
            payment.status = 'verified'
            payment.verified_at = timezone.now()
            payment.verified_by = request.user
            payment.notes = notes
            
            # Update order status
            order.order_status = 'confirmed'
            order.payment_status = 'completed'
            order.save()
            
            message = f'Payment verified successfully. Order #{order.order_number} is now confirmed.'
            
        else:  # reject
            payment.status = 'failed'
            payment.notes = notes
            
            # Restore product stock
            for item in order.items.all():
                item.product.stock += item.quantity
                item.product.save()
            
            # Update order status
            order.order_status = 'cancelled'
            order.payment_status = 'failed'
            order.save()
            
            message = f'Payment rejected. Order #{order.order_number} has been cancelled.'
        
        payment.save()
        
        return Response({
            'success': True,
            'message': message,
            'payment': PaymentSerializer(payment).data
        })

class AdminAllPaymentsView(APIView):
    """
    Get all payments (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get all payments (Admin only)",
        responses={200: 'All payments'},
        tags=['Admin - Payments']
    )
    def get(self, request):
        payments = Payment.objects.all().order_by('-payment_date')
        
        data = []
        for payment in payments:
            data.append({
                'id': payment.id,
                'order_id': payment.order.id,
                'order_number': payment.order.order_number,
                'customer_name': payment.order.full_name,     
                'customer_email': payment.order.email,       
                'customer_phone': payment.order.phone,       
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'payment_screenshot': payment.payment_screenshot.url if payment.payment_screenshot else None,
                'status': payment.status,
                'payment_date': payment.payment_date,
                'verified_at': payment.verified_at,
                'notes': payment.notes
            })
        
        return Response({
            'success': True,
            'total_payments': payments.count(),
            'payments': data
        })