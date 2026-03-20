#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": (),
}

financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    """
    For a given year, determines whether it is a leap year (True) or a common year (False).

    :param int year: The year to test
    :return: The leap year value.
    :rtype: bool
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Parses a date in DD-MM-YYYY format from a string.

    :param str maybe_dt: The string to test
    :return: A tuple of the format (day, month, year) or None if the date is invalid.
    :rtype: tuple[int, int, int] | None
    """
    parts_am = 3
    month_am = 12
    parts = maybe_dt.split("-")
    if len(parts) != parts_am:
        return None

    day_str, month_str, year_str = parts

    if not (day_str.isdigit() and month_str.isdigit() and year_str.isdigit()):
        return None

    day, month, year = int(day_str), int(month_str), int(year_str)

    if month < 1 or month > month_am:
        return None

    days_in_month = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31]

    if day < 1 or day > days_in_month[month - 1]:
        return None

    return day, month, year


def parse_amount(amount_str: str) -> float | None:
    """
    Parses a string containing a number (replacing commas with periods).

    :param str amount_str: String containing the number
    :return: Floating-point number or None if parsing failed
    :rtype: float | None
    """
    amount_str = amount_str.replace(",", ".")

    if amount_str.count(".") > 1:
        return None

    for character in amount_str:
        if not (character.isdigit() or character == "."):
            return None


    return float(amount_str)



def is_valid_category(category_name: str) -> bool:
    """
    Checks if a category exists.

    :param str category_name: Full name of the category (Common::Target)
    :return: Whether the category exists
    :rtype: bool
    """
    if "::" not in category_name:
        return False

    common, target = category_name.split("::", 1)

    if common not in EXPENSE_CATEGORIES:
        return False

    if not target:
        return True

    return target in EXPENSE_CATEGORIES[common]


def get_all_categories() -> list[str]:
    """
    Returns a list of all available categories.

    :return: List of strings with categories
    :rtype: list[str]
    """
    categories = []
    for common, targets in EXPENSE_CATEGORIES.items():
        categories.extend([f"{common}::{target}" for target in targets] or [f"{common}::"])
    return sorted(categories)


def income_handler(amount: float, income_date: str) -> str:
    financial_transactions_storage.append({"amount": amount, "date": income_date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    financial_transactions_storage.append({
        "category": category_name,
        "amount": -amount,
        "date": income_date
    })
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(get_all_categories())


def calculate_capital_up_to_date(target_date: tuple[int, int, int]) -> float:
    """
    Calculates total equity on the specified date.

    :param tuple target_date: Target date (day, month, year)
    :return: Total equity
    :rtype: float
    """
    total = 0.0
    day, month, year = target_date

    for transaction in financial_transactions_storage:
        trans_date = extract_date(transaction["date"])
        if trans_date is None:
            continue

        t_day, t_month, t_year = trans_date

        if (t_year < year or
                (t_year == year and t_month < month) or
                (t_year == year and t_month == month and t_day <= day)):
            total += transaction["amount"]

    return total


def get_month_transactions(month: int, year: int) -> list[dict[str, Any]]:
    """
    Returns transactions for the specified month.

    :param int month: Month
    :param int year: Year
    :return: List of transactions for the month
    :rtype: list[dict[str, Any]]
    """
    month_transactions = []

    for transaction in financial_transactions_storage:
        trans_date = extract_date(transaction["date"])
        if trans_date is None:
            continue

        _, t_month, t_year = trans_date

        if t_month == month and t_year == year:
            month_transactions.append(transaction)

    return month_transactions


def stats_handler(report_date: str) -> str:
    if not (date := extract_date(report_date)):
        return INCORRECT_DATE_MSG

    total = calculate_capital_up_to_date(date)

    income = expenses = 0.0
    cats = {}

    for t in get_month_transactions(date[1], date[2]):
        amt = t["amount"]
        if amt > 0:
            income += amt
        else:
            expenses -= amt
            if "category" in t:
                cats[t["category"]] = cats.get(t["category"], 0) - amt

    diff = income - expenses
    type_ = "profit" if diff >= 0 else "loss"

    out = [f"Your statistics as of {report_date}:",
           f"Total capital: {total:.2f} rubles",
           f"This month, the {type_} amounted to {abs(diff):.2f} rubles.",
           f"Income: {income:.2f} rubles",
           f"Expenses: {expenses:.2f} rubles",
           "",
           "Details (category: amount):"]

    if cats:
        out.extend(f"{i}. {cat}: {amt:,.0f}".replace(",", " ")
                   for i, (cat, amt) in enumerate(sorted(cats.items()), 1))

    return "\n".join(out)


def validate_amount(amount_str: str) -> float | None:
    """Checks if the sum is correct and returns it or None"""
    amount = parse_amount(amount_str)
    return amount if amount is not None and amount > 0 else None


def handle_income(parts: list[str]) -> None:
    """Income command handler"""
    parts_am = 3
    if len(parts) != parts_am:
        print(UNKNOWN_COMMAND_MSG)
        return

    if not (amount := validate_amount(parts[1])):
        print(NONPOSITIVE_VALUE_MSG)
        return

    if not extract_date(parts[2]):
        print(INCORRECT_DATE_MSG)
        return

    print(income_handler(amount, parts[2]))


def handle_cost(parts: list[str]) -> None:
    """Cost command handler"""
    parts_am_first = 2
    parts_am_second = 4
    if len(parts) == parts_am_first and parts[1].lower() == "categories":
        print(cost_categories_handler())
        return

    if len(parts) != parts_am_second:
        print(UNKNOWN_COMMAND_MSG)
        return

    if not is_valid_category(parts[1]):
        print(NOT_EXISTS_CATEGORY)
        print("Available categories:")
        print(cost_categories_handler())
        return

    if not (amount := validate_amount(parts[2])):
        print(NONPOSITIVE_VALUE_MSG)
        return

    if not extract_date(parts[3]):
        print(INCORRECT_DATE_MSG)
        return

    print(cost_handler(parts[1], amount, parts[3]))


def handle_stats(parts: list[str]) -> None:
    """Stats command handler"""
    parts_am = 2
    if len(parts) != parts_am:
        print(UNKNOWN_COMMAND_MSG)
        return

    if not extract_date(parts[1]):
        print(INCORRECT_DATE_MSG)
        return

    print(stats_handler(parts[1]))


def main() -> None:
    """The main function of the program"""
    while True:
        command_line = input()
        if not command_line:
            continue

        parts = command_line.strip().split()
        if not parts:
            continue

        match parts[0].lower():
            case "income":
                handle_income(parts)
            case "cost":
                handle_cost(parts)
            case "stats":
                handle_stats(parts)
            case _:
                print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
