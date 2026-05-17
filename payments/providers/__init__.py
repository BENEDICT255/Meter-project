from django.conf import settings

from .swahilies import SwahiliesError, SwahiliesResponse
from .swahilies import initiate_push as _swahilies_initiate


def initiate_push(*, order_id: str, amount, phone_number: str) -> SwahiliesResponse:
    """Dispatch to the configured payment provider.

    PAYMENT_PROVIDER=fake bypasses the real Swahilies API and returns a
    deterministic Selcom-shaped reference. Intended for e2e tests and
    manual UI exploration without a working Swahilies key.
    """
    if getattr(settings, "PAYMENT_PROVIDER", "swahilies") == "fake":
        return SwahiliesResponse(reference=f"FAKE-{order_id[:16]}")
    return _swahilies_initiate(
        order_id=order_id, amount=amount, phone_number=phone_number
    )


__all__ = ["SwahiliesError", "SwahiliesResponse", "initiate_push"]
