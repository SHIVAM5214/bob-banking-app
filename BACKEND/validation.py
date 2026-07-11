"""
validation.py — Shared Input Validation Helpers
================================================
All deposit / withdrawal amount checks live here so that:
  1. View functions stay concise.
  2. The same rules are reused by unit tests without importing Flask.

Each function returns (is_valid: bool, error_message: str | None).
"""

from decimal import Decimal, InvalidOperation


def _parse_amount(raw: str):
    """Try to parse *raw* as a Decimal.  Returns (Decimal, None) on success
    or (None, error_message) on failure."""
    if not raw or not raw.strip():
        return None, "Please enter an amount."
    try:
        value = Decimal(raw.strip())
    except InvalidOperation:
        return None, "Amount must be a valid number."
    return value, None


def _check_positive(value: Decimal):
    """Return an error string if *value* is not strictly positive, else None."""
    if value <= 0:
        return "Amount must be greater than zero."
    return None


def _check_decimal_places(value: Decimal):
    """Return an error string if *value* has more than 2 decimal places."""
    # sign, digits, exponent — a negative exponent means decimal places
    sign, digits, exponent = value.as_tuple()
    if exponent < -2:
        return "Amount cannot have more than two decimal places."
    return None


def validate_deposit(raw_amount: str):
    """Validate a deposit request.

    Parameters
    ----------
    raw_amount : str
        The raw string value from the HTML form field.

    Returns
    -------
    (float, None)         on success  — caller should use the returned float
    (None, error_message) on failure
    """
    value, err = _parse_amount(raw_amount)
    if err:
        return None, err

    err = _check_positive(value)
    if err:
        return None, "Deposit " + err.lower()

    err = _check_decimal_places(value)
    if err:
        return None, err

    return float(value), None


def validate_withdrawal(raw_amount: str, current_balance: float):
    """Validate a withdrawal request.

    Parameters
    ----------
    raw_amount      : str   — raw string from the form field
    current_balance : float — authoritative balance read from the database

    Returns
    -------
    (float, None)         on success
    (None, error_message) on failure
    """
    value, err = _parse_amount(raw_amount)
    if err:
        return None, err

    err = _check_positive(value)
    if err:
        return None, "Withdrawal " + err.lower()

    err = _check_decimal_places(value)
    if err:
        return None, err

    if float(value) > current_balance:
        return None, "Insufficient funds."

    return float(value), None
