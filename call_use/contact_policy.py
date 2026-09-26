"""Outbound contact authorization and regional calling policy.

This module provides a small, provider-independent safety gate for automated
outbound calls. It is intentionally policy-oriented: legal requirements vary
by jurisdiction and deployment, so callers must supply an explicit lawful-
contact authorization and DNC/opt-out result before origination.
"""

from __future__ import annotations

from dataclasses import dataclass

from call_use.dialing_policy import can_dial_now, country_for_number


@dataclass(frozen=True)
class ContactAuthorization:
    """Evidence supplied by the calling application before dialing."""

    lawful_contact: bool
    dnc_checked: bool
    opted_out: bool = False


class ContactPolicyError(ValueError):
    """Raised when an outbound call fails the contact policy gate."""


def authorize_outbound_call(
    number: str,
    authorization: ContactAuthorization,
    *,
    enforce_contact_hours: bool = True,
) -> str:
    """Validate authorization, suppression state, and local contact hours.

    Returns the ISO country code when the call is permitted.
    """
    country = country_for_number(number)

    if not authorization.lawful_contact:
        raise ContactPolicyError("Outbound call requires lawful-contact authorization")
    if not authorization.dnc_checked:
        raise ContactPolicyError("Outbound call requires a completed DNC/opt-out check")
    if authorization.opted_out:
        raise ContactPolicyError("Recipient is suppressed by opt-out/DNC policy")
    if enforce_contact_hours and not can_dial_now(number):
        raise ContactPolicyError("Outside configured local contact hours")

    return country
