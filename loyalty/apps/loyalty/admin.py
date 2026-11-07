from django.contrib import admin

from .models import Canje, ProgramaFidelizacion, Visita


@admin.register(ProgramaFidelizacion)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ("negocio", "nombre", "visitas_requeridas", "descripcion_premio", "activo")
    list_filter = ("negocio", "activo")


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ("cliente", "local", "creado_en")
    list_filter = ("negocio", "local")
    date_hierarchy = "creado_en"

    # Historial inmutable: se puede ver, pero no editar ni borrar
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Canje)
class CanjeAdmin(admin.ModelAdmin):
    list_display = ("cliente", "local", "visitas_consumidas", "creado_en")
    list_filter = ("negocio", "local")