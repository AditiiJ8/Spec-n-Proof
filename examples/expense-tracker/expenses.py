#!/usr/bin/env python3
"""A tiny command-line expense tracker.

It exists as a demo target for the spec-and-proof skills and is small on purpose.

    python3 expenses.py add 12.50 food "lunch"
    python3 expenses.py list
    python3 expenses.py total
    python3 expenses.py total --category food

Data lives in a JSON file: --file PATH, else $EXPENSES_FILE, else ./expenses.json.
Amounts are stored as integer cents, so repeated additions never drift.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import date

DEFAULT_FILE = "expenses.json"
MAX_CENTS = 100000000000  # 1,000,000,000.00
_AMOUNT = re.compile(r"([0-9]+)(?:\.([0-9]+))?")


class ExpenseError(Exception):
    """A problem the user can fix: bad input or an unreadable data file."""


def parse_amount(text):
    """Turn text such as '12.50' into integer cents, or raise ExpenseError."""
    match = _AMOUNT.fullmatch(text.strip())
    if not match:
        raise ExpenseError("not a valid amount: %r (use a positive number like 12.50)" % text)
    whole, fraction = match.group(1), match.group(2) or ""
    if len(fraction) > 2:
        raise ExpenseError("too many decimal places: %r (at most 2)" % text)
    cents = int(whole) * 100 + int(fraction.ljust(2, "0"))
    if cents <= 0:
        raise ExpenseError("amount must be greater than zero")
    if cents > MAX_CENTS:
        raise ExpenseError("amount is too large")
    return cents


def format_amount(cents):
    return "%d.%02d" % divmod(cents, 100)


def _is_record(item):
    return (
        isinstance(item, dict)
        and isinstance(item.get("amount_cents"), int)
        and not isinstance(item.get("amount_cents"), bool)
        and isinstance(item.get("category"), str)
        and isinstance(item.get("date"), str)
        and isinstance(item.get("note", ""), str)
    )


def load_expenses(path):
    """Return the stored expenses. A missing file means no expenses yet."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as exc:
        raise ExpenseError("cannot read %s: %s" % (path, exc))
    if not isinstance(data, list) or not all(_is_record(item) for item in data):
        raise ExpenseError("%s does not contain a list of expenses" % path)
    return data


def save_expenses(path, items):
    """Write atomically so a crash cannot leave a half-written file."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".expenses-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def add_expense(path, amount_text, category, note="", on=None):
    """Validate everything first, then load, append, and save."""
    cents = parse_amount(amount_text)
    category = category.strip().lower()
    if not category:
        raise ExpenseError("category must not be empty")
    try:
        day = date.fromisoformat(on).isoformat() if on else date.today().isoformat()
    except ValueError:
        raise ExpenseError("date must look like YYYY-MM-DD: %r" % on)
    items = load_expenses(path)
    record = {"amount_cents": cents, "category": category, "note": note, "date": day}
    items.append(record)
    save_expenses(path, items)
    return record


def total_cents(items, category=None):
    return sum(i["amount_cents"] for i in items if category is None or i["category"] == category)


def format_line(item):
    return ("%s  %10s  %s  %s" % (item["date"], format_amount(item["amount_cents"]), item["category"], item.get("note", ""))).rstrip()


def build_parser():
    parser = argparse.ArgumentParser(prog="expenses", description="A tiny expense tracker.")
    parser.add_argument("--file", default=os.environ.get("EXPENSES_FILE", DEFAULT_FILE), help="data file (default: $EXPENSES_FILE or ./expenses.json)")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="record an expense")
    add.add_argument("amount", help="for example 12.50")
    add.add_argument("category")
    add.add_argument("note", nargs="?", default="")
    add.add_argument("--date", help="YYYY-MM-DD (default: today)")
    commands.add_parser("list", help="show all expenses in the order added")
    total = commands.add_parser("total", help="sum of all expenses, or of one category")
    total.add_argument("--category")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "add":
            record = add_expense(args.file, args.amount, args.category, args.note, args.date)
            print("Added %s to %s on %s" % (format_amount(record["amount_cents"]), record["category"], record["date"]))
        elif args.command == "list":
            items = load_expenses(args.file)
            print("\n".join(format_line(i) for i in items) if items else "No expenses yet.")
        else:
            items = load_expenses(args.file)
            if args.category:
                category = args.category.strip().lower()
                print("Total (%s): %s" % (category, format_amount(total_cents(items, category))))
            else:
                print("Total: %s" % format_amount(total_cents(items)))
    except (ExpenseError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
