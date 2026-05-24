from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated,IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, UpdateProfileSerializer,
    ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer
)
from .models import User
from django.contrib.auth import get_user_model


User=get_user_model()



class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('User created successfully', UserSerializer),
            400: 'Validation error'
        },
        operation_description="Register a new user with email, phone and password",
        operation_summary="User Registration",
        tags=['Auth']
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Registration successful',
                'user': UserSerializer(user).data,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response('Login successful'),
            401: 'Invalid credentials'
        },
        operation_description="Login with email and password",
        operation_summary="User Login",
        tags=['Auth']
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'Bearer'
        })

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={200: UserSerializer()},
        operation_description="Get current user profile",
        operation_summary="Get Profile",
        tags=['Auth']
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'user': serializer.data
        })
    
    @swagger_auto_schema(
        request_body=UpdateProfileSerializer,
        responses={200: UserSerializer()},
        operation_description="Update user profile (full_name, phone)",
        operation_summary="Update Profile",
        tags=['Auth']
    )
    def put(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': UserSerializer(request.user).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Logout user (blacklist refresh token)",
        operation_summary="User Logout",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
            }
        ),
        tags=['Auth'],
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Successfully logged out'
            })
        except Exception:
            return Response({
                'success': False,
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={200: 'Password changed', 400: 'Validation error'},
        operation_description="Change user password",
        operation_summary="Change Password",
        tags=['Auth']
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        if not user.check_password(serializer.validated_data['current_password']):
            return Response({
                'success': False,
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
            },
            required=['refresh_token'],
            tags=['Auth']
        ),
        responses={200: 'New access token', 401: 'Invalid token'},
        operation_description="Refresh access token",
        operation_summary="Refresh Token"
    )
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'success': False,
                'error': 'Refresh token required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            
            return Response({
                'success': True,
                'access_token': str(access_token),
                'token_type': 'Bearer'
            })
        except Exception:
            return Response({
                'success': False,
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=ForgotPasswordSerializer,
        responses={
            200: 'OTP sent to email',
            400: 'Validation error'
        },
        tags=['Auth'],
        operation_description="Request password reset OTP",
        operation_summary="Forgot Password - Request OTP"
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            serializer.save()
            return Response({
                'success': True,
                'message': 'OTP sent to your email address'
            })
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to send OTP. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: 'OTP verified',
            400: 'Invalid OTP'
        },
        operation_description="Verify OTP for password reset",
        operation_summary="Verify OTP",
        tags=['Auth']
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'OTP verified successfully'
        })

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=ResetPasswordSerializer,
        responses={
            200: 'Password reset successful',
            400: 'Validation error'
        },
        operation_description="Reset password using OTP",
        operation_summary="Reset Password",
        tags=['Auth']
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Password reset successful. You can now login with your new password.'
        })


class AdminUserListView(APIView):
    """
    List all users (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get all users (Admin only)",
        responses={200: UserSerializer(many=True)},
        tags=['Admin']
    )
    def get(self, request):
        users = User.objects.filter(is_staff=False, is_superuser=False).order_by('-created_at')
        serializer = UserSerializer(users, many=True)
        return Response({
            'success': True,
            'count': users.count(),
            'users': serializer.data
        })

class AdminUserDetailView(APIView):
    """
    Get, update or delete a user (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get user details (Admin only)",
        responses={200: UserSerializer()},
        tags=['Admin']
    )
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'user': serializer.data
        })
    
    @swagger_auto_schema(
        request_body=UserSerializer,
        operation_description="Update user (Admin only)",
        responses={200: UserSerializer()},
        tags=['Admin']
    )
    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Don't allow admin to change their own role
        if user.id == request.user.id and 'is_staff' in request.data:
            return Response({
                'success': False,
                'error': 'You cannot change your own admin status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'User updated successfully',
                'user': serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Delete user (Admin only)",
        responses={204: 'User deleted'},
        tags=['Admin']
    )
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Don't allow admin to delete themselves
        if user.id == request.user.id:
            return Response({
                'success': False,
                'error': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.delete()
        return Response({
            'success': True,
            'message': 'User deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

class AdminUserStatusToggleView(APIView):
    """
    Toggle user active status (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            }
        ),
        operation_description="Activate/Deactivate user (Admin only)",
        responses={200: 'Status updated'},
        tags=['Admin']
    )
    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Don't allow admin to deactivate themselves
        if user.id == request.user.id:
            return Response({
                'success': False,
                'error': 'You cannot change your own status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        is_active = request.data.get('is_active', not user.is_active)
        user.is_active = is_active
        user.save()
        
        return Response({
            'success': True,
            'message': f'User {"activated" if is_active else "deactivated"} successfully',
            'user': UserSerializer(user).data
        })

class AdminUserRoleUpdateView(APIView):
    """
    Update user role (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'staff', 'admin']),
            }
        ),
        operation_description="Update user role (Admin only)",
        responses={200: 'Role updated'},
        tags=['Admin']
    )
    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Don't allow admin to change their own role
        if user.id == request.user.id:
            return Response({
                'success': False,
                'error': 'You cannot change your own role'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        role = request.data.get('role')
        
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'staff':
            user.is_staff = True
            user.is_superuser = False
        elif role == 'user':
            user.is_staff = False
            user.is_superuser = False
        else:
            return Response({
                'success': False,
                'error': 'Invalid role. Choose: user, staff, or admin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.save()
        
        return Response({
            'success': True,
            'message': f'User role updated to {role}',
            'user': UserSerializer(user).data
        })