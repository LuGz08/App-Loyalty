from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class ProgramaFidelizacion(TimeStampedModel):
    """Reglas de fidelización de un negocio. Nada de esto va fijo en el código."""

    negocio = models.ForeignKey(
        "businesses.Negocio", on_delete=models.CASCADE, related_name="programas"
    )
    nombre = models.CharField(max_length=150, default="Programa principal")
    visitas_requeridas = models.PositiveSmallIntegerField(default=10)
    descripcion_premio = models.CharField(max_length=255, help_text="Ej: Un café gratis.")
    # Anti-abuso: minutos mínimos entre dos visitas del mismo cliente (0 = sin límite)
    minutos_entre_visitas = models.PositiveIntegerField(default=60)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["negocio"],
                condition=models.Q(activo=True),
                name="un_programa_activo_por_negocio",
            ),
        ]

    def __str__(self):
        return f"{self.negocio}: {self.visitas_requeridas} visitas -> {self.descripcion_premio}"


class Visita(TimeStampedModel):
    """Un toque válido. Historial inmutable: no se edita ni se borra."""

    # Redundante a propósito: simplifica y asegura el filtrado por tenant
    negocio = models.ForeignKey(
        "businesses.Negocio", on_delete=models.CASCADE, related_name="visitas"
    )
    local = models.ForeignKey(
        "businesses.Local", on_delete=models.PROTECT, related_name="visitas"
    )
    cliente = models.ForeignKey(
        "customers.Cliente", on_delete=models.CASCADE, related_name="visitas"
    )
    tag = models.ForeignKey(
        "nfc.TagNFC", on_delete=models.SET_NULL, null=True, blank=True, related_name="visitas"
    )

    class Meta:
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["cliente", "-creado_en"]),
            models.Index(fields=["negocio", "-creado_en"]),
        ]

    def clean(self):
        if self.local_id and self.cliente_id:
            if self.local.negocio_id != self.cliente.negocio_id:
                raise ValidationError("El cliente y el local pertenecen a negocios distintos.")

    def save(self, *args, **kwargs):
        if self.local_id and not self.negocio_id:
            self.negocio_id = self.local.negocio_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Visita de {self.cliente} en {self.local} ({self.creado_en:%Y-%m-%d %H:%M})"


class Canje(TimeStampedModel):
    """Registro de que un cliente cobró su premio."""

    negocio = models.ForeignKey(
        "businesses.Negocio", on_delete=models.CASCADE, related_name="canjes"
    )
    cliente = models.ForeignKey(
        "customers.Cliente", on_delete=models.CASCADE, related_name="canjes"
    )
    programa = models.ForeignKey(
        ProgramaFidelizacion, on_delete=models.PROTECT, related_name="canjes"
    )
    local = models.ForeignKey(
        "businesses.Local", on_delete=models.PROTECT, related_name="canjes"
    )
    visitas_consumidas = models.PositiveSmallIntegerField(
        help_text="Meta vigente al momento del canje (queda como registro histórico)."
    )
    canjeado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="canjes_realizados",
    )

    class Meta:
        ordering = ["-creado_en"]

    def clean(self):
        # El ajuste nuevo: misma coherencia entre negocios que ya tiene Visita
        if self.cliente_id and self.local_id and self.programa_id:
            negocios = {
                self.cliente.negocio_id,
                self.local.negocio_id,
                self.programa.negocio_id,
            }
            if len(negocios) > 1:
                raise ValidationError("Cliente, local y programa deben ser del mismo negocio.")

    def save(self, *args, **kwargs):
        if self.local_id and not self.negocio_id:
            self.negocio_id = self.local.negocio_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Canje de {self.cliente} ({self.creado_en:%Y-%m-%d})"