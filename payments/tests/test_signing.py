import hashlib
import hmac as stdlib_hmac

from payments.signing import compute_hmac, verify_hmac


SECRET = b"super-secret-test-key"
BODY = b'{"control_number":"990000000001","amount":"5000","status":"paid"}'


def _expected_header(body, secret):
    return "sha256=" + stdlib_hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_compute_hmac_format():
    h = compute_hmac(BODY, SECRET)
    assert h.startswith("sha256=")
    assert len(h) == len("sha256=") + 64  # 32 bytes hex


def test_verify_correct_signature():
    header = _expected_header(BODY, SECRET)
    assert verify_hmac(BODY, header, SECRET) is True


def test_verify_wrong_signature():
    assert verify_hmac(BODY, "sha256=" + "0" * 64, SECRET) is False


def test_verify_rejects_missing_prefix():
    naked = stdlib_hmac.new(SECRET, BODY, hashlib.sha256).hexdigest()
    assert verify_hmac(BODY, naked, SECRET) is False


def test_verify_rejects_empty_header():
    assert verify_hmac(BODY, "", SECRET) is False


def test_verify_rejects_wrong_algorithm():
    assert verify_hmac(BODY, "sha1=" + "a" * 40, SECRET) is False
