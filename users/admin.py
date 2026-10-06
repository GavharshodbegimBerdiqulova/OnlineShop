from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, User, VerificationCode


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display = ("id", "email", "phone", "username", "first_name", "last_name", "role", "is_verified", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Shaxsiy ma'lumot", {"fields": ("username", "first_name", "last_name", "phone", "avatar", "birth_date")}),
        ("Ruxsatlar", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)
    search_fields = ("email", "phone", "username", "first_name", "last_name")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "city", "street", "is_default")


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("contact", "purpose", "is_used", "attempts", "created_at")
