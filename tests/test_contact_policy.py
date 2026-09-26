import pytest

from call_use.contact_policy import (
    ContactAuthorization,
    ContactPolicyError,
    authorize_outbound_call,
)


def test_authorized_za_call_passes_when_dnc_checked():
    authorization = ContactAuthorization(lawful_contact=True, dnc_checked=True)
    assert authorize_outbound_call(
        "+27821234567", authorization, enforce_contact_hours=False
    ) == "ZA"


def test_unauthorized_call_is_blocked():
    authorization = ContactAuthorization(lawful_contact=False, dnc_checked=True)
    with pytest.raises(ContactPolicyError, match="lawful-contact"):
        authorize_outbound_call(
            "+27821234567", authorization, enforce_contact_hours=False
        )


def test_unchecked_dnc_is_blocked():
    authorization = ContactAuthorization(lawful_contact=True, dnc_checked=False)
    with pytest.raises(ContactPolicyError, match="DNC"):
        authorize_outbound_call(
            "+27821234567", authorization, enforce_contact_hours=False
        )


def test_opted_out_recipient_is_blocked():
    authorization = ContactAuthorization(
        lawful_contact=True, dnc_checked=True, opted_out=True
    )
    with pytest.raises(ContactPolicyError, match="opt-out"):
        authorize_outbound_call(
            "+26658123456", authorization, enforce_contact_hours=False
        )
