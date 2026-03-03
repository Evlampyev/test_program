from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

from task_description_app.models import Task
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


# Личный кабинет ученика
@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        return redirect('teacher_dashboard')

    try:
        profile = request.user.student_profile
        # print(f"{profile=}")
        group = profile.group
        # Получаем одноклассников (учеников из той же группы)
        classmates = StudentProfile.objects.filter(group=group).exclude(user=request.user).select_related('user')
        print(f"{classmates=}")
    except StudentProfile.DoesNotExist:
        profile = None
        group = None
        classmates = []

    # Получаем список решенных задач (реальные ID)
    solved_task_ids = profile.get_solved_tasks()
    print(f"{solved_task_ids=}")

    # Если нужно получить полные объекты задач
    solved_tasks = Task.objects.filter(id__in=solved_task_ids)

    # # Проверяем, решена ли конкретная задача
    # task_id = 34  # реальный ID задачи
    # is_solved = profile.is_task_solved(task_id)

    context = {
        'profile': profile,
        'group': group,
        'classmates': classmates,
        'solved_task_ids': solved_task_ids,
        'solved_tasks': solved_tasks,
        'solved_count': profile.get_solved_tasks_count(),
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
