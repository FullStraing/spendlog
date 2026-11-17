"""Tests for spendlog — run: python -m unittest -v"""
import json
import os
import tempfile
import unittest

import spendlog


class TestAddExpense(unittest.TestCase):
    def setUp(self):
        self.data = {"expenses": [], "budgets": {}}

    def test_adds_entry(self):
        entry = spendlog.add_expense(self.data, 4.5, "Coffee", "oat latte", "2026-11-16")
        self.assertEqual(entry, {"date": "2026-11-16", "amount": 4.5,
                                 "category": "coffee", "note": "oat latte"})
        self.assertEqual(len(self.data["expenses"]), 1)

    def test_category_is_normalised(self):
        entry = spendlog.add_expense(self.data, 10, "  Groceries ", "", "2026-11-16")
        self.assertEqual(entry["category"], "groceries")

    def test_rejects_non_positive_amount(self):
        for bad in (0, -3.5):
            with self.assertRaises(ValueError):
                spendlog.add_expense(self.data, bad, "food", "", "2026-11-16")


class TestMonthTotals(unittest.TestCase):
    def setUp(self):
        self.data = {"expenses": [
            {"date": "2026-11-02", "amount": 4.5, "category": "coffee", "note": ""},
            {"date": "2026-11-15", "amount": 12.0, "category": "food", "note": ""},
            {"date": "2026-11-16", "amount": 3.0, "category": "coffee", "note": ""},
            {"date": "2026-10-30", "amount": 99.0, "category": "food", "note": ""},
        ], "budgets": {}}

    def test_totals_only_that_month(self):
        self.assertEqual(spendlog.month_totals(self.data, "2026-11"),
                         {"coffee": 7.5, "food": 12.0})

    def test_empty_month(self):
        self.assertEqual(spendlog.month_totals(self.data, "2026-09"), {})


class TestBudgets(unittest.TestCase):
    def test_remaining_and_over(self):
        data = {"expenses": [
            {"date": "2026-11-05", "amount": 120.0, "category": "food", "note": ""},
            {"date": "2026-11-06", "amount": 95.0, "category": "food", "note": ""},
        ], "budgets": {"food": 200.0, "coffee": 30.0}}
        rows = spendlog.budget_status(data, "2026-11")
        by_cat = {r["category"]: r for r in rows}
        self.assertEqual(by_cat["food"]["spent"], 215.0)
        self.assertEqual(by_cat["food"]["remaining"], -15.0)
        self.assertEqual(by_cat["coffee"]["spent"], 0.0)
        self.assertEqual(by_cat["coffee"]["remaining"], 30.0)


class TestPersistence(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "spendlog.json")
            data = spendlog.load(path)
            spendlog.add_expense(data, 5, "food", "snack", "2026-11-16")
            spendlog.save(path, data)
            again = spendlog.load(path)
            self.assertEqual(len(again["expenses"]), 1)
            self.assertEqual(again["expenses"][0]["amount"], 5)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as f:
                json.load(f)  # valid JSON


class TestCLI(unittest.TestCase):
    def test_add_then_month_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SPENDLOG_FILE"] = os.path.join(tmp, "s.json")
            try:
                self.assertEqual(spendlog.main(["add", "4.50", "coffee", "latte"]), 0)
                self.assertEqual(spendlog.main(["budget", "coffee", "30"]), 0)
                self.assertEqual(spendlog.main(["month"]), 0)
                data = spendlog.load(os.environ["SPENDLOG_FILE"])
                self.assertEqual(len(data["expenses"]), 1)
                self.assertEqual(data["budgets"]["coffee"], 30.0)
            finally:
                del os.environ["SPENDLOG_FILE"]

    def test_add_rejects_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SPENDLOG_FILE"] = os.path.join(tmp, "s.json")
            try:
                self.assertEqual(spendlog.main(["add", "0", "food"]), 2)
            finally:
                del os.environ["SPENDLOG_FILE"]


if __name__ == "__main__":
    unittest.main()
