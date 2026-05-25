from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import ContactMessage
from .serializers import (
    ContactMessageSerializer, CreateContactSerializer, ReplyContactSerializer
)
import logging

logger = logging.getLogger(__name__)

class SubmitContactView(APIView):
    """
    Submit a contact message (anyone can submit)
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=CreateContactSerializer,
        operation_description="Submit a contact message",
        responses={201: 'Message sent successfully'},
        tags=['Contact']
    )
    def post(self, request):
        serializer = CreateContactSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the message
        try:
            contact = serializer.save()
            logger.info(f"Contact message saved: ID {contact.id} from {contact.email}")
        except Exception as e:
            logger.error(f"Failed to save contact message: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to save your message. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Try to send emails but don't fail if they don't work
        email_errors = []
        
        # Send auto-reply email to customer (try but don't fail)
        try:
            self.send_auto_reply(contact)
            logger.info(f"Auto-reply email sent to {contact.email}")
        except Exception as e:
            email_errors.append(f"Auto-reply: {str(e)}")
            logger.error(f"Auto-reply email failed for {contact.email}: {str(e)}")
        
        # Send notification email to admin (try but don't fail)
        try:
            self.notify_admin(contact)
            logger.info(f"Admin notification sent for message {contact.id}")
        except Exception as e:
            email_errors.append(f"Admin notification: {str(e)}")
            logger.error(f"Admin notification failed for message {contact.id}: {str(e)}")
        
        # Always return success because the message is saved in database
        response_data = {
            'success': True,
            'message': 'Your message has been sent successfully. We will get back to you within 24 hours.',
            'contact_id': contact.id
        }
        
        # Include email warnings if any (for debugging)
        if email_errors:
            response_data['email_warnings'] = email_errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def send_auto_reply(self, contact):
        """Send auto-reply email to customer"""
        subject = f"Thank you for contacting Bag - {contact.subject}"
        message = f"""
Dear {contact.full_name},

Thank you for reaching out to us!

We have received your message regarding "{contact.subject}" and will get back to you within 24 hours.

Your message:
--------------------------------------------------
{contact.message}
--------------------------------------------------

If you need immediate assistance, please call us at +977 9841234567.

Best regards,
Bag Customer Support Team
"""
        
        # Use console backend for development if email not configured
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [contact.email],
            fail_silently=False,
        )
    
    def notify_admin(self, contact):
        """Send notification to admin"""
        subject = f"New Contact Message: {contact.subject} from {contact.full_name}"
        message = f"""
New contact message received:

Name: {contact.full_name}
Email: {contact.email}
Phone: {contact.phone or 'Not provided'}
Subject: {contact.subject}
Date: {contact.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{contact.message}

---
View in admin panel: {getattr(settings, 'SITE_URL', 'http://localhost:8000')}/admin-contacts/
"""
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@bag.com')
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            fail_silently=False,
        )


# ==================== ADMIN VIEWS ====================

class AdminContactListView(APIView):
    """
    Get all contact messages (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get all contact messages (Admin only)",
        responses={200: ContactMessageSerializer(many=True)},
        tags=['Admin - Contact']
    )
    def get(self, request):
        status_filter = request.query_params.get('status', None)
        
        if status_filter:
            messages = ContactMessage.objects.filter(status=status_filter).order_by('-created_at')
        else:
            messages = ContactMessage.objects.all().order_by('-created_at')
        
        serializer = ContactMessageSerializer(messages, many=True)
        
        return Response({
            'success': True,
            'count': messages.count(),
            'messages': serializer.data
        })


class AdminContactDetailView(APIView):
    """
    Get, update, or delete a contact message (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    def get_message(self, message_id):
        try:
            return ContactMessage.objects.get(id=message_id)
        except ContactMessage.DoesNotExist:
            return None
    
    @swagger_auto_schema(
        operation_description="Get contact message details (Admin only)",
        responses={200: ContactMessageSerializer()},
        tags=['Admin - Contact']
    )
    def get(self, request, message_id):
        message = self.get_message(message_id)
        
        if not message:
            return Response({
                'success': False,
                'error': 'Message not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Mark as read if not already
        if message.status == 'pending':
            message.status = 'read'
            message.save()
        
        serializer = ContactMessageSerializer(message)
        return Response({
            'success': True,
            'message': serializer.data
        })
    
    @swagger_auto_schema(
        request_body=ReplyContactSerializer,
        operation_description="Reply to contact message (Admin only)",
        responses={200: 'Reply sent'},
        tags=['Admin - Contact']
    )
    def post(self, request, message_id):
        message = self.get_message(message_id)
        
        if not message:
            return Response({
                'success': False,
                'error': 'Message not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ReplyContactSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save admin reply
        message.admin_reply = serializer.validated_data['admin_reply']
        message.status = serializer.validated_data.get('status', 'replied')
        message.replied_at = timezone.now()
        message.replied_by = request.user
        message.save()
        
        # Send reply email to customer (try but don't fail)
        try:
            self.send_reply_email(message)
        except Exception as e:
            logger.error(f"Reply email failed: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Reply sent successfully',
            'contact': ContactMessageSerializer(message).data
        })
    
    def send_reply_email(self, message):
        """Send reply email to customer"""
        subject = f"Response to your inquiry - {message.subject}"
        email_body = f"""
Dear {message.full_name},

Thank you for contacting Bag. Here's our response to your inquiry:

--------------------------------------------------
Your message: {message.message}
--------------------------------------------------

Our Response:
{message.admin_reply}

--------------------------------------------------

If you have further questions, please don't hesitate to reply to this email or call us at +977 9841234567.

Best regards,
Bag Customer Support Team
"""
        
        send_mail(
            subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [message.email],
            fail_silently=False,
        )
    
    @swagger_auto_schema(
        operation_description="Delete contact message (Admin only)",
        responses={204: 'Message deleted'},
        tags=['Admin - Contact']
    )
    def delete(self, request, message_id):
        message = self.get_message(message_id)
        
        if not message:
            return Response({
                'success': False,
                'error': 'Message not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        message.delete()
        
        return Response({
            'success': True,
            'message': 'Message deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class AdminContactStatsView(APIView):
    """
    Get contact statistics (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get contact statistics (Admin only)",
        responses={200: 'Statistics'},
        tags=['Admin - Contact']
    )
    def get(self, request):
        total = ContactMessage.objects.count()
        pending = ContactMessage.objects.filter(status='pending').count()
        read = ContactMessage.objects.filter(status='read').count()
        replied = ContactMessage.objects.filter(status='replied').count()
        closed = ContactMessage.objects.filter(status='closed').count()
        
        return Response({
            'success': True,
            'stats': {
                'total': total,
                'pending': pending,
                'read': read,
                'replied': replied,
                'closed': closed
            }
        })