from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    negocio = models.ForeignKey(
        "businesses.Negocio",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="managers",
    )

    @property
    def es_encargado(self):
        return self.negocio_id is not None and not self.is_superuser