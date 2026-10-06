from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, User, VerificationCode


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "role", "is_verified", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Shaxsiy ma'lumot", {"fields": ("first_name", "last_name", "phone", "avatar", "birth_date")}),
        ("Ruxsatlar", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)
    search_fields = ("email", "first_name", "last_name")


admin.site.register(Address)
admin.site.register(VerificationCode)
