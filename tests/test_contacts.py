"""Tests for ios_backup_core.contacts."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ios_backup_core.contacts import normalize_phone, clean_phone_number, resolve_contact


class TestNormalizePhone:
    def test_us_formatted(self):
        assert normalize_phone("+1 (775) 555-1234") == "7755551234"

    def test_dashes(self):
        assert normalize_phone("775-555-1234") == "7755551234"

    def test_dots(self):
        assert normalize_phone("775.555.1234") == "7755551234"

    def test_e164_strips_country_code(self):
        # 11-digit number → last 10
        assert normalize_phone("+17755551234") == "7755551234"

    def test_short_number_unchanged(self):
        # Less than 10 digits — return as-is (digits only)
        assert normalize_phone("555-1234") == "5551234"

    def test_email_stays_empty(self):
        # No digits at all
        result = normalize_phone("user@example.com")
        assert result == ""

    def test_already_normalized(self):
        assert normalize_phone("7755551234") == "7755551234"


class TestCleanPhoneNumber:
    def test_strips_formatting_keeps_plus(self):
        assert clean_phone_number("+1 (775) 555-1234") == "+17755551234"

    def test_no_plus(self):
        assert clean_phone_number("775-555-1234") == "7755551234"

    def test_empty(self):
        assert clean_phone_number("") == ""

    def test_none_like_empty(self):
        assert clean_phone_number("") == ""


class TestResolveContact:
    def _contacts(self):
        return {
            "7755551234": "Alice",
            "+17755551234": "Alice",
            "bob@example.com": "Bob",
            "BOB@EXAMPLE.COM": "Bob",
        }

    def test_exact_match(self):
        c = self._contacts()
        assert resolve_contact("7755551234", c) == "Alice"

    def test_normalized_match(self):
        c = self._contacts()
        # Input has formatting; normalized form "7755551234" is in contacts
        assert resolve_contact("775-555-1234", c) == "Alice"

    def test_plus1_prefix_toggle_add(self):
        c = self._contacts()
        # Input is 10-digit; contacts has "+1..." key
        assert resolve_contact("7755551234", c) == "Alice"

    def test_plus1_prefix_toggle_strip(self):
        c = {"+17755551234": "Alice"}
        # Input has +1 prefix; contacts also has the bare 10-digit form
        # Ensure both directions work
        result = resolve_contact("+17755551234", c)
        assert result == "Alice"

    def test_email_exact(self):
        c = self._contacts()
        assert resolve_contact("bob@example.com", c) == "Bob"

    def test_email_case_insensitive(self):
        c = {"bob@example.com": "Bob"}
        assert resolve_contact("BOB@EXAMPLE.COM", c) == "Bob"

    def test_unknown_returns_empty(self):
        c = self._contacts()
        assert resolve_contact("9995550000", c) == ""

    def test_empty_identifier_returns_empty(self):
        assert resolve_contact("", {}) == ""
