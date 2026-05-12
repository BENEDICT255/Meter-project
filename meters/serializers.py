from rest_framework import serializers

from .models import Meter


class MeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meter
        fields = ("id", "meter_number", "label", "created_at")
        read_only_fields = ("id", "created_at")
