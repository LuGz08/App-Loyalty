from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("email", "negocio", "contador_visitas", "visitas_totales", "acepta_marketing")
    list_filter = ("negocio", "acepta_marketing")
    search_fields = ("email",)
