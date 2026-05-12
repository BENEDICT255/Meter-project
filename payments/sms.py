import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

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


def _get_provider() -> SmsProvider:
    name = settings.SMS_PROVIDER
    if name == "console":
        return ConsoleSmsProvider()
    # Task 4 will register the real provider (Beem / Twilio / AT) here.
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
