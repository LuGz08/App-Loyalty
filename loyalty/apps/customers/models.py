import uuid

from django.db import models

from apps.core.models import TimeStampedModel


class Cliente(TimeStampedModel):
    """
    Cliente final, perteneciente a UN negocio.
    El mismo email en dos negocios son dos registros distintos: el
    consentimiento de publicidad se da a ese negocio, no a la plataforma.
    """

    negocio = models.ForeignKey(
        "businesses.Negocio", on_delete=models.CASCADE, related_name="clientes"
    )
    email = models.EmailField()
    fecha_nacimiento = models.DateField()
    email_verificado = models.BooleanField(default=False)

    # Consentimiento de marketing
    acepta_marketing = models.BooleanField(default=False)
    fecha_consentimiento = models.DateTimeField(null=True, blank=True)
    fecha_baja_marketing = models.DateTimeField(null=True, blank=True)
    # Token para el enlace de "darse de baja" en cada correo
    token_baja = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # El contador se reinicia al canjear; visitas_totales nunca se reinicia
    contador_visitas = models.PositiveIntegerField(default=0)
    visitas_totales = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "email"], name="email_unico_por_negocio"
            ),
        ]
        indexes = [
            models.Index(fields=["negocio", "fecha_nacimiento"]),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.negocio})"
