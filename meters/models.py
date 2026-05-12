import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class Meter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meters",
    )
    meter_number = models.CharField(
        max_length=14,
        unique=True,
        validators=[RegexValidator(regex=r"^\d{10,14}$", message="meter_number must be 10-14 digits")],
    )
    label = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["owner"])]

    def __str__(self):
        return self.meter_number
