"""
test_validation.py — Unit tests for validation.py
===================================================
Tests every boundary condition described in the implementation guide,
Section 5 (Validation Rules).  No Flask context or database required.
"""

import pytest

from validation import validate_deposit, validate_withdrawal


# --------------------------------------------------------------------------- #
# validate_deposit                                                              #
# --------------------------------------------------------------------------- #

class TestValidateDeposit:
    def test_valid_integer_amount(self):
        amount, err = validate_deposit("100")
        assert err is None
        assert amount == pytest.approx(100.0)

    def test_valid_decimal_amount(self):
        amount, err = validate_deposit("49.99")
        assert err is None
        assert amount == pytest.approx(49.99)

    def test_empty_string_fails(self):
        amount, err = validate_deposit("")
        assert amount is None
        assert "enter an amount" in err.lower()

    def test_whitespace_only_fails(self):
        amount, err = validate_deposit("   ")
        assert amount is None
        assert err is not None

    def test_non_numeric_fails(self):
        amount, err = validate_deposit("abc")
        assert amount is None
        assert "number" in err.lower()

    def test_zero_fails(self):
        amount, err = validate_deposit("0")
        assert amount is None
        assert "greater than zero" in err.lower()

    def test_negative_fails(self):
        amount, err = validate_deposit("-10")
        assert amount is None
        assert err is not None

    def test_three_decimal_places_fails(self):
        amount, err = validate_deposit("1.001")
        assert amount is None
        assert "decimal places" in err.lower()

    def test_two_decimal_places_passes(self):
        amount, err = validate_deposit("1.01")
        assert err is None
        assert amount == pytest.approx(1.01)


# --------------------------------------------------------------------------- #
# validate_withdrawal                                                           #
# --------------------------------------------------------------------------- #

class TestValidateWithdrawal:
    BALANCE = 500.00

    def test_valid_withdrawal(self):
        amount, err = validate_withdrawal("100", self.BALANCE)
        assert err is None
        assert amount == pytest.approx(100.0)

    def test_exact_balance_passes(self):
        amount, err = validate_withdrawal("500", self.BALANCE)
        assert err is None
        assert amount == pytest.approx(500.0)

    def test_exceeds_balance_fails(self):
        amount, err = validate_withdrawal("500.01", self.BALANCE)
        assert amount is None
        assert "insufficient funds" in err.lower()

    def test_empty_fails(self):
        amount, err = validate_withdrawal("", self.BALANCE)
        assert amount is None
        assert err is not None

    def test_zero_fails(self):
        amount, err = validate_withdrawal("0", self.BALANCE)
        assert amount is None
        assert "greater than zero" in err.lower()

    def test_negative_fails(self):
        amount, err = validate_withdrawal("-50", self.BALANCE)
        assert amount is None
        assert err is not None

    def test_non_numeric_fails(self):
        amount, err = validate_withdrawal("fifty", self.BALANCE)
        assert amount is None
        assert "number" in err.lower()

    def test_three_decimal_places_fails(self):
        amount, err = validate_withdrawal("10.001", self.BALANCE)
        assert amount is None
        assert "decimal places" in err.lower()
