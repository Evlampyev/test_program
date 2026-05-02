# task_description_app/templatetags/dict_extras.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    return dictionary.get(key)


@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    try:
        return dictionary.get(key, False)
    except (AttributeError, TypeError):
        return False
