"""Tests for ios_backup_core.timestamps."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ios_backup_core.timestamps import (
    apple_to_iso,
    iso_to_apple,
    detect_timestamp_format,
    NANOSECOND_THRESHOLD,
)


class TestAppleToIso:
    def test_known_seconds(self):
        # 694224000 seconds after 2001-01-01 = 2023-01-01T00:00:00+00:00
        # Verified: 694224000 + 978307200 (Apple epoch offset) = 1672531200 = 2023-01-01 UTC
        result = apple_to_iso(694224000)
        assert result == "2023-01-01T00:00:00+00:00"

    def test_nanoseconds_auto_detected(self):
        # Same timestamp but in nanoseconds — value > NANOSECOND_THRESHOLD
        ns_value = 694224000 * 1_000_000_000
        assert ns_value > NANOSECOND_THRESHOLD
        result = apple_to_iso(ns_value)
        assert result == "2023-01-01T00:00:00+00:00"

    def test_none_returns_none(self):
        assert apple_to_iso(None) is None

    def test_zero_returns_none(self):
        assert apple_to_iso(0) is None

    def test_float_input(self):
        result = apple_to_iso(694224000.0)
        assert result is not None
        assert "2023-01-01" in result

    def test_string_input(self):
        result = apple_to_iso("694224000")
        assert result is not None
        assert "2023-01-01" in result


class TestIsoToApple:
    def test_round_trip_seconds(self):
        iso = "2023-01-01T00:00:00+00:00"
        apple_ts = iso_to_apple(iso)
        assert apple_ts is not None
        assert abs(apple_ts - 694224000) < 1

    def test_round_trip_nanoseconds(self):
        iso = "2023-01-01T00:00:00+00:00"
        ns = iso_to_apple(iso, nanoseconds=True)
        assert ns is not None
        assert abs(ns - 694224000 * 1_000_000_000) < 1_000

    def test_date_only_string(self):
        result = iso_to_apple("2023-01-01")
        assert result is not None
        assert abs(result - 694224000) < 1

    def test_empty_string_returns_none(self):
        assert iso_to_apple("") is None

    def test_apple_to_iso_round_trips(self):
        original_ts = 694224000.0
        iso = apple_to_iso(original_ts)
        back = iso_to_apple(iso)
        assert back is not None
        assert abs(back - original_ts) < 1


class TestDetectTimestampFormat:
    def test_nanoseconds(self):
        # A value well above NANOSECOND_THRESHOLD
        assert detect_timestamp_format(694224000 * 1_000_000_000) == "nanoseconds"

    def test_seconds(self):
        assert detect_timestamp_format(694224000) == "seconds"

    def test_small_value(self):
        assert detect_timestamp_format(100) == "seconds"

    def test_none(self):
        assert detect_timestamp_format(None) == "seconds"

    def test_threshold_boundary(self):
        # One below threshold → seconds; threshold itself → nanoseconds
        assert detect_timestamp_format(NANOSECOND_THRESHOLD - 1) == "seconds"
        assert detect_timestamp_format(NANOSECOND_THRESHOLD + 1) == "nanoseconds"
