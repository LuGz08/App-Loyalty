from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.businesses.models import Local
from apps.customers.models import Cliente
from apps.nfc.models import TagNFC

from .models import Canje, ProgramaFidelizacion, Visita


# --- Errores esperados del negocio (no son bugs) ---------------------------
class ErrorFidelizacion(Exception):
    """Base de todos los rechazos normales del sistema."""


class TagInvalido(ErrorFidelizacion):
    pass


class ClienteInvalido(ErrorFidelizacion):
    pass


class SinPrograma(ErrorFidelizacion):
    pass


class PermisoDenegado(ErrorFidelizacion):
    pass


class PremioNoDisponible(ErrorFidelizacion):
    pass


class VisitaMuyPronto(ErrorFidelizacion):
    def __init__(self, segundos_restantes):
        self.segundos_restantes = segundos_restantes
        super().__init__("Esta visita es muy reciente, intenta más tarde.")


@dataclass
class ResultadoVisita:
    visita: Visita
    contador: int
    requeridas: int
    premio_disponible: bool


# --- Registrar una visita (toque NFC) --------------------------------------
def registrar_visita(*, tag_uid, cliente_id):
    tag = (
        TagNFC.objects.select_related("local__negocio")
        .filter(
            uid=tag_uid,
            activo=True,
            local__activo=True,
            local__negocio__activo=True,
        )
        .first()
    )
    if tag is None:
        raise TagInvalido("Chip no reconocido o desactivado.")
    local = tag.local

    with transaction.atomic():
        # Bloquea la fila del cliente: toques simultáneos se procesan de a uno.
        # Filtrar por negocio también garantiza que el cliente sea de este tenant.
        try:
            cliente = Cliente.objects.select_for_update().get(
                pk=cliente_id, negocio_id=local.negocio_id
            )
        except Cliente.DoesNotExist:
            raise ClienteInvalido("Cliente no encontrado en este negocio.")

        programa = ProgramaFidelizacion.objects.filter(
            negocio_id=local.negocio_id, activo=True
        ).first()
        if programa is None:
            raise SinPrograma("Este negocio no tiene un programa activo.")

        # Tiempo mínimo entre visitas
        if programa.minutos_entre_visitas:
            ultima = cliente.visitas.order_by("-creado_en").first()
            if ultima is not None:
                disponible_desde = ultima.creado_en + timedelta(
                    minutes=programa.minutos_entre_visitas
                )
                restante = disponible_desde - timezone.now()
                if restante > timedelta(0):
                    raise VisitaMuyPronto(int(restante.total_seconds()) + 1)

        visita = Visita(negocio=local.negocio, local=local, cliente=cliente, tag=tag)
        visita.full_clean()  # aquí se ejecuta el clean() de coherencia entre negocios
        visita.save()

        cliente.contador_visitas += 1
        cliente.visitas_totales += 1
        cliente.save(update_fields=["contador_visitas", "visitas_totales", "actualizado_en"])

    return ResultadoVisita(
        visita=visita,
        contador=cliente.contador_visitas,
        requeridas=programa.visitas_requeridas,
        premio_disponible=cliente.contador_visitas >= programa.visitas_requeridas,
    )


# --- Canjear el premio (lo hace el encargado) ------------------------------
def canjear_premio(*, cliente_id, local_id, usuario):
    if not usuario.es_encargado:
        raise PermisoDenegado("Solo un encargado de local puede canjear premios.")

    with transaction.atomic():
        try:
            local = Local.objects.get(pk=local_id, negocio_id=usuario.negocio_id)
        except Local.DoesNotExist:
            raise PermisoDenegado("Ese local no pertenece a tu negocio.")

        try:
            cliente = Cliente.objects.select_for_update().get(
                pk=cliente_id, negocio_id=usuario.negocio_id
            )
        except Cliente.DoesNotExist:
            raise ClienteInvalido("Cliente no encontrado en tu negocio.")

        programa = ProgramaFidelizacion.objects.filter(
            negocio_id=usuario.negocio_id, activo=True
        ).first()
        if programa is None:
            raise SinPrograma("Tu negocio no tiene un programa activo.")

        if cliente.contador_visitas < programa.visitas_requeridas:
            raise PremioNoDisponible(
                f"Faltan {programa.visitas_requeridas - cliente.contador_visitas} visitas."
            )

        canje = Canje(
            negocio_id=usuario.negocio_id,
            cliente=cliente,
            programa=programa,
            local=local,
            visitas_consumidas=programa.visitas_requeridas,
            canjeado_por=usuario,
        )
        canje.full_clean()
        canje.save()

        cliente.contador_visitas = 0  # tu decisión: el contador se reinicia al canjear
        cliente.save(update_fields=["contador_visitas", "actualizado_en"])

    return canje