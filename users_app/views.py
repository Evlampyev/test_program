from datetime import datetime, timedelta
import string
import random

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone

from task_description_app.models import Task, TaskAttempt
from .forms import StudentRegistrationForm, LoginForm, AssignTeacherForm
from .models import User, StudentProfile, Group, SchoolClass
from manage import logger

User = get_user_model()


# Регистрация ученика
def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'users_app/student_register.html', {'form': form})


# Вход для всех
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)

                # Перенаправление в зависимости от типа пользователя
                if user.user_type == 'teacher':
                    return redirect('teacher_dashboard')
                else:
                    return redirect('student_dashboard')
    else:
        form = LoginForm()

    return render(request, 'users_app/login.html', {'form': form})


# Выход
def user_logout(request):
    logout(request)
    return redirect('login')


# Личный кабинет учителя
@login_required
def teacher_dashboard(request):
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    # Получаем группы учителя
    groups = Group.objects.filter(teacher=request.user).select_related('school_class')

    # Для каждой группы добавляем учеников
    for group in groups:
        group.students_list = User.objects.filter(
            user_type='student',
            student_profile__group=group
        ).select_related('student_profile').order_by('last_name', 'first_name')

    context = {'groups': groups}
    return render(request, 'users_app/th_dashboard.html', context)


def get_task_title(task_id: int) -> str:
    """
    Определяет Заголовок задачи
    :param task_id:
    :return: title
    """
    try:
        task = Task.objects.get(id=task_id)
        return task.title
    except Task.DoesNotExist:
        return 'Нет данных'


def get_task_level(task_id: int) -> str:
    """
    Определяет уровень задачи по её ID
    :param task_id:
    :return: A, B, C or D
    """
    try:
        task = Task.objects.get(id=task_id)
        return task.difficulty.display_name[-1]
    except Task.DoesNotExist:
        return 'Неизвестно'


# def get_task_level_from_db(task_id):
#     """Получает уровень задачи из БД"""
#     try:
#         task = Task.objects.get(id=task_id)
#         return task.difficulty.display_name if task.difficulty else 'Не определен'
#     except Task.DoesNotExist:
#         return 'Не определен'


@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        return redirect('teacher_dashboard')

    try:
        profile = request.user.student_profile
        group = profile.group
        # Получаем одноклассников
        classmates = StudentProfile.objects.filter(group=group).exclude(user=request.user).select_related('user')

        if group:
            # Получаем всех учеников группы
            group_students = User.objects.filter(
                user_type='student',
                student_profile__group=group
            ).select_related('student_profile')
            rating_data = []

            for student in group_students:
                # Получаем количество решенных задач (уникальных)
                solved_count = TaskAttempt.objects.filter(user=student, is_solved=True).values(
                    'task_id').distinct().count()

                # Получаем общее количество попыток
                total_attempts = TaskAttempt.objects.filter(user=student).count()

                # Получаем количество неудачных попыток
                failed_attempts = TaskAttempt.objects.filter(
                    user=student,
                    is_solved=False
                ).count()

                rating_data.append({
                    'user': student,
                    'solved_count': solved_count,
                    'total_attempts': total_attempts,
                    'failed_attempts': failed_attempts,
                    'full_name': f"{student.last_name} {student.first_name}",
                })

                # Сортируем:
                # 1. По количеству решенных задач (по убыванию)
                # 2. Если одинаково, то по количеству попыток (по возрастанию)
                rating_data.sort(
                    key=lambda x: (-x['solved_count'], x['total_attempts'])
                )

                # Добавляем место
                for idx, item in enumerate(rating_data, 1):
                    item['place'] = idx
                    # Определяем цвет медали
                    if idx == 1:
                        item['badge_class'] = 'bg-warning text-dark'  # золото
                    elif idx == 2:
                        item['badge_class'] = 'bg-secondary'  # серебро
                    elif idx == 3:
                        item['badge_class'] = 'bg-danger'  # бронза
                    else:
                        item['badge_class'] = 'bg-light text-dark'

                # Находим место текущего ученика
                current_user_place = None
                for item in rating_data:
                    if item['user'].id == request.user.id:
                        current_user_place = item['place']
                        break

        else:
            rating_data = []
            current_user_place = None

        # ПОЛУЧАЕМ ПОСЛЕДНИЕ ЗАДАЧИ УЧЕНИКА

        last_attempts = TaskAttempt.objects.filter(
            user=request.user
        ).order_by('-attempt_time')[:10]  # последние 10 попыток

        # Группируем по задачам, чтобы получить уникальные задачи
        # и для каждой задачи собираем статистику
        tasks_stats = []
        seen_tasks = set()

        for attempt in last_attempts:
            task_id = attempt.real_task_id  # или attempt.task.id если есть связь

            if task_id not in seen_tasks:
                seen_tasks.add(task_id)

                # Получаем все попытки по этой задаче
                task_attempts = TaskAttempt.objects.filter(
                    user=request.user,
                    real_task_id=task_id
                ).order_by('-attempt_time')

                # Определяем статус (решена или нет)
                is_solved = task_attempts.filter(is_solved=True).exists()

                # Получаем информацию о задаче
                # Если есть модель Task, свяжите её
                task_info = {
                    'id': task_id,
                    'title': f'Задача #{task_id}',  # Заглушка, замените на реальное название
                    'level': get_task_level(task_id),  # Функция для получения уровня
                    'attempts_count': task_attempts.count(),
                    'is_solved': is_solved,
                    'last_attempt': task_attempts.first(),
                    'status_class': 'status-done' if is_solved else 'status-pending',
                    'status_text': 'Решено' if is_solved else 'В процессе',
                }
                tasks_stats.append(task_info)

                if len(tasks_stats) >= 5:  # Хотим только 3 последние задачи
                    break

    except StudentProfile.DoesNotExist:
        profile = None
        group = None
        classmates = []
        tasks_stats = []

    # Общая статистика
    total_attempts = TaskAttempt.objects.filter(user=request.user).count()
    solved_tasks_count = TaskAttempt.objects.filter(
        user=request.user,
        is_solved=True
    ).values('task_id').distinct().count()
    if total_attempts > 0:
        success_rate = round((solved_tasks_count / total_attempts) * 100)
    else:
        success_rate = 0
    context = {
        'profile': profile,
        'group': group,
        'classmates': classmates,
        'tasks_stats': tasks_stats,  # данные для шаблона
        'total_attempts': total_attempts,
        'solved_tasks_count': solved_tasks_count,
        'success_rate': success_rate,
        'rating_data': rating_data,
    }
    return render(request, 'users_app/st_dashboard.html', context)


# Вспомогательная функция для форматирования последнего входа
def format_last_login(last_login):
    if not last_login:
        return "никогда"

    time_diff = timezone.now() - last_login

    if time_diff < timedelta(minutes=1):
        return "только что"
    elif time_diff < timedelta(hours=1):
        minutes = int(time_diff.total_seconds() / 60)
        return f"{minutes} мин. назад"
    elif time_diff < timedelta(days=1):
        hours = int(time_diff.total_seconds() / 3600)
        return f"{hours} ч. назад"
    elif time_diff < timedelta(days=7):
        days = time_diff.days
        return f"{days} д. назад"
    else:
        return last_login.strftime("%d.%m.%Y %H:%M")


# Просмотр учеников группы (для учителя)
@login_required
def group_students(request, group_id):
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    # Получаем группу и проверяем, что учитель имеет к ней доступ
    group = get_object_or_404(Group, id=group_id, teacher=request.user)

    # Получаем всех учеников группы с дополнительной статистикой
    students = User.objects.filter(
        user_type='student',
        student_profile__group=group
    ).select_related('student_profile')

    # Для каждого ученика собираем статистику
    students_data = []
    for student in students:
        # Получаем все попытки ученика
        all_attempts = TaskAttempt.objects.filter(user=student)

        # Количество решенных задач (уникальных)
        solved_count = all_attempts.filter(
            is_solved=True
        ).values('task_id').distinct().count()

        # Количество задач "в процессе" (пытался, но не решил)
        # Находим все задачи, которые ученик пробовал решать
        attempted_tasks = all_attempts.values('task_id').distinct()

        # Из них находим те, которые не решены
        in_progress_count = 0
        for task_data in attempted_tasks:
            task_id = task_data['task_id']
            has_solved = all_attempts.filter(
                task_id=task_id,
                is_solved=True
            ).exists()
            if not has_solved:
                in_progress_count += 1

        # Точность (процент успешных попыток)
        total_attempts = all_attempts.count()
        successful_attempts = all_attempts.filter(is_solved=True).count()

        if total_attempts > 0:
            accuracy = round((successful_attempts / total_attempts) * 100)
        else:
            accuracy = 0

        # Последний вход (берем из last_login пользователя)
        last_login_display = format_last_login(student.last_login)

        # Максимальное количество задач для прогресс-бара
        # Можно взять общее количество задач в этом уровне или установить константу
        max_tasks = 20  # или рассчитать динамически

        students_data.append({
            'student': student,
            'solved_count': solved_count,
            'in_progress_count': in_progress_count,
            'accuracy': accuracy,
            # 'last_login': last_login,
            'last_login_display': last_login_display,
            'progress_width': min(100, int((solved_count / max_tasks) * 100)),
            'max_tasks': max_tasks,
        })

    # Сортируем учеников (например, по фамилии)
    students_data.sort(key=lambda x: (x['student'].last_name, x['student'].first_name))
    # print(f"{students_data = }")
    context = {
        'group': group,
        'students_data': students_data,
    }
    return render(request, 'users_app/group_students.html', context)


@login_required
def get_student_stats(request, student_id):
    """API для получения статистики ученика (только за последнюю неделю)"""
    if request.user.user_type != 'teacher':
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    try:
        student = User.objects.get(id=student_id, user_type='student')
    except User.DoesNotExist:
        return JsonResponse({'error': 'Ученик не найден'}, status=404)

    # Определяем дату недельной давности
    week_ago = timezone.now() - timedelta(days=7)

    # Получаем попытки за последнюю неделю
    recent_attempts = TaskAttempt.objects.filter(
        user=student,
        attempt_time__gte=week_ago
    ).order_by('-attempt_time')

    # Собираем уникальные задачи за неделю
    tasks_data = []
    seen_tasks = set()

    for attempt in recent_attempts:
        task_id = attempt.real_task_id
        if task_id not in seen_tasks:
            seen_tasks.add(task_id)

            # Получаем все попытки по этой задаче за неделю
            task_attempts = recent_attempts.filter(real_task_id=task_id)
            attempts_count = task_attempts.count()

            # Проверяем, решена ли задача за эту неделю
            is_solved = task_attempts.filter(is_solved=True).exists()

            task_level = get_task_level(task_id)
            # task_level = get_task_level_from_db(task_id)

            tasks_data.append({
                'id': task_id,
                'title': f'Задача #{task_id}',
                'level': task_level,  # Добавляем уровень
                'attempts': attempts_count,
                'is_solved': is_solved,
                'last_attempt': attempt.attempt_time.strftime('%d.%m.%Y %H:%M'),
                'status_text': '✅ Решена' if is_solved else '🔄 В процессе',
                'status_class': 'success' if is_solved else 'warning',
            })
    # print(f"{tasks_data = }")
    return JsonResponse({
        'student_name': f"{student.last_name} {student.first_name}",
        'tasks': tasks_data,
        'total_tasks': len(tasks_data),
    })


@login_required
def student_tasks(request, student_id):
    """Страница со списком задач ученика"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    # Получаем ученика
    student = get_object_or_404(User, id=student_id, user_type='student')

    # Получаем все попытки ученика
    all_attempts = TaskAttempt.objects.filter(user=student).order_by('-attempt_time')

    # Группируем по задачам
    tasks_data = []
    seen_tasks = set()

    for attempt in all_attempts:
        task_id = attempt.real_task_id
        if task_id not in seen_tasks:
            seen_tasks.add(task_id)

            # Все попытки по этой задаче
            task_attempts = all_attempts.filter(real_task_id=task_id)

            # Статистика
            total_attempts = task_attempts.count()
            successful_attempts = task_attempts.filter(is_solved=True).count()
            is_solved = successful_attempts > 0

            # Дата первой и последней попытки
            first_attempt = task_attempts.last()
            last_attempt = task_attempts.first()

            # Определяем уровень задачи (из вашей логики)
            task_level = get_task_level(task_id)  # реализуйте эту функцию

            tasks_data.append({
                'id': task_id,
                'title': f'Задача #{task_id}',
                'level': task_level,
                'total_attempts': total_attempts,
                'successful_attempts': successful_attempts,
                'is_solved': is_solved,
                'first_attempt': first_attempt.attempt_time if first_attempt else None,
                'last_attempt': last_attempt.attempt_time if last_attempt else None,
                'status_class': 'success' if is_solved else 'warning',
                'status_text': 'Решена' if is_solved else 'В процессе',
                'success_rate': round((successful_attempts / total_attempts * 100)) if total_attempts > 0 else 0,
            })

    # Сортируем задачи (сначала последние активные)
    tasks_data.sort(key=lambda x: x['last_attempt'] or datetime.min, reverse=True)

    # Общая статистика
    total_tasks = len(tasks_data)
    solved_tasks = sum(1 for t in tasks_data if t['is_solved'])
    in_progress_tasks = total_tasks - solved_tasks
    total_attempts = all_attempts.count()

    context = {
        'student': student,
        'tasks_data': tasks_data,
        'total_tasks': total_tasks,
        'solved_tasks': solved_tasks,
        'in_progress_tasks': in_progress_tasks,
        'total_attempts': total_attempts,
    }

    return render(request, 'users_app/teacher/student_tasks.html', context)


# Для администратора: назначение учителя на группу
@staff_member_required
def assign_teacher(request):
    if request.method == 'POST':
        form = AssignTeacherForm(request.POST)
        if form.is_valid():
            teacher = form.cleaned_data['teacher']
            school_class = form.cleaned_data['school_class']
            group_number = form.cleaned_data['group_number']

            # Получаем или создаем группу
            group, created = Group.objects.get_or_create(
                school_class=school_class,
                number=group_number,
                defaults={'teacher': teacher}
            )

            # Если группа уже существовала, обновляем учителя
            if not created:
                old_teacher = group.teacher
                group.teacher = teacher
                group.save()
                messages.success(request,
                                 f'Учитель {teacher.last_name} {teacher.first_name} назначен на группу {school_class.number}{school_class.letter} - {group_number}')
            else:
                messages.success(request,
                                 f'Группа создана и назначена учителю {teacher.last_name} {teacher.first_name}')

            return redirect('assign_teacher')
    else:
        form = AssignTeacherForm()

    # Получаем все необходимые данные для шаблона
    teachers = User.objects.filter(user_type='teacher').select_related('teacher_profile')
    classes = SchoolClass.objects.all().order_by('number', 'letter')
    assignments = Group.objects.filter(teacher__isnull=False).select_related('school_class', 'teacher')

    context = {
        'form': form,
        'teachers': teachers,
        'classes': classes,
        'assignments': assignments,
        'teachers_count': teachers.count(),
        'classes_count': classes.count(),
        'total_groups': Group.objects.count(),
    }
    return render(request, 'users_app/assign_teacher.html', context)


@csrf_exempt  # ТОЛЬКО ДЛЯ ОТЛАДКИ!
@login_required
def reset_password(request, student_id):
    """Сброс пароля ученика"""
    logger.info(f"Запрос на сброс пароля для ученика {student_id} от пользователя {request.user.username}")

    # Проверка метода
    if request.method != 'POST':
        logger.warning(f"Неверный метод: {request.method}")
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    # Проверка прав доступа
    if request.user.user_type != 'teacher':
        logger.warning(f"Пользователь {request.user.username} не является учителем")
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    try:
        User = get_user_model()
        student = User.objects.get(id=student_id, user_type='student')
        logger.info(f"Найден ученик: {student.last_name} {student.first_name}")

        # Генерируем новый пароль
        new_password = generate_random_password()
        logger.info(f"Сгенерирован новый пароль для {student.username}")

        # Устанавливаем новый пароль
        student.set_password(new_password)
        student.save()
        logger.info(f"Пароль успешно изменен для {student.username}")

        return JsonResponse({
            'success': True,
            'new_password': new_password,
            'message': f'Пароль для {student.last_name} {student.first_name} сброшен'
        })

    except User.DoesNotExist:
        logger.error(f"Ученик с id {student_id} не найден")
        return JsonResponse({'error': 'Ученик не найден'}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при сбросе пароля: {str(e)}")
        return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)


def generate_random_password(length=8):
    """Генерирует случайный пароль"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
