# views.py (приложение tasks)
from datetime import datetime
import os
import re
import textwrap
import mimetypes
import pytz

from django.db.models import Max
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.http import JsonResponse, HttpResponse, Http404
from django.db import models
from django.contrib import messages
from django.utils import timezone
import markdown
import json
from django.views.decorators.csrf import csrf_exempt

from .forms import TaskAddForm, TaskContentForm, CollectionForm, TaskEditForm
from .models import Task, DifficultyLevel, ClassStructure, TaskPlacement, CollectionAttempt, Collection, CollectionItem, \
    CollectionAssignment, User, TaskAttempt, UploadedProgram
from .utils import create_uploaded_file_from_code, get_task_files
from manage import logger


def is_teacher(user):
    return user.is_authenticated and user.user_type == 'teacher'


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


def render_markdown_without_empty_blocks(md_content, task_id):
    """Конвертирует Markdown в HTML и удаляет пустые блоки кода"""
    # Сначала обрабатываем изображения в Markdown
    md_content_with_images = process_markdown_images(md_content, task_id)

    # Затем конвертируем в HTML
    html_content = markdown.markdown(md_content_with_images, extensions=['extra'])

    # Удаляем пустые блоки кода
    html_content = re.sub(r'<pre><code[^>]*>\s*</code></pre>\n?', '', html_content)

    return html_content


def process_markdown_images(md_content, task_id):
    """
    Обрабатывает изображения в Markdown, заменяя пути на правильные URL
    """
    lines = md_content.split('\n')
    new_lines = []

    for line in lines:
        # Ищем изображения в формате ![alt](img.png)
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

        def replace_img(match):
            alt = match.group(1)
            src = match.group(2)

            # Если это наше изображение img.png
            if src == 'img.png' or src.endswith('.png') or src.endswith('.jpg'):
                return f'<img class="img-right" src="/tasks/task/{task_id}/image/{src}" alt="{alt}">'
            return match.group(0)

        new_line = re.sub(img_pattern, replace_img, line)
        new_lines.append(new_line)

    return '\n'.join(new_lines)


def render_markdown_with_images(md_content, task_id):
    """Устаревшая функция, оставлена для совместимости"""
    return process_markdown_images(md_content, task_id)


def get_task_info(request, task_id):
    """API для получения информации о задаче"""
    task = get_object_or_404(Task, id=task_id)
    task_files = get_task_files(task_id)

    # Читаем содержимое task.md
    md_content = ""
    if os.path.exists(task_files['md']):
        with open(task_files['md'], 'r', encoding='utf-8') as f:
            md_content = f.read()

    # Конвертируем Markdown в HTML
    html_content = render_markdown_for_modal(md_content, task_id)

    dif_level = get_object_or_404(DifficultyLevel, id=task.difficulty_id)

    return JsonResponse({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'difficulty': dif_level.display_name,
        'md_content': html_content,  # Возвращаем HTML, а не Markdown
        'test_files': task.test_files,
    }, json_dumps_params={'ensure_ascii': False})


def render_markdown_for_modal(md_content, task_id):
    """
    Конвертирует Markdown в HTML для отображения в модальном окне
    """

    # 1. Сначала обрабатываем изображения в Markdown
    # Заменяем ![alt](img.png) на HTML теги
    def replace_images(match):
        alt = match.group(1)
        src = match.group(2)
        if src in ['img.png', 'image.png', 'picture.png'] or src.endswith(('.png', '.jpg', '.jpeg')):
            return f'<img class="img-right" src="/tasks/task/{task_id}/image/{src}" alt="{alt}">'
        return match.group(0)

    md_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_images, md_content)

    # 2. Конвертируем Markdown в HTML
    html_content = markdown.markdown(md_content, extensions=['extra', 'tables'])

    # 3. Удаляем пустые блоки кода
    html_content = re.sub(r'<pre><code[^>]*>\s*</code></pre>\n?', '', html_content)

    # 4. Убеждаемся, что таблицы не экранированы
    # HTML таблицы должны остаться как есть

    return html_content


# def render_markdown_without_empty_blocks(md_content, task_id):
#     """Конвертирует Markdown в HTML и удаляет пустые блоки кода"""
#     # Сначала обрабатываем изображения в Markdown
#     md_content = render_markdown_images_in_markdown(md_content, task_id)
#
#     # Конвертируем Markdown в HTML
#     html_content = markdown.markdown(md_content, extensions=['extra'])
#
#     # Удаляем пустые блоки кода
#     html_content = re.sub(r'<pre><code[^>]*>\s*</code></pre>\n?', '', html_content)
#
#     return html_content


# def render_markdown_images_in_markdown(md_content, task_id):
#     """
#     Обрабатывает изображения на уровне Markdown (ДО конвертации в HTML)
#     """
#     lines = md_content.split('\n')
#     new_lines = []
#
#     for line in lines:
#         # Ищем Markdown изображения: ![alt](img.png)
#         img_matches = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', line)
#
#         for alt, src in img_matches:
#             # Проверяем, является ли это изображением
#             if src.endswith(('.png', '.jpg', '.jpeg', '.gif')):
#                 # Создаем HTML тег вместо Markdown
#                 html_img = f'<img class="img-right" src="/tasks/task/{task_id}/image/{src}" alt="{alt}">'
#                 line = line.replace(f'![{alt}]({src})', html_img)
#
#         new_lines.append(line)
#
#     return '\n'.join(new_lines)
#
#
# # Старая функция - переименуем и оставим для обратной совместимости
# def render_markdown_with_images(html_content, task_id):
#     """
#     Обрабатывает изображения в HTML (устаревшая версия)
#     """
#     # Ищем img теги с src="img.png"
#     pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
#
#     def replace_img(match):
#         src = match.group(1)
#         if src == 'img.png' or src.endswith('.png'):
#             # Находим alt текст
#             alt_match = re.search(r'alt="([^"]+)"', match.group(0))
#             alt = alt_match.group(1) if alt_match else ""
#             return f'<img class="img-right" src="/tasks/task/{task_id}/image/{src}" alt="{alt}">'
#         return match.group(0)
#
#     return re.sub(pattern, replace_img, html_content)


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

    html_content = render_markdown_without_empty_blocks(md_content, task.id)

    # Получаем загруженную программу и попытки
    uploaded_program = None
    last_attempt = None

    if request.user.is_authenticated:
        # Последняя программа
        uploaded_program = UploadedProgram.objects.filter(
            task=task,
            user=request.user
        ).order_by('-upload_time').first()

        # ВАЖНО: ищем попытку по реальному ID задачи (real_task_id)
        # Преобразуем task.id в строку для сравнения
        task_id_str = str(task.id)

        last_attempt = TaskAttempt.objects.filter(
            user=request.user,
            real_task_id=task_id_str  # используем real_task_id вместо task_id
        ).order_by('-attempt_time').first()

    context = {
        'task': task,
        'md_html': html_content,
        'uploaded_program': uploaded_program,
        'last_attempt': last_attempt,
        'title': task.title
    }
    return render(request, 'task_description_app/task_detail.html', context)


@login_required
def get_attempt_results(request, attempt_id):
    """API для получения результатов попытки (для ученика и учителя)"""
    try:
        attempt = get_object_or_404(TaskAttempt, id=attempt_id)

        # Проверяем права доступа
        is_teacher = request.user.user_type == 'teacher'
        is_owner = attempt.user == request.user

        # Если не учитель и не владелец - доступ запрещен
        if not (is_teacher or is_owner):
            return JsonResponse({
                'success': False,
                'error': 'Доступ запрещен'
            }, status=403)

        # Парсим результаты
        results_data = {}
        if attempt.result:
            try:
                results_data = json.loads(attempt.result)
            except json.JSONDecodeError:
                results_data = {'message': attempt.result}

        # Получаем код программы
        code = attempt.code or ''

        # Если код пустой, пробуем получить из UploadedProgram
        if not code and is_teacher:
            # Для учителя - показываем код из последней программы ученика
            from .models import UploadedProgram
            program = UploadedProgram.objects.filter(
                user=attempt.user,
                task__id=attempt.real_task_id
            ).order_by('-upload_time').first()

            if program and program.program_file:
                try:
                    program.program_file.open('r')
                    code = program.program_file.read()
                    program.program_file.close()
                except Exception as e:
                    print(f"Ошибка чтения файла: {e}")

        # Формируем ответ
        response_data = {
            'success': True,
            'code': code,
            'status': attempt.status,
            'is_solved': attempt.is_solved,
            'attempt_time': attempt.attempt_time.strftime('%d.%m.%Y %H:%M:%S'),
            'real_task_id': attempt.real_task_id,
            'task_id': attempt.task_id,
            'result': results_data,
            'student_name': f"{attempt.user.last_name} {attempt.user.first_name}" if is_teacher else None
        }

        return JsonResponse(response_data)

    except TaskAttempt.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Попытка не найдена'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# def get_task_info(request, task_id):
#     """API для получения информации о задаче"""
#     task = get_object_or_404(Task, id=task_id)
#     task_files = get_task_files(task_id)
#
#     # Читаем содержимое task.md
#     md_content = ""
#     if os.path.exists(task_files['md']):
#         with open(task_files['md'], 'r', encoding='utf-8') as f:
#             md_content = f.read()
#     md_content = render_markdown_without_empty_blocks(md_content, task_id)
#
#
#
#     dif_level = get_object_or_404(DifficultyLevel, id=task.difficulty_id)
#
#     return JsonResponse({
#         'id': task.id,
#         'title': task.title,
#         'description': task.description,
#         'difficulty': dif_level.display_name,
#         'md_content': md_content,
#         'test_files': task.test_files,
#     })


def clean_text(text):
    """Очищает текст от лишних пробелов"""
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


def md_template():
    temp = textwrap.dedent('''\
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
    return temp


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
                py_content = clean_text(content_form.cleaned_data['task_py_content'])
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

                # 5. Сохраняем изображение(если загружено)
                if request.FILES.get('task_image'):
                    image_file = request.FILES['task_image']
                    image_path = os.path.join(task_dir, 'img.png')

                    # Сохраняем как img.png (перезаписываем, если существует)
                    with open(image_path, 'wb+') as destination:
                        for chunk in image_file.chunks():
                            destination.write(chunk)

                # 6. СОЗДАЕМ СВЯЗИ В СТРУКТУРЕ
                # находим или создаем узлы структуры
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
        default_md = md_template()
        content_form.fields['task_md_content'].initial = default_md

        # Шаблон для task.py
        default_py = '''def solve():
    data = input().split()
    # Ваш код
    result = 0
    print(result)

if __name__ == "__main__":
    solve()'''
        content_form.fields['task_py_content'].initial = clean_text(default_py)

        difficulty_levels = DifficultyLevel.objects.all()
        max_id = Task.objects.aggregate(Max('id'))['id__max'] or 0

        context = {
            'task_form': task_form,
            'content_form': content_form,
            'difficulty_levels': difficulty_levels,
            'task_id': max_id + 1,
        }
        return render(request, 'task_description_app/task_add.html', context)


def serve_task_image(request, task_id, filename):
    """
    Отдает изображение из папки задачи
    """
    from .models import Task
    from django.conf import settings
    import os

    try:
        task = get_object_or_404(Task, id=task_id)

        # Путь к папке задачи
        task_dir = os.path.join(settings.TASKS_ROOT, 'tasks', str(task.id))
        file_path = os.path.join(task_dir, filename)

        # Выводим список файлов в директории
        if os.path.exists(task_dir):
            files = os.listdir(task_dir)
        else:
            print(f"Директория не существует: {task_dir}")

        if not os.path.exists(file_path):
            raise Http404(f"Файл не найден: {file_path}")

        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type=content_type)

    except Exception as e:
        logger.info(f"Ошибка в serve_task_image: {e}")
        raise


def get_task_path_from_structure(task):
    """Получает путь к задаче из структуры ClassStructure"""
    placements = TaskPlacement.objects.filter(task=task).select_related('structure_node')
    if not placements.exists():
        return None

    # Берем первый placement (или можно объединить несколько)
    placement = placements.first()
    node = placement.structure_node

    # Собираем путь из названий узлов
    path_parts = []
    current = node
    while current:
        path_parts.insert(0, current.name)
        current = current.parent

    # Добавляем папку задачи
    path_parts.append(f"task_{task.id}")

    return os.path.join(settings.BASE_DIR, 'tasks_for_tests', *path_parts)


def get_or_create_structure_node(class_name, topic_name, lesson_name, level_name):
    """Получает или создает узлы структуры"""
    # Уровень 0: Класс
    class_node, _ = ClassStructure.objects.get_or_create(
        name=class_name,
        level=0,
        parent=None
    )

    # Уровень 1: Тема
    topic_node, _ = ClassStructure.objects.get_or_create(
        name=topic_name,
        level=1,
        parent=class_node
    )

    # Уровень 2: Урок
    lesson_node, _ = ClassStructure.objects.get_or_create(
        name=lesson_name,
        level=2,
        parent=topic_node
    )

    # Уровень 3: Уровень сложности
    level_node, _ = ClassStructure.objects.get_or_create(
        name=level_name,
        level=3,
        parent=lesson_node
    )

    return level_node


@login_required
@user_passes_test(is_teacher)
def task_edit(request, task_id):
    """Редактирование существующей задачи"""
    task = get_object_or_404(Task, id=task_id)

    # Получаем путь к папке задачи (из структуры или из settings.TASKS_ROOT)
    task_dir = os.path.join(settings.TASKS_ROOT, 'tasks', str(task.id))

    # Создаем папку, если её нет
    os.makedirs(task_dir, exist_ok=True)

    # Пути к файлам
    task_md_path = os.path.join(task_dir, 'task.md')
    task_py_path = os.path.join(task_dir, 'task.py')
    img_path = os.path.join(task_dir, 'img.png')

    # Читаем текущее содержимое файлов
    current_md_content = ""
    current_py_content = ""
    img_exists = os.path.exists(img_path)

    if os.path.exists(task_md_path):
        with open(task_md_path, 'r', encoding='utf-8') as f:
            current_md_content = f.read()
    else:
        # Если файла нет, создаем заглушку
        current_md_content = str(md_template())

    if os.path.exists(task_py_path):
        with open(task_py_path, 'r', encoding='utf-8') as f:
            current_py_content = f.read()
    else:
        current_py_content = "def solve():\n    pass\n\nif __name__ == '__main__':\n    solve()"

    # Читаем существующие тесты
    existing_tests = []
    test_files = sorted([f for f in os.listdir(task_dir) if f.endswith('.in')])
    for test_file in test_files:
        test_num = test_file.replace('test', '').replace('.in', '')
        out_file = f'test{test_num}.out'

        input_content = ""
        output_content = ""

        in_path = os.path.join(task_dir, test_file)
        if os.path.exists(in_path):
            with open(in_path, 'r', encoding='utf-8') as f:
                input_content = f.read()

        out_path = os.path.join(task_dir, out_file)
        if os.path.exists(out_path):
            with open(out_path, 'r', encoding='utf-8') as f:
                output_content = f.read()

        existing_tests.append({
            'num': test_num,
            'input': input_content,
            'output': output_content
        })

    if request.method == 'POST':
        # Используем обычные формы, а не ModelForm для редактирования
        # Обновляем задачу вручную
        task.title = request.POST.get('title', '')
        difficulty_id = request.POST.get('difficulty')
        if difficulty_id:
            task.difficulty_id = difficulty_id
        task.description = request.POST.get('description', '')
        task.save()

        # Обновляем task.md
        new_md_content = request.POST.get('task_md_content', '')
        # Применяем clean_text для удаления лишних переносов
        cleaned_md_content = clean_text(new_md_content)

        if cleaned_md_content != current_md_content:
            with open(task_md_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_md_content)

        # Обновляем task.py
        new_py_content = request.POST.get('task_py_content', '')
        cleaned_py_content = clean_text(new_py_content)
        if cleaned_py_content != current_py_content:
            with open(task_py_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_py_content)

        # Обновляем тесты
        test_count = int(request.POST.get('test_count', 0))

        # Удаляем старые тестовые файлы
        for old_file in os.listdir(task_dir):
            if old_file.startswith('test') and (old_file.endswith('.in') or old_file.endswith('.out')):
                os.remove(os.path.join(task_dir, old_file))

        # Создаем новые тесты
        test_files_list = []
        for i in range(1, test_count + 1):
            input_data = request.POST.get(f'test_{i}_input', '')
            output_data = request.POST.get(f'test_{i}_output', '')

            if input_data.strip() or output_data.strip():
                in_path = os.path.join(task_dir, f'test{i}.in')
                out_path = os.path.join(task_dir, f'test{i}.out')

                # Очищаем данные тестов от лишних переносов
                cleaned_input = clean_text(input_data)
                cleaned_output = clean_text(output_data)

                with open(in_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_input)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_output)

                test_files_list.append(f'test{i}.in')

        task.test_files = test_files_list
        task.save()

        # Обработка изображения
        if 'task_image' in request.FILES:
            image_file = request.FILES['task_image']
            with open(img_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
        elif request.POST.get('remove_image') == 'true' and img_exists:
            os.remove(img_path)

        messages.success(request, f'Задача #{task.id} успешно обновлена!')
        return redirect('tasks:task_edit', task_id=task.id)

    # GET запрос - заполняем формы
    from .forms import TaskEditForm, TaskContentForm
    task_form = TaskEditForm(initial={
        'title': task.title,
        'difficulty': task.difficulty_id,
        'description': task.description,
    })
    content_form = TaskContentForm(initial={
        'task_md_content': current_md_content,
        'task_py_content': current_py_content,
    })

    context = {
        'task_form': task_form,
        'content_form': content_form,
        'existing_tests': existing_tests,
        'task_id': task.id,
        'task': task,
        'img_exists': img_exists,
        'is_edit_mode': True,
    }
    return render(request, 'task_description_app/task_edit.html', context)


@login_required
@user_passes_test(is_teacher)
def task_delete(request, task_id):
    """Удаление задачи"""
    task = get_object_or_404(Task, id=task_id)
    task_title = task.title

    # Получаем путь к папке задачи
    task_dir = get_task_path_from_structure(task)

    # Удаляем папку с файлами, если она существует
    if task_dir and os.path.exists(task_dir):
        shutil.rmtree(task_dir)

    # Удаляем связи TaskPlacement
    TaskPlacement.objects.filter(task=task).delete()

    task.delete()
    messages.success(request, f'Задача "{task_title}" (#{task_id}) успешно удалена!')
    return redirect('tasks:task_list')


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

    return redirect('tasks:collection_attempt', attempt_id=attempt.id)


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

    for assignment in assignments:
        if assignment.is_overdue():
            assignment.status = 'expired'
            assignment.save()

    context = {
        'assignments': assignments,
        'title': 'Мои задания',

    }
    return render(request, 'task_description_app/my_assignments.html', context)


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

        # Сохраняем попытку
        TaskAttempt.objects.create(
            user=request.user,
            real_task_id=task_id,
            code=code,
            is_solved=is_solved,
            status='completed'
        )

    # Обновляем попытку
    attempt.score = total_score
    attempt.status = 'completed'
    attempt.completed_at = timezone.now()
    attempt.save()

    # Уведомляем учителя
    from notifications.utils import notify_teacher_about_completed_assignment
    notify_teacher_about_completed_assignment(
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
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    # Проверяем, что пользователь - ученик
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Доступ только для учеников'}, status=403)

    try:
        data = json.loads(request.body)
        message = data.get('message', '')

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


@login_required
@csrf_exempt
def check_solution(request):
    """API для проверки решения задачи"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        code = data.get('code')
        language = data.get('language', 'python')

        if not task_id or not code:
            return JsonResponse({'error': 'Не указан ID задачи или код решения'}, status=400)

        # Получаем задачу
        task = get_object_or_404(Task, id=task_id)

        # СОЗДАЕМ ОБЪЕКТ InMemoryUploadedFile
        uploaded_file = create_uploaded_file_from_code(
            code=code,
            filename=f"solution_task_{task_id}_{request.user.id}.py",
            task_id=task_id
        )

        # Сохраняем программу в UploadedProgram
        uploaded_program = UploadedProgram.objects.create(
            user=request.user,
            task=task,
            program_file=uploaded_file,
            status='testing'
        )
        tests_path = os.path.join(settings.TASKS_ROOT, 'tasks', str(task_id))

        # Проверяем решение
        if language == 'python':
            from testing_app.tester_project.tester import PythonCodeTester
            tester = PythonCodeTester(uploaded_program.program_file.path, tests_path)
            result_tests = tester.run_all_tests()
        else:
            return JsonResponse({'error': f'Язык {language} не поддерживается'}, status=400)

        # Вычисляем статистику
        total_tests = len(result_tests)
        passed_count = sum(1 for r in result_tests if r.get('passed', False))
        failed_count = total_tests - passed_count
        success = failed_count == 0

        result = {
            'success': success,
            'tests_passed': passed_count,
            'total_tests': total_tests,
            'results': result_tests,
            'message': 'Все тесты пройдены!' if success else f'Пройдено {passed_count} из {total_tests} тестов'
        }

        # Обновляем статус
        uploaded_program.status = 'passed' if result.get('success', False) else 'failed'
        uploaded_program.test_results = result_tests
        uploaded_program.save()

        # Сохраняем попытку
        task_attempt = TaskAttempt.objects.create(
            user=request.user,
            real_task_id=task_id,
            code=code,
            is_solved=result.get('success', False),
            status='correct' if result.get('success', False) else 'incorrect',
            result=json.dumps(result_tests),
            task_id=uploaded_program.task_id,  # связываем с программой
            task_path=uploaded_program.program_file.path,
        )

        # Отправляем уведомление учителю, если задача решена
        if result.get('success', False):
            from notifications.utils import notify_teacher_about_task_solved
            notify_teacher_about_task_solved(
                student=request.user,
                task_id=task_id,
                task_level=task.difficulty.display_name if task.difficulty else None,
                task_title=task.title
            )

        return JsonResponse({
            'success': result.get('success', False),
            'tests_passed': result.get('tests_passed', 0),
            'total_tests': result.get('total_tests', 0),
            'message': result.get('message', ''),
            'attempt_id': task_attempt.id,
            'program_id': uploaded_program.id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e),
            'error': str(e)
        }, status=500)
