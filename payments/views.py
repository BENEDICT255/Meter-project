import json
from datetime import timedelta

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .control_numbers import generate_control_number
from .models import Token, Transaction
from .serializers import InitiateSerializer, TokenSerializer, TransactionSerializer
from .signing import verify_hmac
from .sms import send_token_sms
from .token_logic import get_strategy


class InitiatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitiateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        meter = serializer.context["meter"]
        amount = serializer.validated_data["amount"]

        existing = set(Transaction.objects.values_list("control_number", flat=True))
        control_number = generate_control_number(existing=existing)

        txn = Transaction.objects.create(
            user=request.user,
            meter=meter,
            amount=amount,
            control_number=control_number,
            expires_at=timezone.now() + timedelta(minutes=settings.TRANSACTION_TTL_MINUTES),
        )
        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class PaymentWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body
        signature = request.headers.get("X-Signature", "")
        secret = settings.WEBHOOK_HMAC_SECRET.encode()
        if not verify_hmac(body, signature, secret):
            return Response(
                {"detail": "invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            return Response({"detail": "invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        control_number = payload.get("control_number")
        if not control_number:
            return Response(
                {"detail": "control_number required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = None
        with db_transaction.atomic():
            try:
                txn = Transaction.objects.select_for_update().get(control_number=control_number)
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

            provider_status = payload.get("status")

            if provider_status == "paid":
                txn.status = Transaction.Status.PAID
                txn.paid_at = timezone.now()
                txn.provider_reference = payload.get("provider_reference", "")
                txn.save(update_fields=["status", "paid_at", "provider_reference", "updated_at"])

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
            else:
                txn.status = Transaction.Status.FAILED
                txn.save(update_fields=["status", "updated_at"])
                return Response(
                    {"transaction": TransactionSerializer(txn).data, "token": None},
                    status=status.HTTP_200_OK,
                )

        # SMS dispatch outside the DB transaction; failures must not roll back.
        send_token_sms(token)

        return Response(
            {
                "transaction": TransactionSerializer(txn).data,
                "token": TokenSerializer(token).data,
            },
            status=status.HTTP_200_OK,
        )
