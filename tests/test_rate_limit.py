"""Tests for call_use.rate_limit."""

import time
from unittest.mock import patch

import pytest

from call_use.rate_limit import RateLimiter

pytestmark = pytest.mark.unit


class TestRateLimiter:
    def test_under_limit_allows(self):
        rl = RateLimiter(max_calls=10, window_seconds=3600)
        for i in range(5):
            assert rl.check("key1") is True

    def test_at_limit_rejects(self):
        rl = RateLimiter(max_calls=3, window_seconds=3600)
        assert rl.check("key1") is True
        assert rl.check("key1") is True
        assert rl.check("key1") is True
        assert rl.check("key1") is False  # 4th call rejected

    def test_after_window_expiry_allows(self):
        rl = RateLimiter(max_calls=2, window_seconds=10)
        assert rl.check("key1") is True
        assert rl.check("key1") is True
        assert rl.check("key1") is False
        # Fast-forward past window
        with patch("call_use.rate_limit.time") as mock_time:
            mock_time.time.return_value = time.time() + 11
            assert rl.check("key1") is True

    def test_different_keys_independent(self):
        rl = RateLimiter(max_calls=1, window_seconds=3600)
        assert rl.check("key1") is True
        assert rl.check("key1") is False
        assert rl.check("key2") is True  # Different key, independent
        assert rl.check("key2") is False

    def test_window_edge(self):
        rl = RateLimiter(max_calls=1, window_seconds=10)
        base = time.time()
        with patch("call_use.rate_limit.time") as mock_time:
            mock_time.time.return_value = base
            assert rl.check("key1") is True
            assert rl.check("key1") is False
            # At exactly base+10, cutoff=base, call at base has t > cutoff false
            # so it falls off, slot is free
            mock_time.time.return_value = base + 10
            assert rl.check("key1") is True  # Old call expired
            # Fill slot again
            assert rl.check("key1") is False
            # Just past window
            mock_time.time.return_value = base + 20.01
            assert rl.check("key1") is True
