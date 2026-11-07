from django.db import models

from apps.core.models import TimeStampedModel


class TagNFC(TimeStampedModel):
    """Un chip físico, asociado a un local."""

    local = models.ForeignKey(
        "businesses.Local", on_delete=models.CASCADE, related_name="tags"
    )
    uid = models.CharField(max_length=32, unique=True, help_text="UID de fábrica del chip.")
    etiqueta = models.CharField(max_length=100, blank=True, help_text="Ej: Mostrador.")
    # Referencia a la clave del chip en un gestor de secretos.
    # Nunca guardar la clave en texto plano en la base de datos.
    clave_ref = models.CharField(max_length=255, blank=True)
    # Último contador de toques validado (anti-repetición de URLs)
    ultimo_contador = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Tag {self.uid} - {self.local}"
