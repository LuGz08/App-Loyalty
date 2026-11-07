from django.contrib import admin

from .models import TagNFC


@admin.register(TagNFC)
class TagNFCAdmin(admin.ModelAdmin):
    list_display = ("uid", "local", "etiqueta", "activo")
    list_filter = ("local__negocio", "activo")
    search_fields = ("uid",)