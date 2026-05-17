#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS_COUNT = 3
MAX_MONTH = 12
MIN_YEAR = 1
AMOUNT_SPLIT_MAX = 2
INCOME_CMD_ARGS = 3
COST_CMD_ARGS = 4
STATS_CMD_ARGS = 2
CATEGORIES_CMD_ARGS = 2
DAYS_IN_MONTH = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None
    if not all(p.isdigit() for p in parts):
        return None

    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    if year < MIN_YEAR or month < 1 or month > MAX_MONTH or day < 1:
        return None

    days_in_month = DAYS_IN_MONTH.copy()
    if is_leap_year(year):
        days_in_month[2] = 29

    if day > days_in_month[month]:
        return None

    return day, month, year


def _parse_amount(s: str) -> float | None:
    s = s.replace(",", ".")
    if not s or s in {".", "-"}:
        return None

    neg = False
    if s[0] == "-":
        neg = True
        s = s[1:]

    if not s or s == ".":
        return None

    parts = s.split(".")
    if len(parts) > AMOUNT_SPLIT_MAX:
        return None

    for p in parts:
        if not p or not p.isdigit():
            return None

    return -float(s) if neg else float(s)


def _is_valid_category(cat: str) -> bool:
    if "::" not in cat:
        return False
    common, target = cat.split("::")
    return common in EXPENSE_CATEGORIES and target in EXPENSE_CATEGORIES[common]


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({"amount": amount, "date": parsed_date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if not _is_valid_category(category_name):
        return NOT_EXISTS_CATEGORY
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({"category": category_name, "amount": amount, "date": parsed_date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(f"{k}::{v}" for k, kv in EXPENSE_CATEGORIES.items() for v in kv)


def stats_handler(report_date: str) -> str:
    data = _stats_calculator(report_date)
    if not data:
        return INCORRECT_DATE_MSG

    def fmt_detail(v: float) -> str:
        return str(int(v)) if v == int(v) else f"{v:.2f}"

    def fmt_total(v: float) -> str:
        return f"{v:.2f}"

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {fmt_total(data['total_capital'])} rubles",
        f"This month, the {data['diff_word']} amounted to {fmt_total(data['diff_val'])} rubles.",
        f"Income: {fmt_total(data['month_income'])} rubles",
        f"Expenses: {fmt_total(data['month_expense'])} rubles",
        "",
        "Details (category: amount):",
    ]

    if data["cat_expenses"]:
        sorted_cats = sorted(data["cat_expenses"].keys(), key=lambda s: s.lower())
        for i, cat in enumerate(sorted_cats, 1):
            lines.append(f"{i}. {cat}: {fmt_detail(data['cat_expenses'][cat])}")

    return "\n".join(lines)


def _stats_calculator(report_date: str) -> dict[str, Any]:
    rd = extract_date(report_date)
    if rd is None:
        return {}
    report_year, report_month, report_day = rd[2], rd[1], rd[0]
    total_capital = 0.0
    month_income = 0.0
    month_expense = 0.0
    cat_expenses: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        if "date" not in transaction:
            continue
        td = transaction["date"]
        transaction_day, transaction_month, transaction_year = td
        if (transaction_year, transaction_month, transaction_day) > (report_year, report_month, report_day):
            continue

        val = transaction["amount"]
        is_expense = "category" in transaction
        if is_expense:
            total_capital -= val
        else:
            total_capital += val

        if transaction_year == report_year and transaction_month == report_month:
            if is_expense:
                month_expense += val
                cat = transaction["category"]
                cat_expenses[cat] = cat_expenses.get(cat, 0.0) + val
            else:
                month_income += val

    month_diff = month_income - month_expense
    return {
        "total_capital": total_capital,
        "diff_word": "profit" if month_diff >= 0 else "loss",
        "diff_val": abs(month_diff),
        "month_income": month_income,
        "month_expense": month_expense,
        "cat_expenses": cat_expenses,
    }


def _handle_income_cmd(parts: list[str]) -> None:
    if len(parts) != INCOME_CMD_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return
    amt = _parse_amount(parts[1])
    if amt is None:
        print(NONPOSITIVE_VALUE_MSG)
        return
    print(income_handler(amt, parts[2]))


def _handle_cost_cmd(parts: list[str]) -> None:
    if len(parts) == CATEGORIES_CMD_ARGS and parts[1] == "categories":
        print(cost_categories_handler())
        return
    if len(parts) != COST_CMD_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return
    amt = _parse_amount(parts[2])
    if amt is None:
        print(NONPOSITIVE_VALUE_MSG)
        return
    print(cost_handler(parts[1], amt, parts[3]))


def _handle_stats_cmd(parts: list[str]) -> None:
    if len(parts) != STATS_CMD_ARGS:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(stats_handler(parts[1]))


def _process_line(line: str) -> None:
    parts = line.split()
    if not parts:
        return
    cmd = parts[0]
    if cmd == "income":
        _handle_income_cmd(parts)
    elif cmd == "cost":
        _handle_cost_cmd(parts)
    elif cmd == "stats":
        _handle_stats_cmd(parts)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    while True:
        try:
            line = input().strip()
            if not line:
                continue
            _process_line(line)
        except EOFError:
            break


if __name__ == "__main__":
    main()
