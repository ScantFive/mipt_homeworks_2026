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
MONTH31 = (1, 3, 5, 7, 8, 10, 12)
MONTH30 = (4, 6, 9, 11)
FEBRUARY = 2
AMOUNT_KEY = "amount"
DATE_KEY = "date"
CATEGORY_KEY = "category"

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
    if year % 4 != 0:
        return False
    if year % 100 == 0:
        return year % 400 == 0
    return True


def get_days_in_month(month: int, year: int) -> int:
    if month in MONTH31:
        return 31
    if month in MONTH30:
        return 30
    if month == FEBRUARY:
        return 29 if is_leap_year(year) else 28
    return 0


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None
    if not all(p.isdigit() for p in parts):
        return None

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])
    if year < MIN_YEAR or month < 1 or month > MAX_MONTH or day < 1:
        return None

    if day > get_days_in_month(month, year):
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
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({AMOUNT_KEY: amount, DATE_KEY: parsed_date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if not _is_valid_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({CATEGORY_KEY: category_name, AMOUNT_KEY: amount, DATE_KEY: parsed_date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    output: list[str] = []
    for common, scats in EXPENSE_CATEGORIES.items():
        output.extend(f"{common}::{target}" for target in scats)
    return "\n".join(output)


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
        sorted_cats = _get_sorted_categories(data["cat_expenses"])
        for i, (cat, amount) in enumerate(sorted_cats, 1):
            lines.append(f"{i}. {cat}: {fmt_detail(amount)}")

    return "\n".join(lines)


def _get_sorted_categories(cat_expenses: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(cat_expenses.items(), key=lambda x: x[0].lower())


def _update_capital(transaction: dict[str, Any], current_capital: float) -> float:
    amount = transaction[AMOUNT_KEY]
    if CATEGORY_KEY in transaction:
        return current_capital - float(amount)
    return current_capital + float(amount)


def _update_stats(
    transaction: dict[str, Any], report_year: int, report_month: int, stats: tuple[float, float, dict[str, float]]
) -> tuple[float, float, dict[str, float]]:
    income, expense, details = stats
    t_date = transaction.get(DATE_KEY)
    if not isinstance(t_date, tuple) or len(t_date) != DATE_PARTS_COUNT:
        return income, expense, details

    if t_date[2] == report_year and t_date[1] == report_month:
        amount = transaction.get(AMOUNT_KEY)
        if isinstance(amount, (int, float)):
            if CATEGORY_KEY in transaction:
                expense += float(amount)
                cat = transaction.get(CATEGORY_KEY)
                if isinstance(cat, str):
                    details[cat] = details.get(cat, 0) + float(amount)
            else:
                income += float(amount)
    return income, expense, details


def _is_up_to_date(transaction: dict[str, Any], report_date: tuple[int, int, int]) -> bool:
    if not transaction or DATE_KEY not in transaction:
        return False
    transaction_date = transaction[DATE_KEY]
    return (transaction_date[2], transaction_date[1], transaction_date[0]) <= report_date


def _process_transaction_stats(
    transaction: dict[str, Any],
    report_date: tuple[int, int, int],
    total_capital: float,
    month_stats: tuple[float, float, dict[str, float]],
) -> tuple[float, tuple[float, float, dict[str, float]]]:
    if not transaction or DATE_KEY not in transaction:
        return total_capital, month_stats

    td = transaction[DATE_KEY]
    report_year, report_month, report_day = report_date

    if not isinstance(td, tuple) or len(td) != DATE_PARTS_COUNT:
        return total_capital, month_stats

    transaction_day, transaction_month, transaction_year = td
    if (transaction_year, transaction_month, transaction_day) > (report_year, report_month, report_day):
        return total_capital, month_stats

    val = transaction[AMOUNT_KEY]
    if not isinstance(val, (int, float)):
        return total_capital, month_stats

    is_expense = CATEGORY_KEY in transaction
    if is_expense:
        total_capital -= float(val)
    else:
        total_capital += float(val)

    month_stats = _update_stats(transaction, report_year, report_month, month_stats)

    return total_capital, month_stats


def _stats_calculator(report_date: str) -> dict[str, Any]:
    rd = extract_date(report_date)
    if rd is None:
        return {}

    report_date_for_process = (rd[2], rd[1], rd[0])
    total_capital: float = 0
    month_stats: tuple[float, float, dict[str, float]] = (0, 0, {})

    for transaction in financial_transactions_storage:
        total_capital, month_stats = _process_transaction_stats(transaction, report_date_for_process)

    month_income, month_expense, cat_expenses = month_stats
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
    if len(parts) == CATEGORIES_CMD_ARGS and parts[1] == CATEGORY_KEY:
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
    def get_line() -> str | None:
        try:
            return input().strip()
        except EOFError:
            return None

    while True:
        line = get_line()
        if line is None:
            break
        if line:
            _process_line(line)


if __name__ == "__main__":
    main()
