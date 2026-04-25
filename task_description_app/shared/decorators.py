# shared/decorators.py
from django.contrib.auth.decorators import user_passes_test

def is_teacher(user):
    """Проверка, является ли пользователь учителем"""
    return user.is_authenticated and user.user_type == 'teacher'

def teacher_required(view_func):
    """Декоратор для доступа только учителям"""
    return user_passes_test(is_teacher)(view_func)