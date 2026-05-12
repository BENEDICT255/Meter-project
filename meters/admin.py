from django.contrib import admin

from .models import Meter


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ("meter_number", "owner", "label", "created_at")
    search_fields = ("meter_number", "owner__phone_number")
    list_filter = ("created_at",)
