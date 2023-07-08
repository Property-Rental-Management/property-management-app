from os import path


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
