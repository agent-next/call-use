"""E.164 phone-number validation for supported calling regions."""

import re

# E.164 NANP format: +1 followed by 10 digits.
_E164_NANP_RE = re.compile(r"\+1[2-9]\d{2}[2-9]\d{6}")

# South Africa: +27 followed by 9 national digits.
_ZA_RE = re.compile(r"\+27[1-8]\d{8}")

# Lesotho: +266 followed by 8 national digits.
_LS_RE = re.compile(r"\+266[5-8]\d{7}")

# Caribbean / Atlantic NPAs
_CARIBBEAN_ATLANTIC_NPAS = frozenset(
    {
        "242", "246", "264", "268", "284", "340", "345", "441", "473", "649",
        "658", "664", "721", "758", "767", "784", "787", "809", "829", "849",
        "868", "869", "876", "939",
    }
)

# Pacific NPAs
_PACIFIC_NPAS = frozenset({"670", "671", "684"})

# Non-geographic NPAs
_NON_GEOGRAPHIC_NPAS = frozenset(
    {"456", "500", "521", "522", "533", "544", "566", "577", "588", "600", "700"}
)

_DENIED_NPAS = _CARIBBEAN_ATLANTIC_NPAS | _PACIFIC_NPAS | _NON_GEOGRAPHIC_NPAS


def validate_phone_number(number: str) -> str:
    """Validate a supported E.164 destination number."""
    if not isinstance(number, str):
        raise ValueError("phone_number must be a string")

    number = number.strip()

    if _ZA_RE.fullmatch(number) or _LS_RE.fullmatch(number):
        return number

    if not _E164_NANP_RE.fullmatch(number):
        raise ValueError(
            f"Invalid phone number {number!r}: expected supported E.164 format"
        )

    area_code = number[2:5]
    exchange = number[5:8]

    if area_code in _DENIED_NPAS:
        raise ValueError(f"Denied area code {area_code}: Caribbean, Pacific, or non-geographic NPA")

    if area_code == "900" or exchange == "976" or area_code == "976":
        raise ValueError(
            f"Premium-rate number not allowed (area_code={area_code}, exchange={exchange})"
        )

    return number


def validate_caller_id(caller_id: str | None) -> str | None:
    """Validate a configured caller ID; carrier ownership must also be verified."""
    if caller_id is None:
        return None
    if not isinstance(caller_id, str):
        raise ValueError("caller_id must be a string")
    return validate_phone_number(caller_id)
