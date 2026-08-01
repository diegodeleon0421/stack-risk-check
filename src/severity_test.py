#!/usr/bin/env python3
"""Tests for the severity classifier.

These exist so a reader can disprove the logic rather than trust it. Two of these cases are
regressions from bugs found in real use — see CHANGELOG.md.
"""
from __future__ import annotations

import unittest
from datetime import date

from severity import classify


def product(name, cycles=None, next_eol=None, next_cycle=None, events=None, source="https://x"):
    return {"product": name, "cycles": cycles or [], "next_eol": next_eol,
            "next_eol_cycle": next_cycle, "events": events or [], "source": source}


TODAY = date(2026, 8, 1)


class TestSeverity(unittest.TestCase):
    def test_past_eol_is_urgent(self):
        p = product("python", [{"cycle": "3.9", "eol_date": "2025-10-31", "dead": True}])
        r = classify(p, "3.9", "python 3.9", TODAY)
        self.assertEqual(r.severity, "urgent")
        self.assertIn("2025-10-31", r.facts[0])

    def test_within_90_days_is_upcoming(self):
        p = product("redis", [{"cycle": "8.0", "eol_date": "2026-09-15", "dead": False}])
        self.assertEqual(classify(p, "8.0", "redis 8.0", TODAY).severity, "upcoming")

    def test_within_a_year_is_watch(self):
        p = product("postgresql", [{"cycle": "14", "eol_date": "2026-11-12", "dead": False}])
        r = classify(p, "14", "postgresql 14", TODAY)
        self.assertEqual(r.severity, "watch")
        self.assertEqual(r.days_remaining, 103)

    def test_far_future_is_clear(self):
        p = product("go", [{"cycle": "1.25", "eol_date": "2028-01-01", "dead": False}])
        self.assertEqual(classify(p, "1.25", "go 1.25", TODAY).severity, "clear")

    def test_unresolved_input_is_unknown_not_clear(self):
        """Absence of evidence must never be reported as safety."""
        r = classify(None, None, "frobnicator quantum db", TODAY)
        self.assertEqual(r.severity, "unknown")
        self.assertNotEqual(r.severity, "clear")

    def test_shutdown_event_forces_urgent(self):
        """A recorded shutdown outranks a healthy lifecycle."""
        p = product("localstack", events=[{"category": "eol", "title": "archived"}])
        self.assertEqual(classify(p, None, "localstack", TODAY).severity, "urgent")

    def test_acquisition_raises_clear_to_watch_but_not_higher(self):
        p = product("acme", [{"cycle": "5", "eol_date": "2029-01-01", "dead": False}],
                    events=[{"category": "acquired", "title": "acquired by BigCo"}])
        self.assertEqual(classify(p, "5", "acme 5", TODAY).severity, "watch")

    def test_regression_no_negative_day_counts(self):
        """A cached next_eol that has since passed must read as ended, not '-1 days remaining'."""
        p = product("mongodb", next_eol="2026-07-31", next_cycle="8.2")
        r = classify(p, None, "mongodb", TODAY)
        self.assertEqual(r.severity, "urgent")
        self.assertTrue(all("-1 days" not in f for f in r.facts))
        self.assertIn("reached end of life", " ".join(r.facts))

    def test_unknown_version_falls_back_to_product_level_and_says_so(self):
        p = product("php", [{"cycle": "8.3", "eol_date": "2027-12-31", "dead": False}],
                    next_eol="2027-12-31", next_cycle="8.3")
        r = classify(p, "9.9", "php 9.9", TODAY)
        self.assertIn("not in the tracked release list", " ".join(r.facts))

    def test_days_until_floors_rather_than_rounds(self):
        p = product("x", [{"cycle": "1", "eol_date": "2026-08-02", "dead": False}])
        self.assertEqual(classify(p, "1", "x 1", TODAY).days_remaining, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
