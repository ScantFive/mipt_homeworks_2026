#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: Bool
    """
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: tuple формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    date_parts = maybe_dt.split('-')
    if len(date_parts) != 3:
        return None

    day, month, year = date_parts

    if not (day.isdigit() and month.isdigit() and year.isdigit()):
        return None

    day, month, year = [int(x) for x in date_parts]

    if month < 1 or month > 12 or day < 1 or year < 1:
        return None

    days_in_month = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if day > days_in_month[month - 1]:
        return None

    return day, month, year


def extract_amount(amount_str: str) -> float | None:
    """
    Парсит число с запятой или точкой как разделителем.

    :param str amount_str: Строка с числом
    :return: Число или None если не удалось
    """
    amount_str = amount_str.replace(',', '.')
    if amount_str.count('.') > 1:
        return None
    for character in amount_str:
        if not (character.isdigit() or character == '.'):
            return None

    amount = float(amount_str)
    return amount


def main() -> None:
    """Ваш код здесь"""

    incomes_by_date = {}
    costs_by_category = {}

    while True:

        line = input().strip()
        if not line:
            continue

        line_parts = line.split()
        command = line_parts[0]

        if command == "income":
            if len(line_parts) != 3:
                print(UNKNOWN_COMMAND_MSG)
                continue

            amount_str, date_str = line_parts[1], line_parts[2]

            amount = extract_amount(amount_str)
            if amount is None or amount <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue

            date = extract_date(date_str)
            if date is None:
                print(INCORRECT_DATE_MSG)
                continue

            day, month, year = date
            date_key = (year, month, day)

            if date_key in incomes_by_date:
                incomes_by_date[date_key] += amount
            else:
                incomes_by_date[date_key] = amount

            print(OP_SUCCESS_MSG)

        elif command == "cost":
            if len(line_parts) != 4:
                print(UNKNOWN_COMMAND_MSG)
                continue

            category, amount_str, date_str = line_parts[1], line_parts[2], line_parts[3]

            if not category or ' ' in category or '.' in category or ',' in category:
                print(UNKNOWN_COMMAND_MSG)
                continue

            amount = extract_amount(amount_str)
            if amount is None or amount <= 0:
                print(NONPOSITIVE_VALUE_MSG)
                continue

            date = extract_date(date_str)
            if date is None:
                print(INCORRECT_DATE_MSG)
                continue

            day, month, year = date
            date_key = (year, month, day)

            if category not in costs_by_category:
                costs_by_category[category] = {}

            if date_key in costs_by_category[category]:
                costs_by_category[category][date_key] += amount
            else:
                costs_by_category[category][date_key] = amount

            print(OP_SUCCESS_MSG)

        elif command == "stats":
            if len(line_parts) != 2:
                print(UNKNOWN_COMMAND_MSG)
                continue

            date_str = line_parts[1]

            date = extract_date(date_str)
            if date is None:
                print(INCORRECT_DATE_MSG)
                continue

            target_day, target_month, target_year = date

            total_capital = 0.0
            month_incomes = 0.0
            month_costs = 0.0
            month_costs_by_category = {}

            for date_key, amount in incomes_by_date.items():
                year, month, day = date_key

                if (year < target_year or
                        (year == target_year and month < target_month) or
                        (year == target_year and month == target_month and day <= target_day)):

                    total_capital += amount

                    if month == target_month and year == target_year:
                        month_incomes += amount

            for category, transactions in costs_by_category.items():
                for date_key, amount in transactions.items():
                    year, month, day = date_key

                    if year < target_year or (year == target_year and month < target_month) or (year == target_year and month == target_month and day <= target_day):
                        total_capital -= amount

                        if month == target_month and year == target_year:
                            month_costs += amount
                            month_costs_by_category[category] = month_costs_by_category.get(category, 0.0) + amount

            print(f"Ваша статистика по состоянию на {date_str}:")
            print(f"Суммарный капитал: {total_capital:.2f} рублей")

            difference = month_incomes - month_costs
            if difference >= 0:
                print(f"В этом месяце прибыль составила {difference:.2f} рублей")
            else:
                print(f"В этом месяце убыток составил {abs(difference):.2f} рублей")

            print(f"Доходы: {month_incomes:.2f} рублей")
            print(f"Расходы: {month_costs:.2f} рублей")

            print("\nДетализация (категория: сумма):")
            if month_costs_by_category:
                sorted_categories = sorted(month_costs_by_category.items())

                for i, (category, amount) in enumerate(sorted_categories, 1):
                    if amount.is_integer():
                        print(f"{i}. {category}: {int(amount)}")
                    else:
                        formatted_amount = f"{amount:.2f}".rstrip('0').rstrip('.')
                        print(f"{i}. {category}: {formatted_amount}")
            else:
                print()

        else:
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
