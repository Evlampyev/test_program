# views.py (приложение tasks)
import os
import re
import textwrap


from django.db.models import Max
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.db import models
from django.contrib import messages
import markdown
import json
import logging

from .forms import TaskAddForm, TaskContentForm ,CollectionForm, CollectionItemForm
from .models import Task, DifficultyLevel, ClassStructure, TaskPlacement, CollectionAttempt, Collection, CollectionItem, \
    CollectionAssignment, User
from .utils import get_task_files

logger = logging.getLogger(__name__)


def build_tree_structure():
    """
    Строит дерево для отображения на основе ClassStructure и TaskPlacement
    """
    root_nodes = ClassStructure.objects.filter(parent=None).order_by('name')

    def build_node(node):
        children = []
        for child in node.children.all().order_by('name'):
            children.append(build_node(child))

        # Получаем задачи в этом узле
        tasks = TaskPlacement.objects.filter(
            structure_node=node
        ).select_related('task').order_by('id')

        # Формируем список задач в формате для дерева
        task_list = []
        for placement in tasks:
            task_list.append({
                'id': placement.task.id,
                'name': f"Задача {placement.task.id}",
                'title': placement.task.title,
                'task_id': placement.task.id,
            })

        # Возвращаем узел в формате, который ожидает renderTree
        return {
            'name': node.name,
            'children': children,
            'tasks': task_list,
            'level': node.level,
        }

    tree_data = []
    for node in root_nodes:
        tree_data.append(build_node(node))

    return tree_data


def get_structure(request):
    """API для получения структуры дерева"""
    structure = build_tree_structure()
    return JsonResponse({'structure': structure})


def task_list(request):
    """Страница со списком всех задач"""
    tasks = Task.objects.all()

    # Получаем структуру для дерева
    tree_data = build_tree_structure()

    # Подсчитываем общее количество задач
    total_tasks = Task.objects.count()

    context = {
        'tasks': tasks,
        'title': 'Список задач',
        'tree_data': json.dumps(tree_data),  # Передаем как JSON строку
        'total_tasks': total_tasks,
    }
    return render(request, 'task_description_app/task_list.html', context)


def render_markdown_without_empty_blocks(md_content):
    """Конвертирует Markdown в HTML и удаляет пустые блоки кода"""
    html_content = markdown.markdown(md_content, extensions=['extra'])
    html_content = re.sub(r'<pre><code[^>]*>\s*</code></pre>\n?', '', html_content)
    return html_content


def task_detail(request, task_id):
    """Отображение конкретной задачи с Markdown"""
    task = get_object_or_404(Task, id=task_id)

    # Получаем файлы задачи
    task_files = get_task_files(task_id)
    md_content = ""

    # Читаем task.md
    if os.path.exists(task_files['md']):
        with open(task_files['md'], 'r', encoding='utf-8') as f:
            md_content = f.read()

    html_content = render_markdown_without_empty_blocks(md_content)

    # Получаем загруженную программу
    from task_description_app.models import UploadedProgram
    uploaded_program = None
    if request.user.is_authenticated:
        uploaded_program = UploadedProgram.objects.filter(
            task=task,
            user=request.user
        ).order_by('-upload_time').first()

    context = {
        'task': task,
        'md_html': html_content,
        'uploaded_program': uploaded_program,
        'title': task.title
    }
    return render(request, 'task_description_app/task_detail.html', context)


def get_task_info(request, task_id):
    """API для получения информации о задаче"""
    task = get_object_or_404(Task, id=task_id)
    task_files = get_task_files(task_id)

    # Читаем содержимое task.md
    md_content = ""
    if os.path.exists(task_files['md']):
        with open(task_files['md'], 'r', encoding='utf-8') as f:
            md_content = f.read()

    return JsonResponse({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'difficulty': task.difficulty_id,
        'md_content': md_content,
        'test_files': task.test_files,
    })


def clean_text(text):
    """Очищает текст от лишних пробелов"""
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


@login_required
def task_add(request):
    """Страница добавления новой задачи"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    if request.method == 'POST':
        task_form = TaskAddForm(request.POST)
        content_form = TaskContentForm(request.POST)
        test_count = int(request.POST.get('test_count', 0))

        if task_form.is_valid() and content_form.is_valid() and test_count > 0:
            try:
                # Получаем данные из формы
                class_name = task_form.cleaned_data['class_name'].strip()
                topic = task_form.cleaned_data['topic'].strip()
                lesson = task_form.cleaned_data['lesson'].strip()
                level = task_form.cleaned_data['level']
                task_folder = task_form.cleaned_data['task_folder'].strip()

                # Создаем задачу в БД
                task = task_form.save(commit=False)
                task.created_by = request.user
                task.save()

                # СОЗДАЕМ ПАПКУ ДЛЯ ЗАДАЧИ В НОВОМ МЕСТЕ (tasks/ID/)
                task_dir = os.path.join(settings.TASKS_ROOT, 'tasks', str(task.id))
                os.makedirs(task_dir, exist_ok=True)

                # 1. Сохраняем task.md
                md_content = clean_text(content_form.cleaned_data['task_md_content'])
                with open(os.path.join(task_dir, 'task.md'), 'w', encoding='utf-8') as f:
                    f.write(md_content)

                # 2. Сохраняем task.py
                py_content = content_form.cleaned_data['task_py_content']
                with open(os.path.join(task_dir, 'task.py'), 'w', encoding='utf-8') as f:
                    f.write(py_content)

                # 3. Создаем тесты
                test_files = []
                for i in range(1, test_count + 1):
                    input_data = request.POST.get(f'test_{i}_input', '').strip()
                    output_data = request.POST.get(f'test_{i}_output', '').strip()

                    if input_data:
                        in_path = os.path.join(task_dir, f'test{i}.in')
                        with open(in_path, 'w', encoding='utf-8') as f:
                            f.write(input_data.replace('\r\n', '\n').replace('\r', '\n'))
                        test_files.append(f'test{i}.in')

                    if output_data:
                        out_path = os.path.join(task_dir, f'test{i}.out')
                        with open(out_path, 'w', encoding='utf-8') as f:
                            f.write(output_data.replace('\r\n', '\n').replace('\r', '\n'))
                        test_files.append(f'test{i}.out')

                # 4. Сохраняем список тестов
                task.test_files = test_files
                task.save(update_fields=['test_files'])

                # 5. СОЗДАЕМ СВЯЗИ В СТРУКТУРЕ
                # Находим или создаем узлы структуры
                class_node, _ = ClassStructure.objects.get_or_create(
                    name=class_name,
                    level=0,
                    parent=None
                )

                topic_node, _ = ClassStructure.objects.get_or_create(
                    name=topic,
                    level=1,
                    parent=class_node
                )

                lesson_node, _ = ClassStructure.objects.get_or_create(
                    name=lesson,
                    level=2,
                    parent=topic_node
                )

                level_node, _ = ClassStructure.objects.get_or_create(
                    name=level,
                    level=3,
                    parent=lesson_node
                )

                # Создаем связь задачи с узлом уровня
                TaskPlacement.objects.get_or_create(
                    task=task,
                    structure_node=level_node
                )

                return JsonResponse({
                    'success': True,
                    'message': 'Задача успешно создана!',
                    'task_id': task.id,
                    'task_title': task.title or f"Задача #{task.id}",
                    'path': f"tasks/{task.id}"  # Возвращаем новый путь
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Ошибка при создании задачи: {str(e)}'
                }, status=500)
        else:
            errors = {}
            errors.update(task_form.errors)
            errors.update(content_form.errors)
            if test_count == 0:
                errors['tests'] = ['Добавьте хотя бы один тест']
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

    else:
        # GET запрос - отображаем форму
        task_form = TaskAddForm()
        content_form = TaskContentForm()

        # Шаблон для task.md
        default_md = textwrap.dedent('''\
                    ## Название задачи
                    Описание задачи...
                    <table style="width: auto; margin: auto"> 
                        <tr style="text-align: center">
                            <th><b><i>Формат ввода</i></b></th>
                            <th><b><i>Формат вывода</i></b></th>
                        </tr>
                        <tr style="vertical-align: top">
                            <td>Строка данных</td>
                            <td style="vertical-align: top">Строка данных</td>
                        </tr>
                    </table> 

                    ### Пример
                    <table style="width: auto; margin: auto"> 
                        <tr style="text-align: center">
                            <th><b><i>Ввод</i></b></th>
                            <th><b><i>Вывод</i></b></th>
                        </tr>
                        <tr style="vertical-align: top">
                            <td>Нечто</td>
                            <td>Что-то</td>
                        </tr>
                    </table>
                ''')
        content_form.fields['task_md_content'].initial = default_md

        # Шаблон для task.py
        default_py = '''def solve():
    data = input().split()
    # Ваш код
    result = 0
    print(result)

if __name__ == "__main__":
    solve()'''
        content_form.fields['task_py_content'].initial = default_py

        difficulty_levels = DifficultyLevel.objects.all()
        max_id = Task.objects.aggregate(Max('id'))['id__max'] or 0

        context = {
            'task_form': task_form,
            'content_form': content_form,
            'difficulty_levels': difficulty_levels,
            'task_id': max_id + 1,
        }
        return render(request, 'task_description_app/task_add.html', context)

# для контрольных работ и своих уроков
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
    return render(request, 'task_description_app/collection_list.html', context)


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
            return redirect('collection_edit', collection_id=collection.id)
    else:
        form = CollectionForm()

    context = {
        'form': form,
        'title': 'Создание подборки',
    }
    return render(request, 'task_description_app/collection_create.html', context)


def collection_edit(request, collection_id):
    """Редактирование подборки (выбор задач)"""
    if request.user.user_type != 'teacher':
        return redirect('student_dashboard')

    collection = get_object_or_404(Collection, id=collection_id, author=request.user)

    # Получаем все доступные задачи
    all_tasks = Task.objects.all().order_by('id')

    # Получаем задачи уже в подборке
    selected_tasks = collection.collection_items.select_related('task').order_by('order')

    if request.method == 'POST':
        # Обновляем порядок и баллы
        for item in selected_tasks:
            order = request.POST.get(f'order_{item.id}')
            max_score = request.POST.get(f'max_score_{item.id}')
            if order:
                item.order = int(order)
            if max_score:
                item.max_score = int(max_score)
            item.save()

        # Добавляем новые задачи
        task_ids = request.POST.getlist('selected_tasks')[0].split(',')
        # print(f"{task_ids = }")
        for i, task_id in enumerate(task_ids):
            task = get_object_or_404(Task, id=int(task_id))
            CollectionItem.objects.get_or_create(
                collection=collection,
                task=task,
                defaults={'order': selected_tasks.count() + i + 1}
            )

        # Удаляем задачи, отмеченные для удаления
        if request.POST.get('remove_tasks'):
            remove_ids = request.POST.getlist('remove_tasks')
            CollectionItem.objects.filter(id__in=remove_ids).delete()

        return redirect('tasks:collection_edit', collection_id=collection.id)

    context = {
        'collection': collection,
        'all_tasks': all_tasks,
        'selected_tasks': selected_tasks,
        'title': f'Редактирование: {collection.title}',
    }
    return render(request, 'task_description_app/collection_edit.html', context)


def collection_detail(request, collection_id):
    """Просмотр подборки"""
    collection = get_object_or_404(Collection, id=collection_id)

    # Проверяем доступ
    if not collection.is_public and collection.author != request.user:
        return redirect('home')

    # Получаем все задачи в подборке
    items = collection.collection_items.select_related('task').order_by('order')

    # Проверяем, есть ли попытка ученика
    attempt = None
    if request.user.is_authenticated and request.user.user_type == 'student':
        attempt = CollectionAttempt.objects.filter(
            collection=collection,
            student=request.user
        ).first()

    context = {
        'collection': collection,
        'items': items,
        'attempt': attempt,
        'title': collection.title,
    }
    return render(request, 'task_description_app/collection_detail.html', context)


def start_collection(request, collection_id):
    """Начать выполнение подборки"""
    if request.user.user_type != 'student':
        return redirect('home')

    collection = get_object_or_404(Collection, id=collection_id)

    # Создаем новую попытку
    attempt = CollectionAttempt.objects.create(
        collection=collection,
        student=request.user,
        max_score=collection.get_total_score()
    )

    return redirect('collection_attempt', attempt_id=attempt.id)


def collection_attempt(request, attempt_id):
    """Выполнение подборки"""
    attempt = get_object_or_404(CollectionAttempt, id=attempt_id, student=request.user)

    if attempt.status != 'in_progress':
        return redirect('collection_detail', collection_id=attempt.collection.id)

    items = attempt.collection.collection_items.select_related('task').order_by('order')

    context = {
        'attempt': attempt,
        'items': items,
        'title': f'Выполнение: {attempt.collection.title}',
    }
    return render(request, 'task_description_app/collection_attempt.html', context)


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
            return redirect('assign_collection', collection_id=collection.id)

        # Создаем назначения
        for student_id in student_ids:
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
        return redirect('tasks:collection_detail', collection_id=collection.id)

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
    return render(request, 'task_description_app/assign_collection.html', context)


@login_required
def my_assignments(request):
    """Список назначенных КР для ученика"""
    if request.user.user_type != 'student':
        return redirect('teacher_dashboard')

    assignments = CollectionAssignment.objects.filter(
        student=request.user
    ).select_related('collection').order_by('-assigned_at')

    context = {
        'assignments': assignments,
        'title': 'Мои задания',
    }
    return render(request, 'task_description_app/my_assignments.html', context)

