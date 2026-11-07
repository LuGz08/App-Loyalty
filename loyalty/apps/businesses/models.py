from django.db import models

from apps.core.models import TimeStampedModel


class Negocio(TimeStampedModel):
    """El tenant: cada empresa que paga por la plataforma."""

    class Plan(models.TextChoices):
        PILOTO = "piloto", "Piloto"
        BASICO = "basico", "Básico"
        PRO = "pro", "Pro"

    nombre = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, help_text="Identificador único en URLs.")
    email_contacto = models.EmailField()
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.PILOTO)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "negocios"

    def __str__(self):
        return self.nombre


class Local(TimeStampedModel):
    """Una sucursal física de un negocio."""

    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name="locales")
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255, blank=True)
    zona_horaria = models.CharField(max_length=64, default="America/Santiago")
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["negocio", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"], name="local_nombre_unico_por_negocio"
            ),
        ]

    def __str__(self):
        return f"{self.negocio} - {self.nombre}"