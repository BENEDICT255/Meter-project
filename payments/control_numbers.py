import secrets


class ControlNumberCollisionError(RuntimeError):
    pass


def _random_suffix() -> str:
    # 10 random digits
    return "".join(str(secrets.randbelow(10)) for _ in range(10))


def generate_control_number(*, existing: set[str], max_attempts: int = 10) -> str:
    """Return a 12-digit string starting with '99' that is not in `existing`.

    Raises ControlNumberCollisionError if no unique value is found in max_attempts tries.
    The caller is responsible for passing the current set of in-use control numbers
    (typically by querying the Transaction table).
    """
    for _ in range(max_attempts):
        candidate = "99" + _random_suffix()
        if candidate not in existing:
            return candidate
    raise ControlNumberCollisionError(
        f"could not generate unique control number after {max_attempts} attempts"
    )
