# для контрольных работ и своих уроков

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import models
from django.contrib import messages
from django.utils import timezone

import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import CollectionForm
from . import CollectionAttempt, Collection, CollectionItem, CollectionAssignment
from ..shared import is_teacher


def collection_list(request):
    """Список подборок"""
    collections = Collection.objects.filter(author=request.user) if request.user.is_authenticated else []

    # Если учитель - показывает свои и публичные
    if request.user.user_type == 'teacher':
        collections = Collection.objects.filter(
            models.Q(author=request.user) | models.Q(is_public=True)
        ).distinct()

    context = {
        'collections': collections,
        'title': 'Мои подборки',
    }
    return render(request, 'task_description_app/collections/collection_list.html', context)


def collection_create(request):
    """Создание новой подборки"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = CollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.author = request.user
            collection.save()
            return redirect('tasks_&_collections:collections:edit', collection_id=collection.id)
    else:
        form = CollectionForm()

    context = {
        'form': form,
        'title': 'Создание подборки',
    }
    return render(request, 'task_description_app/collections/collection_create.html', context)


def collection_edit(request, collection_id):
    """Редактирование подборки (выбор задач)"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    collection = get_object_or_404(Collection, id=collection_id, author=request.user)

    # Получаем все доступные задачи
    from task_description_app.tasks import Task
    all_tasks = Task.objects.all().order_by('id')

    # Получаем задачи уже в подборке
    selected_tasks = collection.collection_items.select_related('task').order_by('order')

    if request.method == 'POST':
        # Обновляем порядок и баллы только для существующих задач
        for item in selected_tasks:
            order = request.POST.get(f'order_{item.id}', '')
            max_score = request.POST.get(f'max_score_{item.id}', '')

            # Проверяем, что значения не пустые
            if order and order.strip():
                try:
                    item.order = int(order)
                except ValueError:
                    pass  # Если не число, оставляем как есть

            if max_score and max_score.strip():
                try:
                    item.max_score = int(max_score)
                except ValueError:
                    pass
            item.save()

        # Добавляем новые задачи через скрытое поле
        selected_tasks_str = request.POST.get('selected_tasks', '')
        if selected_tasks_str:
            task_ids = selected_tasks_str.split(',')
            existing_task_ids = [item.task.id for item in selected_tasks]

            for order_num, task_id in enumerate(task_ids, start=1):
                task_id = task_id.strip()
                if not task_id:
                    continue

                task_id_int = int(task_id)
                if task_id_int not in existing_task_ids:
                    task = get_object_or_404(Task, id=task_id_int)
                    CollectionItem.objects.create(
                        collection=collection,
                        task=task,
                        order=order_num,
                        max_score=10  # Значение по умолчанию
                    )

        # Удаляем задачи, отмеченные для удаления
        remove_tasks_str = request.POST.get('remove_tasks', '')
        if remove_tasks_str:
            remove_ids = [int(id_str) for id_str in remove_tasks_str.split(',') if id_str]
            CollectionItem.objects.filter(id__in=remove_ids).delete()

        return redirect('tasks_&_collections:collections:edit', collection_id=collection.id)

    context = {
        'collection': collection,
        'all_tasks': all_tasks,
        'selected_tasks': selected_tasks,
        'title': f'Редактирование: {collection.title}',
    }
    return render(request, 'task_description_app/collections/collection_edit.html', context)


def collection_detail(request, collection_id):
    """Просмотр подборки"""
    collection = get_object_or_404(Collection, id=collection_id)
    # print("зашли в detail ")
    # Проверяем доступ
    if request.user.user_type == 'teacher':
        if not collection.is_public and collection.author != request.user:
            return redirect('home')
    # print("Пошли дальше")
    # Получаем все задачи в подборке
    items = collection.collection_items.select_related('task').order_by('order')

    # Получаем информацию о попытках ученика
    last_attempt = None
    last_completed_attempt = None
    in_progress_attempt = None

    if request.user.is_authenticated and request.user.user_type == 'student':
        # Все попытки ученика
        attempts = CollectionAttempt.objects.filter(
            collection=collection,
            student=request.user
        ).order_by('-started_at')

        last_attempt = attempts.first()
        last_completed_attempt = attempts.filter(status='completed').first()
        in_progress_attempt = attempts.filter(status='in_progress').first()

    context = {
        'collection': collection,
        'items': items,
        'last_attempt': last_attempt,
        'last_completed_attempt': last_completed_attempt,
        'in_progress_attempt': in_progress_attempt,
        'title': collection.title,
    }
    return render(request, 'task_description_app/collections/collection_detail.html', context)


def start_collection(request, collection_id):
    """Начать выполнение подборки"""
    if request.user.user_type != 'student':
        return redirect('home')

    collection = get_object_or_404(Collection, id=collection_id)

    # Проверяем, есть ли уже завершенная попытка
    completed_attempt = CollectionAttempt.objects.filter(
        collection=collection,
        student=request.user,
        status='completed'
    ).first()

    if completed_attempt:
        messages.warning(request, 'Вы уже успешно выполнили эту контрольную работу. Повторное выполнение невозможно.')
        return redirect('tasks_&_collections:collections:my_assignments')

    # Проверяем, есть ли незавершенная попытка
    in_progress_attempt = CollectionAttempt.objects.filter(
        collection=collection,
        student=request.user,
        status='in_progress'
    ).first()

    if in_progress_attempt:
        messages.info(request, 'Продолжаем выполнение контрольной работы')
        return redirect('tasks_&_collections:collections:attempt', attempt_id=in_progress_attempt.id)

    # 👇 Обновляем статус назначения на 'in_progress'
    assignment = CollectionAssignment.objects.filter(
        collection=collection,
        student=request.user
    ).first()

    if assignment and assignment.status != 'in_progress':
        assignment.status = 'in_progress'
        assignment.save()

    # Создаем новую попытку
    attempt = CollectionAttempt.objects.create(
        collection=collection,
        student=request.user,
        max_score=collection.get_total_score()
    )

    return redirect('tasks_&_collections:collections:attempt', attempt_id=attempt.id)


def collection_attempt(request, attempt_id):
    """Выполнение подборки"""
    attempt = get_object_or_404(CollectionAttempt, id=attempt_id, student=request.user)

    if attempt.status != 'in_progress':
        messages.warning(request, 'Эта работа уже завершена или проверена')
        return redirect('tasks_&_collections:collections:detail', collection_id=attempt.collection.id)

    items = attempt.collection.collection_items.select_related('task').order_by('order')

    context = {
        'attempt': attempt,
        'items': items,
        'title': f'Выполнение: {attempt.collection.title}',
    }
    return render(request, 'task_description_app/collections/collection_attempt.html', context)


@login_required
def assign_collection(request, collection_id):
    """Выдача контрольной работы ученикам"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    collection = get_object_or_404(Collection, id=collection_id, author=request.user)

    if request.method == 'POST':
        # Получаем выбранных учеников
        student_ids = request.POST.getlist('students')
        due_date = request.POST.get('due_date')

        if not student_ids:
            messages.error(request, 'Выберите хотя бы одного ученика')
            return redirect('tasks_&_collections:collections:assign', collection_id=collection.id)

        # Создаем назначения
        for student_id in student_ids:
            from task_description_app.tasks.models import User
            student = get_object_or_404(User, id=student_id, user_type='student')

            # Проверяем, не назначена ли уже
            assignment, created = CollectionAssignment.objects.get_or_create(
                collection=collection,
                student=student,
                defaults={'due_date': due_date if due_date else None}
            )

            if created:
                # Можно добавить уведомление
                from notifications.utils import notify_student_about_assignment
                notify_student_about_assignment(student, collection)

        messages.success(request, f'Контрольная работа выдана {len(student_ids)} ученикам')
        return redirect('tasks_&_collections:collections:detail', collection_id=collection.id)

    # GET запрос - показываем форму выдачи
    students = collection.get_available_students()

    # Группируем по классам
    students_by_class = {}
    for student in students:
        class_name = str(student.student_profile.group.school_class) if student.student_profile.group else "Без класса"
        if class_name not in students_by_class:
            students_by_class[class_name] = []
        students_by_class[class_name].append(student)

    context = {
        'collection': collection,
        'students_by_class': students_by_class,
        'title': f'Выдача: {collection.title}',
    }
    return render(request, 'task_description_app/collections/assign_collection.html', context)


@login_required
def my_assignments(request):
    """Список назначенных КР для ученика"""
    if request.user.user_type != 'student':
        return redirect('teacher_dashboard')

    assignments = CollectionAssignment.objects.filter(
        student=request.user
    ).select_related('collection').order_by('-assigned_at')

    # Получаем все завершенные попытки одним запросом (оптимизация)
    attempts = CollectionAttempt.objects.filter(
        student=request.user,
        status='completed'
    ).order_by('-completed_at')

    # Создаем словарь: collection_id -> последняя попытка
    attempts_dict = {}
    for attempt in attempts:
        if attempt.collection_id not in attempts_dict:
            attempts_dict[attempt.collection_id] = attempt

    # print(assignments)
    # print("*" * 40)
    for assignment in assignments:
        # print("*" * 40)
        # print(f"{assignment.status = }")
        if assignment.is_overdue():
            assignment.status = 'expired'
            assignment.save()

        # Добавляем последнюю завершенную попытку
        assignment.last_completed_attempt = attempts_dict.get(assignment.collection_id)

    context = {
        'assignments': assignments,
        'title': 'Мои задания',

    }
    return render(request, 'task_description_app/collections/my_assignments.html', context)


@login_required
@csrf_exempt
def complete_collection(request, attempt_id):
    """Завершение контрольной работы"""
    attempt = get_object_or_404(CollectionAttempt, id=attempt_id, student=request.user)

    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'Работа уже завершена'}, status=400)

    data = json.loads(request.body)
    results = data.get('results', [])

    total_score = 0
    max_score = attempt.max_score

    # Обновляем результаты
    for result in results:
        task_id = result['task_id']
        is_solved = result.get('is_solved', False)
        code = result.get('code', '')

        if is_solved:
            # Находим задачу в подборке
            item = attempt.collection.collection_items.filter(task_id=task_id).first()
            if item:
                total_score += item.max_score

        # Сохраняем попытку решения задачи
        from task_description_app.tasks import TaskAttempt
        TaskAttempt.objects.create(
            user=request.user,
            real_task_id=task_id,
            code=code,
            is_solved=is_solved,
            status='completed',
            collection_attempt_id=attempt,
        )

    # Обновляем попытку КР
    attempt.score = total_score
    attempt.status = 'completed'
    # print(10 * "-", f"{attempt.status}")
    attempt.completed_at = timezone.now()
    attempt.save()

    # Обновляем статус назначения
    assignment = CollectionAssignment.objects.filter(
        collection=attempt.collection,
        student=request.user
    ).first()

    if assignment and assignment.status != 'completed':
        assignment.status = 'completed'
        assignment.save()

    # Уведомляем учителя
    from notifications.utils import notify_teacher_about_completed_assignment

    notification = notify_teacher_about_completed_assignment(
        teacher=attempt.collection.author,
        student=request.user,
        collection=attempt.collection,
        attempt=attempt
    )

    return JsonResponse({
        'success': True,
        'score': total_score,
        'max_score': max_score,
        'percentage': round((total_score / max_score) * 100) if max_score > 0 else 0
    })


@login_required
@csrf_exempt
def student_request_time_extension(request, collection_id):
    """
    API для отправки запроса учителю о продлении времени на выполнение задания
    """
    # print("*" * 30)
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    # Проверяем, что пользователь - ученик
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Доступ только для учеников'}, status=403)

    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        # print(message)

        # Получаем задание
        from .models import CollectionAssignment
        assignment = get_object_or_404(CollectionAssignment,
                                       collection_id=collection_id,
                                       student=request.user)

        # Получаем учителя (автора коллекции)
        teacher = assignment.collection.author

        # Используем существующую функцию из уведомлений
        from notifications.utils import notify_teacher_about_time_request

        notification = notify_teacher_about_time_request(
            teacher=teacher,
            student=request.user,
            collection=assignment.collection,
            assignment=assignment,
            message=message
        )

        if notification:
            return JsonResponse({
                'success': True,
                'message': 'Запрос отправлен учителю'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось отправить запрос'
            }, status=500)

    except CollectionAssignment.DoesNotExist:
        return JsonResponse({'error': 'Задание не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# collections/views.py
def collection_attempt_results(request, attempt_id):
    """Просмотр результатов завершенной попытки"""
    attempt = get_object_or_404(
        CollectionAttempt,
        id=attempt_id,
        student=request.user,
        status='completed'
    )

    # Получаем все задачи в подборке
    items = attempt.collection.collection_items.select_related('task').order_by('order')

    # Получаем результаты из этой попытки контрольной
    task_results = attempt.task_attempts.all()

    # Создаем словарь: task_id -> результат
    results_dict = {}
    for result in task_results:
        if result.real_task_id not in results_dict:
            results_dict[result.real_task_id] = result.is_solved

    # Создаем список с уже подготовленными данными
    items_with_status = []
    for item in items:
        task_id_str = str(item.task.id)
        items_with_status.append({
            'item': item,
            'task_id': item.task.id,
            'title': item.task.title,
            'max_score': item.max_score,
            'order': item.order,
            'is_solved': results_dict.get(task_id_str, False),
        })

    context = {
        'attempt': attempt,
        'items_with_status': items_with_status,
        'title': f'Результаты: {attempt.collection.title}',
    }
    return render(request, 'task_description_app/collections/collection_results.html', context)


# collections/views.py
def assignment_results(request, assignment_id):
    """Просмотр результатов по назначению (для ученика)"""
    assignment = get_object_or_404(
        CollectionAssignment,
        id=assignment_id,
        student=request.user
    )

    # Находим завершенную попытку
    attempt = CollectionAttempt.objects.filter(
        collection=assignment.collection,
        student=request.user,
        status='completed'
    ).first()

    if not attempt:
        messages.warning(request, 'Нет завершенных попыток')
        return redirect('tasks_&_collections:collections:detail', collection_id=assignment.collection.id)

    return redirect('tasks_&_collections:collections:attempt_results', attempt_id=attempt.id)


@login_required
@user_passes_test(is_teacher)
@require_POST
def collection_delete(request, collection_id):
    """Удаление подборки (только POST запрос)"""

    collection = get_object_or_404(Collection, id=collection_id, author=request.user)
    collection_title = collection.title

    try:
        # Удаляем все связанные объекты
        collection.collection_items.all().delete()
        collection.attempts.all().delete()
        collection.assignments.all().delete()
        collection.delete()

        messages.success(request, f'Подборка "{collection_title}" успешно удалена!')

    except Exception as e:
        messages.error(request, f'Ошибка при удалении: {str(e)}')

    return redirect('tasks_&_collections:collections:list')
