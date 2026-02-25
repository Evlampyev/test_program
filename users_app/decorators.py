# decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def teacher_required(view_func):
    """Декоратор для проверки, что пользователь - учитель"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.user_type != 'teacher':
            messages.error(request, 'Доступ запрещен. Требуются права учителя.')
            return redirect('student_dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def student_required(view_func):
    """Декоратор для проверки, что пользователь - ученик"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.user_type != 'student':
            messages.error(request, 'Доступ запрещен. Требуются права ученика.')
            return redirect('teacher_dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


class TeacherRequiredMixin:
    """Mixin для class-based views"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.user_type != 'teacher':
            messages.error(request, 'Доступ запрещен. Требуются права учителя.')
            return redirect('student_dashboard')

        return super().dispatch(request, *args, **kwargs)
