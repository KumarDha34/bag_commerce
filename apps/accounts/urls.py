from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, LogoutView,
    ChangePasswordView, RefreshTokenView, ForgotPasswordView,
    VerifyOTPView, ResetPasswordView,AdminUserDetailView,AdminUserListView,AdminUserStatusToggleView,AdminUserRoleUpdateView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    
    # Forgot Password
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:user_id>/toggle-status/', AdminUserStatusToggleView.as_view(), name='admin-user-toggle-status'),
    path('admin/users/<int:user_id>/update-role/', AdminUserRoleUpdateView.as_view(), name='admin-user-update-role'),
]