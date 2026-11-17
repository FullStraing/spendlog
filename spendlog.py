#!/usr/bin/env python3
"""spendlog — a tiny CLI expense tracker for a tight student budget.

No dependencies, Python 3.10+. One JSON file holds everything.

Usage:
    python spendlog.py add 4.50 coffee "oat latte"
    python spendlog.py add 12.00 groceries --category food
    python spendlog.py list
    python spendlog.py list --category coffee
    python spendlog.py month            # totals by category this month
    python spendlog.py month 2026-10   # totals for a given month
    python spendlog.py budget food 200  # monthly budget for a category
    python spendlog.py budgets          # list budgets

Data lives in spendlog.json next to this file (or SPENDLOG_FILE).
"""
import argparse
import json
import os
import sys
from datetime import date

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spendlog.json")


def data_file() -> str:
    return os.environ.get("SPENDLOG_FILE", DEFAULT_FILE)


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {"expenses": [], "budgets": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def add_expense(data: dict, amount: float, category: str, note: str = "", when: str = "") -> dict:
    if amount <= 0:
        raise ValueError("amount must be positive")
    entry = {
        "date": when or date.today().isoformat(),
        "amount": round(amount, 2),
        "category": category.strip().lower(),
        "note": note.strip(),
    }
    data.setdefault("expenses", []).append(entry)
    return entry


def month_totals(data: dict, month: str) -> dict:
    """Totals per category for YYYY-MM, plus the grand total under ''."""
    totals: dict[str, float] = {}
    for e in data.get("expenses", []):
        if e["date"].startswith(month):
            totals[e["category"]] = round(totals.get(e["category"], 0) + e["amount"], 2)
    return totals


def budget_status(data: dict, month: str) -> list[dict]:
    """For each budgeted category: budget, spent, remaining."""
    totals = month_totals(data, month)
    rows = []
    for category, budget in sorted(data.get("budgets", {}).items()):
        spent = totals.get(category, 0.0)
        rows.append({
            "category": category,
            "budget": budget,
            "spent": spent,
            "remaining": round(budget - spent, 2),
        })
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="spendlog", description="Tiny CLI expense tracker.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="log an expense")
    p_add.add_argument("amount", type=float)
    p_add.add_argument("category")
    p_add.add_argument("note", nargs="?", default="")
    p_add.add_argument("--date", default="", help="YYYY-MM-DD (default: today)")

    p_list = sub.add_parser("list", help="list expenses")
    p_list.add_argument("--category", default="")
    p_list.add_argument("--month", default="", help="YYYY-MM filter")

    p_month = sub.add_parser("month", help="totals by category for a month")
    p_month.add_argument("month", nargs="?", default=date.today().strftime("%Y-%m"))

    p_budget = sub.add_parser("budget", help="set a monthly budget for a category")
    p_budget.add_argument("category")
    p_budget.add_argument("amount", type=float)

    sub.add_parser("budgets", help="list budgets with spending vs remaining")

    args = parser.parse_args(argv)
    path = data_file()
    data = load(path)

    if args.command == "add":
        try:
            entry = add_expense(data, args.amount, args.category, args.note, args.date)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        save(path, data)
        print(f"logged ${entry['amount']:.2f} [{entry['category']}] {entry['note']} ({entry['date']})")
    elif args.command == "list":
        rows = data.get("expenses", [])
        if args.category:
            rows = [e for e in rows if e["category"] == args.category.strip().lower()]
        if args.month:
            rows = [e for e in rows if e["date"].startswith(args.month)]
        for e in rows:
            print(f"{e['date']}  ${e['amount']:>8.2f}  [{e['category']:<12}] {e['note']}")
        print(f"{len(rows)} expense(s), total ${sum(e['amount'] for e in rows):.2f}")
    elif args.command == "month":
        totals = month_totals(data, args.month)
        grand = 0.0
        for category in sorted(totals):
            print(f"{category:<15} ${totals[category]:>8.2f}")
            grand += totals[category]
        print(f"{'TOTAL':<15} ${grand:>8.2f}")
        for row in budget_status(data, args.month):
            flag = "OVER" if row["remaining"] < 0 else "left"
            print(f"budget {row['category']}: ${row['spent']:.2f} / ${row['budget']:.2f} "
                  f"(${abs(row['remaining']):.2f} {flag})")
    elif args.command == "budget":
        if args.amount <= 0:
            print("error: amount must be positive", file=sys.stderr)
            return 2
        data.setdefault("budgets", {})[args.category.strip().lower()] = round(args.amount, 2)
        save(path, data)
        print(f"budget set: {args.category.strip().lower()} ${args.amount:.2f}/month")
    elif args.command == "budgets":
        rows = budget_status(data, date.today().strftime("%Y-%m"))
        if not rows:
            print("no budgets set — use: spendlog budget <category> <amount>")
        for row in rows:
            print(f"{row['category']:<15} spent ${row['spent']:>8.2f} / ${row['budget']:.2f} "
                  f"-> ${row['remaining']:.2f} left")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
