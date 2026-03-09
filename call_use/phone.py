"""Phone number validation for NANP E.164 numbers."""

import re

# E.164 NANP format: +1 followed by 10 digits
# NPA (area code) starts with 2-9, exchange also starts with 2-9
_E164_NANP_RE = re.compile(r"\+1[2-9]\d{2}[2-9]\d{6}")

# Caribbean / Atlantic NPAs
_CARIBBEAN_ATLANTIC_NPAS = frozenset({
    "242", "246", "264", "268", "284", "340", "345", "441", "473",
    "649", "658", "664", "721", "758", "767", "784", "787", "809",
    "829", "849", "868", "869", "876", "939",
})

# Pacific NPAs
_PACIFIC_NPAS = frozenset({"670", "671", "684"})

# Non-geographic NPAs
_NON_GEOGRAPHIC_NPAS = frozenset({
    "456", "500", "521", "522", "533", "544", "566", "577", "588", "600", "700",
})

_DENIED_NPAS = _CARIBBEAN_ATLANTIC_NPAS | _PACIFIC_NPAS | _NON_GEOGRAPHIC_NPAS


def validate_phone_number(number: str) -> str:
    """Validate and clean a phone number in E.164 NANP format.

    Args:
        number: Phone number string, expected in +1XXXXXXXXXX format.

    Returns:
        The cleaned phone number string.

    Raises:
        ValueError: If the number is invalid, on a denied NPA list, or premium.
    """
    if not isinstance(number, str):
        raise ValueError("phone_number must be a string")

    number = number.strip()

    if not _E164_NANP_RE.fullmatch(number):
        raise ValueError(
            f"Invalid phone number {number!r}: must be E.164 NANP format (+1XXXXXXXXXX)"
        )

    area_code = number[2:5]
    exchange = number[5:8]

    if area_code in _DENIED_NPAS:
        raise ValueError(
            f"Denied area code {area_code}: Caribbean, Pacific, or non-geographic NPA"
        )

    if area_code == "900" or exchange == "976" or area_code == "976":
        raise ValueError(
            f"Premium-rate number not allowed (area_code={area_code}, exchange={exchange})"
        )

    return number


def validate_caller_id(caller_id: str | None) -> str | None:
    """Validate a caller ID in E.164 NANP format, or pass through None.

    Args:
        caller_id: Caller ID string or None.

    Returns:
        Cleaned caller ID string, or None if input was None.

    Raises:
        ValueError: If the caller_id is provided but invalid.
    """
    # TODO v2: Verify caller_id ownership via Twilio Lookup API
    if caller_id is None:
        return None

    if not isinstance(caller_id, str):
        raise ValueError("caller_id must be a string")

    caller_id = caller_id.strip()

    if not _E164_NANP_RE.fullmatch(caller_id):
        raise ValueError(
            f"Invalid caller_id {caller_id!r}: must be E.164 NANP format (+1XXXXXXXXXX)"
        )

    return caller_id
