import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from django.conf import settings
from django.utils import timezone

from .models import Token


logger = logging.getLogger(__name__)


@dataclass
class SmsResult:
    ok: bool
    provider_message_id: str | None = None
    error: str | None = None


class SmsProvider(ABC):
    name: str

    @abstractmethod
    def send(self, *, to: str, message: str) -> SmsResult:
        ...


class ConsoleSmsProvider(SmsProvider):
    name = "console"

    def send(self, *, to: str, message: str) -> SmsResult:
        logger.info("SMS to %s: %s", to, message)
        return SmsResult(ok=True, provider_message_id=f"console-{to}")


def _normalize_msisdn(phone: str) -> str:
    """Tanzanian convention: MalipoPay expects 255XXXXXXXXX (no +)."""
    p = phone.strip()
    if p.startswith("+"):
        p = p[1:]
    if p.startswith("0"):
        p = "255" + p[1:]
    return p


class MalipoPaySmsProvider(SmsProvider):
    name = "malipopay"

    MAX_ATTEMPTS = 3
    BACKOFF_SECONDS = (0.5, 1.0, 2.0)

    def __init__(self, *, api_url: str, api_token: str, sender: str, operator_id: str):
        if not api_token:
            raise ValueError("MalipoPaySmsProvider requires a non-empty api_token")
        if not operator_id:
            raise ValueError("MalipoPaySmsProvider requires a non-empty operator_id")
        self.api_url = api_url
        self.api_token = api_token
        self.sender = sender
        self.operator_id = operator_id

    def send(self, *, to: str, message: str) -> SmsResult:
        msisdn = _normalize_msisdn(to)
        # MalipoPay's snippet sends both camelCase and snake_case keys; mirror exactly.
        payload = {
            "sender": self.sender,
            "phoneNumber": msisdn,
            "phone_number": msisdn,
            "message": message,
            "operator_id": self.operator_id,
        }
        headers = {"apiToken": self.api_token, "Content-Type": "application/json"}

        last_error: str | None = None
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                response = requests.post(
                    self.api_url, json=payload, headers=headers, timeout=10
                )
            except requests.RequestException as exc:
                last_error = f"network error: {exc}"
            else:
                if 200 <= response.status_code < 300:
                    return SmsResult(ok=True, provider_message_id=msisdn)
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"

            if attempt < self.MAX_ATTEMPTS - 1:
                time.sleep(self.BACKOFF_SECONDS[attempt])

        return SmsResult(ok=False, error=last_error)


def _get_provider() -> SmsProvider:
    name = settings.SMS_PROVIDER
    if name == "console":
        return ConsoleSmsProvider()
    if name == "malipopay":
        return MalipoPaySmsProvider(
            api_url=settings.MALIPOPAY_API_URL,
            api_token=settings.MALIPOPAY_API_TOKEN,
            sender=settings.MALIPOPAY_SENDER,
            operator_id=settings.MALIPOPAY_OPERATOR_ID,
        )
    raise ValueError(f"unknown SMS_PROVIDER: {name!r}")


def _compose_message(token: Token) -> str:
    txn = token.transaction
    return (
        f"Daraja Water: your token for meter {txn.meter.meter_number} "
        f"(amount {txn.amount}) is {token.value}."
    )


def send_token_sms(token: Token) -> None:
    """Best-effort SMS dispatch. Marks the token delivered on success.

    Failures are logged but never raised — the caller (webhook) must not
    roll back the paid Transaction just because SMS flaked.
    """
    try:
        provider = _get_provider()
        result = provider.send(
            to=token.transaction.user.phone_number,
            message=_compose_message(token),
        )
    except Exception:  # noqa: BLE001 — best-effort
        logger.exception("SMS provider raised; not marking delivered")
        return

    if result.ok:
        token.delivered_via_sms = True
        token.delivered_at = timezone.now()
        token.save(update_fields=["delivered_via_sms", "delivered_at"])
    else:
        logger.warning("SMS send failed: %s", result.error)
