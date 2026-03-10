from django import template

register = template.Library()


@register.filter
def pluralize_ru(value, arg):
    """
    Универсальное склонение для русских слов.
    Использование:
        {{ count|pluralize_ru:"ученик,ученика,учеников" }}
        {{ count|pluralize_ru:"задача,задачи,задач" }}
        {{ count|pluralize_ru:"попытка,попытки,попыток" }}
    """
    try:
        count = int(value)
        forms = arg.split(',')
        if len(forms) != 3:
            return f"{count} {arg}"

        last_two = count % 100
        last_digit = count % 10

        if 11 <= last_two <= 19:
            return f"{count} {forms[2]}"
        elif last_digit == 1:
            return f"{count} {forms[0]}"
        elif 2 <= last_digit <= 4:
            return f"{count} {forms[1]}"
        else:
            return f"{count} {forms[2]}"
    except (ValueError, TypeError):
        return f"{value} {arg}"
