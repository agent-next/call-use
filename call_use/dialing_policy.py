"""Regional dialing policy for NahaLabs deployments."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

@dataclass(frozen=True)
class CountryPolicy:
    iso2: str
    calling_code: str
    timezone: str

COUNTRY_POLICIES = {
    "ZA": CountryPolicy("ZA", "+27", "Africa/Johannesburg"),
    "LS": CountryPolicy("LS", "+266", "Africa/Maseru"),
}

def country_for_number(number: str) -> str:
    for iso2, policy in COUNTRY_POLICIES.items():
        if number.startswith(policy.calling_code):
            return iso2
    raise ValueError(f"Unsupported destination country for {number!r}")

def can_dial_now(number: str, *, now: datetime | None = None, start_hour: int = 8, end_hour: int = 20) -> bool:
    """Apply configurable local-time contact hours; defaults are operational policy."""
    iso2 = country_for_number(number)
    local_now = (now or datetime.now(tz=ZoneInfo("UTC"))).astimezone(ZoneInfo(COUNTRY_POLICIES[iso2].timezone))
    return start_hour <= local_now.hour < end_hour
