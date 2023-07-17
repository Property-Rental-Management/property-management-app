from enum import Enum
from os import path


# TODO create a class to contain this enum types for the entire project
class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    DIRECT_DEPOSIT = "direct_deposit"
    BANK_TRANSFER = "bank_transfer"


def get_payment_methods() -> list[str]:
    """
    Get a list of payment methods.

    :return: A list of payment methods.
    """
    return [method.value for method in PaymentMethod]


def static_folder() -> str:
    return path.join(path.dirname(path.abspath(__file__)), '../../static')


def template_folder() -> str:
    return path.join(path.dirname(path.abspath(__file__)), '../../templates')


def format_with_grouping(number):
    parts = str(number).split(".")
    whole_part = parts[0]

    formatted_whole_part = ""
    while whole_part:
        formatted_whole_part = whole_part[-3:] + formatted_whole_part
        whole_part = whole_part[:-3]
        if whole_part:
            formatted_whole_part = "," + formatted_whole_part

    if len(parts) > 1:
        decimal_part = parts[1]
        formatted_number = f"{formatted_whole_part}.{decimal_part}"
    else:
        formatted_number = formatted_whole_part

    return formatted_number


def lease_formatter(value):
    if value is None:
        return None

    if value < 60:
        return f"{value} days"
    elif 2 <= value // 30 <= 24:
        months = value // 30
        days = value % 30
        return f"{months} months and {days} days"
    else:
        years = value // 365
        months = (value % 365) // 30
        days = (value % 365) % 30
        return f"{years} years, {months} months, and {days} days"


def format_square_meters(value):
    return f"{value} m²"


def format_payment_method(value):
    if value in [method.value for method in PaymentMethod]:
        return value.replace("_", " ").title()
    else:
        return "Unknown"
