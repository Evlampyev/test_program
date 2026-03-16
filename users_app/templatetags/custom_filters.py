from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    """Умножает значение на аргумент"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def star_rating(value):
    """Возвращает HTML со звездами на основе количества задач"""
    try:
        stars_count = value // 10
        if stars_count == 0:
            return ''

        stars_html = ''
        for i in range(stars_count):
            stars_html += '<i class="fas fa-star text-warning" title="10+ задач"></i>'

        # Добавляем полузвезду за остаток
        remainder = value % 10
        if remainder >= 5:
            stars_html += '<i class="fas fa-star-half-alt text-warning" title="5+ задач"></i>'

        return stars_html
    except (TypeError, ValueError):
        return ''


@register.filter
def get_range(value):
    """Возвращает диапазон для цикла"""
    return range(value)
