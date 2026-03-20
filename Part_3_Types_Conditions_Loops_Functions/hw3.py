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
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: tuple формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parts = maybe_dt.split("-")
    if len(parts) != 3:
        return None

    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None

    if month < 1 or month > 12:
        return None

    days_in_month = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31]

    if day < 1 or day > days_in_month[month - 1]:
        return None

    return day, month, year


def parse_amount(amount_str: str) -> float | None:
    """
    Парсит строку с числом (заменяет запятую на точку).

    :param str amount_str: Строка с числом
    :return: Число с плавающей точкой или None, если не удалось распарсить
    :rtype: float | None
    """
    try:
        amount_str = amount_str.replace(",", ".")
        return float(amount_str)
    except ValueError:
        return None


def is_valid_category(category_name: str) -> bool:
    """
    Проверяет существование категории.

    :param str category_name: Полное имя категории (Common::Target)
    :return: Существует ли категория
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
    Возвращает список всех доступных категорий.

    :return: Список строк с категориями
    :rtype: list[str]
    """
    categories = []
    for common, targets in EXPENSE_CATEGORIES.items():
        if targets:
            for target in targets:
                categories.append(f"{common}::{target}")
        else:
            categories.append(f"{common}::")
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
    Рассчитывает общий капитал на указанную дату.

    :param tuple target_date: Целевая дата (день, месяц, год)
    :return: Общий капитал
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
    Возвращает транзакции за указанный месяц.

    :param int month: Месяц
    :param int year: Год
    :return: Список транзакций за месяц
    :rtype: list[dict[str, Any]]
    """
    month_transactions = []

    for transaction in financial_transactions_storage:
        trans_date = extract_date(transaction["date"])
        if trans_date is None:
            continue

        t_day, t_month, t_year = trans_date

        if t_month == month and t_year == year:
            month_transactions.append(transaction)

    return month_transactions


def stats_handler(report_date: str) -> str:
    date_tuple = extract_date(report_date)
    if date_tuple is None:
        return INCORRECT_DATE_MSG

    day, month, year = date_tuple

    total_capital = calculate_capital_up_to_date(date_tuple)
    month_transactions = get_month_transactions(month, year)

    month_income = 0.0
    month_expenses = 0.0
    expenses_by_category = {}

    for trans in month_transactions:
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

    result = [f"Your statistics as of {report_date}:"]
    result.append(f"Total capital: {total_capital:.2f} rubles")
    result.append(f"This month, the {result_type} amounted to {abs(month_result):.2f} rubles.")
    result.append(f"Income: {month_income:.2f} rubles")
    result.append(f"Expenses: {month_expenses:.2f} rubles")
    result.append("")
    result.append("Details (category: amount):")

    if expenses_by_category:
        sorted_categories = sorted(expenses_by_category.items())
        for i, (category, amount) in enumerate(sorted_categories, 1):
            amount_str = f"{amount:,.0f}".replace(",", " ")
            result.append(f"{i}. {category}: {amount_str}")

    return "\n".join(result)


def validate_amount(amount_str: str) -> float | None:
    """Проверяет корректность суммы и возвращает её или None."""
    amount = parse_amount(amount_str)
    return amount if amount is not None and amount > 0 else None


def handle_income(parts: list[str]) -> None:
    """Обработчик команды income."""
    if len(parts) != 3:
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
    """Обработчик команды cost."""
    if len(parts) == 2 and parts[1].lower() == "categories":
        print(cost_categories_handler())
        return

    if len(parts) != 4:
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
    """Обработчик команды stats."""
    if len(parts) != 2:
        print(UNKNOWN_COMMAND_MSG)
        return

    if not extract_date(parts[1]):
        print(INCORRECT_DATE_MSG)
        return

    print(stats_handler(parts[1]))


def main() -> None:
    """Основная функция программы."""
    try:
        for line in iter(input, ""):
            if not (parts := line.strip().split()):
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
    except EOFError:
        pass


if __name__ == "__main__":
    main()
