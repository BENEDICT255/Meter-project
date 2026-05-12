from decimal import Decimal

from rest_framework import serializers

from meters.models import Meter

from .models import Token, Transaction


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ("id", "value", "strategy", "delivered_via_sms", "delivered_at", "created_at")


class TransactionSerializer(serializers.ModelSerializer):
    token = TokenSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "meter",
            "amount",
            "control_number",
            "status",
            "provider_reference",
            "paid_at",
            "expires_at",
            "created_at",
            "token",
        )
        read_only_fields = fields


class InitiateSerializer(serializers.Serializer):
    meter_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    def validate_meter_id(self, value):
        user = self.context["request"].user
        try:
            self.context["meter"] = Meter.objects.get(id=value, owner=user)
        except Meter.DoesNotExist:
            raise serializers.ValidationError("meter not found")
        return value
