import json
from dataclasses import dataclass
from decimal import Decimal

import requests
from django.conf import settings


class SwahiliesError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


@dataclass(frozen=True)
class SwahiliesResponse:
    reference: str


def initiate_push(*, order_id: str, amount: Decimal, phone_number: str) -> SwahiliesResponse:
    """Trigger a Swahilies USSD push for `phone_number` with `amount`, tagged with `order_id`.

    Returns the Selcom reference the customer will see / pay to. Raises SwahiliesError
    on any non-200 outcome (HTTP error, non-200 application code, or malformed payload).
    """
    payload = {
        "api": 170,
        "code": 104,
        "data": {
            "api_key": settings.SWAHILIES_API_KEY,
            "order_id": order_id,
            "amount": int(amount),
            "is_live": settings.SWAHILIES_IS_LIVE,
            "phone_number": phone_number,
            "webhook_url": settings.SWAHILIES_WEBHOOK_URL,
        },
    }

    try:
        response = requests.post(
            settings.SWAHILIES_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
    except requests.RequestException as exc:
        raise SwahiliesError(f"network error contacting Swahilies: {exc}") from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise SwahiliesError(
            "Swahilies returned non-JSON body",
            status_code=response.status_code,
            body=response.text,
        ) from exc

    if body.get("code") != 200:
        raise SwahiliesError(
            f"Swahilies rejected request: code={body.get('code')!r}",
            status_code=response.status_code,
            body=response.text,
        )

    selcom_raw = body.get("selcom")
    try:
        # `selcom` is a JSON-encoded string per the provider's contract; parse it explicitly.
        selcom = json.loads(selcom_raw) if isinstance(selcom_raw, str) else selcom_raw
        reference = selcom["reference"]
    except (TypeError, ValueError, KeyError) as exc:
        raise SwahiliesError(
            "Swahilies response missing selcom.reference",
            status_code=response.status_code,
            body=response.text,
        ) from exc

    return SwahiliesResponse(reference=str(reference))
