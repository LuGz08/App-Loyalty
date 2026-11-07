from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Negocio", {"fields": ("negocio",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Negocio", {"fields": ("negocio",)}),
    )
    list_display = ("username", "email", "negocio", "is_staff")
    list_filter = UserAdmin.list_filter + ("negocio",)