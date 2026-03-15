"""Property-based tests using Hypothesis.

Covers:
- Phone number validation with fuzzed E.164 inputs
- Rate limiter with random request patterns
"""

import time
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from call_use.phone import validate_phone_number
from call_use.rate_limit import RateLimiter

# ---------------------------------------------------------------------------
# Phone number validation — property-based tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPhoneNumberProperties:
    @given(st.text(min_size=0, max_size=20))
    @settings(max_examples=200)
    def test_arbitrary_text_never_crashes(self, text):
        """validate_phone_number never crashes — it either returns or raises ValueError."""
        try:
            result = validate_phone_number(text)
            # If it returns, it must be a valid E.164 NANP string
            assert result.startswith("+1")
            assert len(result) == 12
        except ValueError:
            pass  # Expected for invalid inputs

    @given(
        area_code=st.sampled_from([str(x) for x in range(200, 1000) if str(x)[0] in "23456789"]),
        exchange=st.sampled_from([str(x) for x in range(200, 1000) if str(x)[0] in "23456789"]),
        subscriber=st.from_regex(r"[0-9]{4}", fullmatch=True),
    )
    @settings(max_examples=200)
    def test_valid_format_accepted_or_rejected_with_reason(self, area_code, exchange, subscriber):
        """Any well-formed +1NXXNXXXXXX either passes or raises with a clear reason."""
        number = f"+1{area_code}{exchange}{subscriber}"
        try:
            result = validate_phone_number(number)
            assert result == number
        except ValueError as e:
            msg = str(e)
            # Must explain WHY it was rejected
            assert any(
                reason in msg for reason in ["Denied area code", "Premium-rate", "Invalid phone"]
            )

    @given(st.integers())
    @settings(max_examples=50)
    def test_non_string_always_raises_type_error(self, value):
        """Non-string inputs always raise ValueError with 'must be a string'."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_phone_number(value)  # type: ignore[arg-type]

    @given(
        prefix=st.sampled_from(["+2", "+3", "+4", "+5", "+6", "+7", "+8", "+9"]),
        digits=st.from_regex(r"[0-9]{10}", fullmatch=True),
    )
    @settings(max_examples=100)
    def test_non_nanp_country_codes_rejected(self, prefix, digits):
        """Phone numbers with non-+1 country codes are always rejected."""
        with pytest.raises(ValueError, match="Invalid phone number"):
            validate_phone_number(f"{prefix}{digits}")


# ---------------------------------------------------------------------------
# Rate limiter — property-based tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRateLimiterProperties:
    @given(
        max_calls=st.integers(min_value=1, max_value=50),
        num_requests=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_never_allows_more_than_max_calls(self, max_calls, num_requests):
        """Rate limiter never allows more than max_calls in a window."""
        rl = RateLimiter(max_calls=max_calls, window_seconds=3600)
        allowed = sum(1 for _ in range(num_requests) if rl.check("test-key"))
        assert allowed <= max_calls

    @given(
        max_calls=st.integers(min_value=1, max_value=20),
        num_keys=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50)
    def test_different_keys_get_independent_limits(self, max_calls, num_keys):
        """Each API key gets its own independent rate limit."""
        rl = RateLimiter(max_calls=max_calls, window_seconds=3600)

        for key_idx in range(num_keys):
            key = f"key-{key_idx}"
            allowed = sum(1 for _ in range(max_calls + 5) if rl.check(key))
            assert allowed == max_calls

    @given(max_calls=st.integers(min_value=1, max_value=10))
    @settings(max_examples=30)
    def test_window_expiry_resets_count(self, max_calls):
        """After window expires, rate limiter allows requests again."""
        rl = RateLimiter(max_calls=max_calls, window_seconds=10)

        # Fill up the limit
        for _ in range(max_calls):
            assert rl.check("key") is True
        assert rl.check("key") is False

        # Advance time past window
        with patch("call_use.rate_limit.time") as mock_time:
            mock_time.time.return_value = time.time() + 11
            assert rl.check("key") is True
