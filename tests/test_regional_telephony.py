import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from call_use.dialing_policy import can_dial_now, country_for_number
from call_use.phone import validate_caller_id, validate_phone_number


def test_south_africa_mobile_is_supported():
    assert validate_phone_number("+27821234567") == "+27821234567"
    assert country_for_number("+27821234567") == "ZA"


def test_lesotho_mobile_is_supported():
    assert validate_phone_number("+26658123456") == "+26658123456"
    assert country_for_number("+26658123456") == "LS"


def test_existing_nanp_number_remains_supported():
    assert validate_phone_number("+12025550123") == "+12025550123"


@pytest.mark.parametrize(
    "number",
    ["+12005550123", "+270821234567", "+26618123456", "0821234567"],
)
def test_unsupported_or_invalid_numbers_are_rejected(number):
    with pytest.raises(ValueError):
        validate_phone_number(number)


def test_caller_id_uses_same_regional_validation():
    assert validate_caller_id("+27821234567") == "+27821234567"
    assert validate_caller_id("+26658123456") == "+26658123456"


def test_local_call_window_uses_country_timezone():
    # 10:00 Johannesburg is within the default 08:00-20:00 window.
    now = datetime(2026, 9, 7, 10, 0, tzinfo=ZoneInfo("Africa/Johannesburg"))
    assert can_dial_now("+27821234567", now=now)
    assert can_dial_now("+26658123456", now=now)

    late = datetime(2026, 9, 7, 21, 0, tzinfo=ZoneInfo("Africa/Johannesburg"))
    assert not can_dial_now("+27821234567", now=late)
