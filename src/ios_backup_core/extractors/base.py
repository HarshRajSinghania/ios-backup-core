"""
Base extractor protocol.

All extractors should duck-type this — no forced inheritance needed.
"""

from typing import Protocol


class Extractor(Protocol):
    """Minimal interface shared by all data extractors."""

    def list(self, backup, **kwargs) -> dict:
        """List records from the backup. Returns a dict with a primary key
        (e.g. 'messages', 'calls', 'notes') and optional pagination fields."""
        ...
