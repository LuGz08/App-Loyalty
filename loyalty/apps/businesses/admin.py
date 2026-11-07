from django.contrib import admin

from .models import Local, Negocio


class LocalInline(admin.TabularInline):
    model = Local
    extra = 0


@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "plan", "activo")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [LocalInline]