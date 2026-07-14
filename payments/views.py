import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Token, Transaction
from .providers import SwahiliesError, initiate_push
from .serializers import InitiateSerializer, TokenSerializer, TransactionSerializer
from .sms import send_token_sms
from .token_logic import get_strategy


class InitiatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "initiate"

    def post(self, request):
        serializer = InitiateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        meter = serializer.context["meter"]
        amount = serializer.validated_data["amount"]
        phone_number = serializer.validated_data["phone_number"]

        order_id = uuid.uuid4().hex
        txn = Transaction.objects.create(
            user=request.user,
            meter=meter,
            amount=amount,
            provider_reference=order_id,
            expires_at=timezone.now() + timedelta(minutes=settings.TRANSACTION_TTL_MINUTES),
        )

        # --- TEMPORARY TEST HACK: Generate token immediately for UI testing ---
        from .models import Token
        from .token_logic import get_strategy
        strategy = get_strategy()
        Token.objects.create(
            transaction=txn,
            value=strategy.generate(
                amount=txn.amount,
                meter_number=txn.meter.meter_number,
                nonce=str(txn.id),
            ),
            strategy=strategy.name,
        )
        # --- END TEMPORARY TEST HACK ---

        try:
            result = initiate_push(
                order_id=order_id,
                amount=amount,
                phone_number=phone_number,
            )

            print(result)
        except SwahiliesError as exc:
            txn.status = Transaction.Status.FAILED
            txn.save(update_fields=["status", "updated_at"])
            return Response(
                {"detail": "payment provider unavailable", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        txn.control_number = result.reference
        txn.save(update_fields=["control_number", "updated_at"])

        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class PaymentWebhookView(APIView):
    # Swahilies does not sign webhooks; we accept any POST. The order_id we sent
    # at initiation is echoed back in transaction_details.order_id and is the lookup key.
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            payload = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return Response({"detail": "invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        details = payload.get("transaction_details") or {}
        order_id = details.get("order_id")
        if not order_id:
            return Response(
                {"detail": "transaction_details.order_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = None
        with db_transaction.atomic():
            try:
                txn = Transaction.objects.select_for_update().get(provider_reference=order_id)
            except Transaction.DoesNotExist:
                return Response(
                    {"detail": "transaction not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if txn.status == Transaction.Status.PAID:
                return Response(
                    {
                        "transaction": TransactionSerializer(txn).data,
                        "token": TokenSerializer(txn.token).data,
                    },
                    status=status.HTTP_200_OK,
                )

            txn.status = Transaction.Status.PAID
            txn.paid_at = timezone.now()
            txn.save(update_fields=["status", "paid_at", "updated_at"])

            strategy = get_strategy()
            value = strategy.generate(
                amount=txn.amount,
                meter_number=txn.meter.meter_number,
                nonce=str(txn.id),
            )
            token = Token.objects.create(
                transaction=txn,
                value=value,
                strategy=strategy.name,
            )

        send_token_sms(token)

        return Response(
            {
                "transaction": TransactionSerializer(txn).data,
                "token": TokenSerializer(token).data,
            },
            status=status.HTTP_200_OK,
        )


class TransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return (
            Transaction.objects.filter(user=self.request.user)
            .select_related("meter", "token")
            .order_by("-created_at")
        )
