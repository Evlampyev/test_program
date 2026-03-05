from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

from task_description_app.models import Task, TaskAttempt
from .forms import StudentRegistrationForm, LoginForm, AssignTeacherForm
from .models import User, StudentProfile, Group, SchoolClass


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
        ).select_related('student_profile')

    context = {
        'groups': groups,
    }
    return render(request, 'users_app/th_dashboard.html', context)


def get_task_level(task_id):
    """
    Определяет уровень задачи по её ID
    """
    try:
        task = Task.objects.get(id=task_id)
        return task.difficulty.display_name
    except Task.DoesNotExist:
        return 'Неизвестно'


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


# Просмотр учеников группы (для учителя)
@login_required
def group_students(request, group_id):
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    students = User.objects.filter(
        user_type='student',
        student_profile__group=group
    ).select_related('student_profile')

    context = {
        'group': group,
        'students': students,
    }
    return render(request, 'users_app/group_students.html', context)


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
