"""Tests for the demo expense tracker. Run: python3 -m unittest discover -s examples/expense-tracker -v"""
import contextlib
import io
import json
import os
import tempfile
import unittest

import expenses
from expenses import ExpenseError


class ParseAmountTests(unittest.TestCase):
    def test_valid_amounts_become_cents(self):
        cases = {"12.50": 1250, "3": 300, "0.05": 5, "0.1": 10, " 7.5 ": 750, "1000000000": 100000000000}
        for text, cents in cases.items():
            with self.subTest(text=text):
                self.assertEqual(expenses.parse_amount(text), cents)

    def test_invalid_amounts_are_rejected(self):
        for text in ["abc", "", "0", "0.00", "-5", "1.005", "1e3", "nan", "inf", "12,50", "1000000000.01"]:
            with self.subTest(text=text):
                with self.assertRaises(ExpenseError):
                    expenses.parse_amount(text)


class FormatAmountTests(unittest.TestCase):
    def test_format(self):
        self.assertEqual(expenses.format_amount(1250), "12.50")
        self.assertEqual(expenses.format_amount(5), "0.05")
        self.assertEqual(expenses.format_amount(0), "0.00")
        self.assertEqual(expenses.format_amount(100000), "1000.00")


class TempDirCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.path = os.path.join(self.dir, "data.json")

    def write_raw(self, text):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def read_raw(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read()


class StorageTests(TempDirCase):
    def test_missing_file_is_empty(self):
        self.assertEqual(expenses.load_expenses(self.path), [])

    def test_round_trip_leaves_no_temp_files(self):
        record = {"amount_cents": 100, "category": "food", "note": "", "date": "2026-10-03"}
        expenses.save_expenses(self.path, [record])
        self.assertEqual(expenses.load_expenses(self.path), [record])
        self.assertEqual(os.listdir(self.dir), ["data.json"])

    def test_corrupt_json_raises(self):
        self.write_raw("{not json")
        with self.assertRaises(ExpenseError):
            expenses.load_expenses(self.path)
        self.assertEqual(self.read_raw(), "{not json")

    def test_wrong_shape_raises(self):
        for raw in ['{"a": 1}', '[1, 2]', '[{"amount_cents": "5", "category": "x", "date": "2026-01-01"}]']:
            with self.subTest(raw=raw):
                self.write_raw(raw)
                with self.assertRaises(ExpenseError):
                    expenses.load_expenses(self.path)


class AddTests(TempDirCase):
    def test_add_persists_a_normalised_record(self):
        record = expenses.add_expense(self.path, "12.50", "  Food ", "lunch", on="2026-10-03")
        self.assertEqual(record, {"amount_cents": 1250, "category": "food", "note": "lunch", "date": "2026-10-03"})
        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(json.load(f), [record])

    def test_default_date_is_today(self):
        record = expenses.add_expense(self.path, "1", "misc")
        self.assertRegex(record["date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_invalid_amount_creates_no_file(self):
        with self.assertRaises(ExpenseError):
            expenses.add_expense(self.path, "abc", "food")
        self.assertFalse(os.path.exists(self.path))

    def test_empty_category_rejected(self):
        with self.assertRaises(ExpenseError):
            expenses.add_expense(self.path, "5", "   ")
        self.assertFalse(os.path.exists(self.path))

    def test_bad_date_rejected(self):
        with self.assertRaises(ExpenseError):
            expenses.add_expense(self.path, "5", "food", on="not-a-date")

    def test_add_to_corrupt_file_leaves_it_untouched(self):
        self.write_raw("garbage")
        with self.assertRaises(ExpenseError):
            expenses.add_expense(self.path, "5", "food")
        self.assertEqual(self.read_raw(), "garbage")


class CliTests(TempDirCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = expenses.main(["--file", self.path, *argv])
        return code, out.getvalue(), err.getvalue()

    def test_add_succeeds(self):
        code, out, err = self.run_cli("add", "12.50", "food", "lunch")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("12.50", out)
        self.assertEqual(len(expenses.load_expenses(self.path)), 1)

    def test_invalid_amounts_exit_1_and_do_not_touch_the_file(self):
        for bad in ["abc", "0", "-5", "1.005"]:
            with self.subTest(amount=bad):
                code, out, err = self.run_cli("add", bad, "food")
                self.assertEqual(code, 1)
                self.assertTrue(err.startswith("error:"))
                self.assertFalse(os.path.exists(self.path))

    def test_list_when_empty(self):
        code, out, _ = self.run_cli("list")
        self.assertEqual((code, out.strip()), (0, "No expenses yet."))

    def test_list_keeps_insertion_order(self):
        self.run_cli("add", "1.00", "food", "first")
        self.run_cli("add", "2.50", "travel", "second")
        code, out, _ = self.run_cli("list")
        lines = out.strip().splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 2)
        self.assertIn("first", lines[0])
        self.assertIn("1.00", lines[0])
        self.assertIn("second", lines[1])
        self.assertIn("2.50", lines[1])

    def test_total_all_and_by_category(self):
        self.run_cli("add", "10.00", "Food")
        self.run_cli("add", "2.25", "travel")
        self.run_cli("add", "0.75", "food")
        self.assertEqual(self.run_cli("total")[1].strip(), "Total: 13.00")
        self.assertEqual(self.run_cli("total", "--category", "FOOD")[1].strip(), "Total (food): 10.75")
        self.assertEqual(self.run_cli("total", "--category", "none")[1].strip(), "Total (none): 0.00")

    def test_total_has_no_float_drift(self):
        for _ in range(3):
            self.run_cli("add", "0.10", "x")
        self.assertEqual(self.run_cli("total")[1].strip(), "Total: 0.30")

    def test_corrupt_file_gives_error_exit_1(self):
        self.write_raw("garbage")
        for command in (["list"], ["total"], ["add", "1", "x"]):
            with self.subTest(command=command):
                code, _, err = self.run_cli(*command)
                self.assertEqual(code, 1)
                self.assertTrue(err.startswith("error:"))
        self.assertEqual(self.read_raw(), "garbage")


if __name__ == "__main__":
    unittest.main()
