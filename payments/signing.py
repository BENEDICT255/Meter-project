import hashlib
import hmac


PREFIX = "sha256="


def compute_hmac(body: bytes, secret: bytes) -> str:
    digest = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return PREFIX + digest


def verify_hmac(body: bytes, header: str, secret: bytes) -> bool:
    """Return True iff `header` is a valid sha256 HMAC of `body` under `secret`.

    Header format: 'sha256=<hex>'. Comparison is constant-time.
    """
    if not header or not header.startswith(PREFIX):
        return False
    expected = compute_hmac(body, secret)
    return hmac.compare_digest(expected, header)
