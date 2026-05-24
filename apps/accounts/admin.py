from django.contrib import admin
from .models import User, PasswordResetOTP
# Register your models here.
admin.site.register(User)
admin.site.register(PasswordResetOTP)