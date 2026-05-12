import re

from payments.control_numbers import generate_control_number


def test_format_is_12_digits_with_99_prefix():
    cn = generate_control_number(existing=set())
    assert re.fullmatch(r"99\d{10}", cn), cn


def test_avoids_collisions():
    existing = {"99" + "0" * 10}
    cn = generate_control_number(existing=existing)
    assert cn not in existing
    assert re.fullmatch(r"99\d{10}", cn)


def test_raises_when_space_exhausted(monkeypatch):
    import payments.control_numbers as cn_mod

    # Force the candidate generator to always return the same value
    monkeypatch.setattr(cn_mod, "_random_suffix", lambda: "0000000000")

    existing = {"990000000000"}
    try:
        cn_mod.generate_control_number(existing=existing, max_attempts=5)
    except cn_mod.ControlNumberCollisionError:
        return
    raise AssertionError("expected ControlNumberCollisionError")
