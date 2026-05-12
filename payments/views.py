from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .control_numbers import generate_control_number
from .models import Transaction
from .serializers import InitiateSerializer, TransactionSerializer


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
