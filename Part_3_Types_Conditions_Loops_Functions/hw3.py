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
    """Для заданного года определяет: високосный (True) или невисокосный (False)."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """Парсит дату формата DD-MM-YYYY из строки."""
    parts = maybe_dt.split("-")
    if len(parts) != 3:
        return None

    day_str, month_str, year_str = parts

    if not (day_str.isdigit() and month_str.isdigit() and year_str.isdigit()):
        return None

    day, month, year = int(day_str), int(month_str), int(year_str)

    if month < 1 or month > 12:
        return None

    days_in_month = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31]

    if day < 1 or day > days_in_month[month - 1]:
        return None

    return day, month, year


def parse_amount(amount_str: str) -> float | None:
    """Парсит строку с числом (заменяет запятую на точку)."""
    amount_str = amount_str.replace(",", ".")

    valid_chars = set("0123456789.")
    for ch in amount_str:
        if ch not in valid_chars:
            return None

    if amount_str.count(".") > 1:
        return None

    if "." in amount_str:
        integer_part, fractional_part = amount_str.split(".")

        if not integer_part.isdigit() or not fractional_part.isdigit():
            return None

        integer_value = int(integer_part) if integer_part else 0
        fractional_value = int(fractional_part) / (10 ** len(fractional_part))
        return integer_value + fractional_value
    else:
        if not amount_str.isdigit():
            return None
        return int(amount_str)


def is_valid_category(category_name: str) -> bool:
    """Проверяет существование категории."""
    if "::" not in category_name:
        return False

    common, target = category_name.split("::", 1)

    if common not in EXPENSE_CATEGORIES:
        return False

    if not target:
        return True

    return target in EXPENSE_CATEGORIES[common]


def get_all_categories() -> list[str]:
    """Возвращает список всех доступных категорий."""
    categories = []
    for common, targets in EXPENSE_CATEGORIES.items():
        if targets:
            for target in targets:
                categories.append(f"{common}::{target}")
        else:
            categories.append(f"{common}::")
    return sorted(categories)


def income_handler(amount: float, income_date: str) -> str:
    """Добавляет доход."""
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    if extract_date(income_date) is None:
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({"amount": amount, "date": income_date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    """Добавляет расход."""
    if not is_valid_category(category_name):
        return NOT_EXISTS_CATEGORY

    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    if extract_date(income_date) is None:
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({
        "category": category_name,
        "amount": -amount,
        "date": income_date
    })
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    """Возвращает список всех категорий."""
    return "\n".join(get_all_categories())


def calculate_capital_up_to_date(target_date: tuple[int, int, int]) -> float:
    """Рассчитывает общий капитал на указанную дату."""
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
    """Возвращает транзакции за указанный месяц."""
    return [
        transaction
        for transaction in financial_transactions_storage
        if (date := extract_date(transaction["date"])) is not None
           and date[1] == month and date[2] == year
    ]


def stats_handler(report_date: str) -> str:
    """Возвращает статистику на указанную дату."""
    date_tuple = extract_date(report_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG

    day, month, year = date_tuple

    total_capital = calculate_capital_up_to_date(date_tuple)

    month_income = 0.0
    month_expenses = 0.0
    expenses_by_category = {}

    for trans in get_month_transactions(month, year):
        amount = trans["amount"]
        if amount > 0:
            month_income += amount
        else:
            month_expenses += abs(amount)
            if "category" in trans:
                category = trans["category"]
                expenses_by_category[category] = expenses_by_category.get(category, 0) + abs(amount)

    month_result = month_income - month_expenses
    result_type = "profit" if month_result >= 0 else "loss"

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
        f"This month, the {result_type} amounted to {abs(month_result):.2f} rubles.",
        f"Income: {month_income:.2f} rubles",
        f"Expenses: {month_expenses:.2f} rubles",
        "",
        "Details (category: amount):"
    ]

    if expenses_by_category:
        for i, (category, amount) in enumerate(sorted(expenses_by_category.items()), 1):
            amount_str = f"{amount:,.0f}".replace(",", " ")
            lines.append(f"{i}. {category}: {amount_str}")

    return "\n".join(lines)


def main() -> None:
    """Основная функция программы."""
    while True:
        command_line = input()
        if not command_line:
            continue

        parts = command_line.strip().split()
        if not parts:
            continue

        command = parts[0].lower()

        if command == "income":
            if len(parts) != 3:
                print(UNKNOWN_COMMAND_MSG)
                continue

            amount = parse_amount(parts[1])
            if amount is None or amount <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue

            if extract_date(parts[2]) is None:
                print(INCORRECT_DATE_MSG)
                continue

            print(income_handler(amount, parts[2]))

        elif command == "cost":
            if len(parts) == 2 and parts[1].lower() == "categories":
                print(cost_categories_handler())
                continue

            if len(parts) != 4:
                print(UNKNOWN_COMMAND_MSG)
                continue

            if not is_valid_category(parts[1]):
                print(NOT_EXISTS_CATEGORY)
                print("Available categories:")
                print(cost_categories_handler())
                continue

            amount = parse_amount(parts[2])
            if amount is None or amount <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue

            if extract_date(parts[3]) is None:
                print(INCORRECT_DATE_MSG)
                continue

            print(cost_handler(parts[1], amount, parts[3]))

        elif command == "stats":
            if len(parts) != 2:
                print(UNKNOWN_COMMAND_MSG)
                continue

            if extract_date(parts[1]) is None:
                print(INCORRECT_DATE_MSG)
                continue

            print(stats_handler(parts[1]))

        else:
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
