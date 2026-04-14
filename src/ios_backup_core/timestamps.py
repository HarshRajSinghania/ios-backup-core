"""
Timestamp conversion utilities for iOS backup data.

Consolidates timestamp handling from messages.py, calls.py, photos.py,
and browser_history.py into a single authoritative module.
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

# Apple Cocoa epoch: Jan 1, 2001 00:00:00 UTC
APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

# Seconds between Unix epoch (1970-01-01) and Apple epoch (2001-01-01)
APPLE_EPOCH_OFFSET = 978307200

# Dates above this value are stored in nanoseconds (iOS 14+)
NANOSECOND_THRESHOLD = 1_000_000_000_000

# Seconds between Windows/Chrome epoch (1601-01-01) and Unix epoch (1970-01-01)
# Chrome/WebKit stores timestamps as microseconds since 1601-01-01
WEBKIT_EPOCH_OFFSET = 11644473600


def apple_to_iso(apple_timestamp) -> Optional[str]:
    """Convert Apple Cocoa timestamp to ISO 8601 string.

    Automatically detects nanosecond timestamps (iOS 14+) via NANOSECOND_THRESHOLD.
    Copied from messages.py:apple_date_to_iso() — do not alter the logic.
    """
    if apple_timestamp is None or apple_timestamp == 0:
        return None
    try:
        ts = float(apple_timestamp)
        # Detect nanosecond timestamps (iOS 14+)
        if ts > NANOSECOND_THRESHOLD:
            ts = ts / 1_000_000_000
        dt = APPLE_EPOCH + timedelta(seconds=ts)
        return dt.isoformat()
    except (ValueError, OverflowError):
        return None


def iso_to_apple(iso_str: str, nanoseconds: bool = False) -> Optional[float]:
    """Convert ISO 8601 string to Apple Cocoa epoch timestamp.

    Pass nanoseconds=True when the target DB stores timestamps as nanoseconds
    (iOS 14+), which is detected by sampling a row before calling this.
    Copied from messages.py:iso_to_apple_date() — do not alter the logic.
    """
    if not iso_str:
        return None
    try:
        # Accept date-only strings like "2023-01-01"
        if len(iso_str) == 10:
            iso_str += "T00:00:00"
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = dt - APPLE_EPOCH.replace(tzinfo=timezone.utc)
        seconds = delta.total_seconds()
        return seconds * 1_000_000_000 if nanoseconds else seconds
    except (ValueError, TypeError):
        return None


def detect_timestamp_format(value) -> str:
    """Classify a raw timestamp value by magnitude.

    Returns:
        'nanoseconds'  — Apple epoch nanoseconds (iOS 14+, value > 1e12)
        'seconds'      — Apple epoch seconds (value <= 1e12, value > 0)
        'unix'         — Unix epoch seconds (negative or anomalously large)
    """
    if value is None:
        return 'seconds'
    try:
        v = float(value)
        if v > NANOSECOND_THRESHOLD:
            return 'nanoseconds'
        return 'seconds'
    except (ValueError, TypeError):
        return 'seconds'


def db_uses_nanoseconds(conn: sqlite3.Connection) -> bool:
    """Return True if the message table stores timestamps in nanoseconds (iOS 14+).

    Copied from messages.py:_db_uses_nanoseconds() — do not alter the logic.
    """
    row = conn.execute("SELECT date FROM message WHERE date > 0 LIMIT 1").fetchone()
    if row and row[0] is not None:
        return float(row[0]) > NANOSECOND_THRESHOLD
    return False


def webkit_to_iso(webkit_timestamp) -> Optional[str]:
    """Convert a WebKit/Chrome timestamp to ISO 8601 string.

    Chrome stores timestamps as microseconds since 1601-01-01 00:00:00 UTC.
    """
    if webkit_timestamp is None or webkit_timestamp == 0:
        return None
    try:
        ts = float(webkit_timestamp)
        # Convert microseconds since Windows epoch to seconds since Unix epoch
        unix_seconds = (ts / 1_000_000) - WEBKIT_EPOCH_OFFSET
        dt = datetime.fromtimestamp(unix_seconds, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def firefox_to_iso(timestamp, divisor: int = 1_000_000) -> Optional[str]:
    """Convert a Firefox iOS timestamp to ISO 8601 string.

    Firefox legacy (browser.db) uses microseconds since Unix epoch → divisor=1_000_000.
    Firefox places (places.db) uses milliseconds since Unix epoch → divisor=1_000.

    Extracted from browser_history.py inline conversion logic.
    """
    if timestamp is None or timestamp == 0:
        return None
    try:
        dt = datetime.fromtimestamp(float(timestamp) / divisor, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, OverflowError, OSError):
        return None
