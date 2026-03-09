"""Tests for call_use.phone validation functions."""

import pytest

from call_use.phone import validate_caller_id, validate_phone_number


class TestValidatePhoneNumber:
    def test_valid_us_number(self):
        assert validate_phone_number("+12125551234") == "+12125551234"

    def test_valid_canadian_number(self):
        assert validate_phone_number("+14165551234") == "+14165551234"

    def test_caribbean_npa_rejected(self):
        with pytest.raises(ValueError, match="Denied area code 876"):
            validate_phone_number("+18762345678")

    def test_premium_900_rejected(self):
        with pytest.raises(ValueError, match="Premium-rate"):
            validate_phone_number("+19002345678")

    def test_premium_exchange_976_rejected(self):
        with pytest.raises(ValueError, match="Premium-rate"):
            validate_phone_number("+12129761234")

    def test_missing_plus_rejected(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("12125551234")

    def test_non_nanp_rejected(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("+442012345678")

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number("")

    def test_whitespace_stripped(self):
        assert validate_phone_number(" +12125551234 ") == "+12125551234"

    def test_integer_input_rejected(self):
        with pytest.raises(ValueError, match="phone_number must be a string"):
            validate_phone_number(12125551234)  # type: ignore[arg-type]


class TestValidateCallerId:
    def test_none_returns_none(self):
        assert validate_caller_id(None) is None

    def test_valid_caller_id(self):
        assert validate_caller_id("+12125551234") == "+12125551234"

    def test_invalid_caller_id_rejected(self):
        with pytest.raises(ValueError, match="Invalid caller_id"):
            validate_caller_id("invalid")
