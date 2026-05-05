# views.py (приложение tasks)
import os
import re
import shutil
import textwrap
import mimetypes
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
from django.views.decorators.http import require_POST

from .forms import TaskAddForm, TaskContentForm, TaskEditForm
from . import Task, DifficultyLevel, TaskAttempt, UploadedProgram
# from .utils import create_uploaded_file_from_code, get_task_files
from manage import logger
from ..shared import ClassStructure, TaskPlacement
from ..shared.decorators import is_teacher
from ..shared.utils import create_uploaded_file_from_code, get_task_files
from ..shared.views import get_task_path_from_structure, get_or_create_structure_node


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


def clean_text(text):
    """Очищает текст от лишних пробелов"""
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


@login_required
def task_list(request):
    """Страница со списком всех задач"""
    tasks = Task.objects.all()

    # Получаем структуру для дерева
    tree_data = build_tree_structure()

    # Подсчитываем общее количество задач
    total_tasks = Task.objects.count()

    # Получаем все уровни сложности для легенды
    difficulty_levels = DifficultyLevel.objects.all().order_by('level_order')

    context = {
        'tasks': tasks,
        'title': 'Список задач',
        'tree_data': json.dumps(tree_data),  # Передаем как JSON строку
        'total_tasks': total_tasks,
        'difficulty_levels': difficulty_levels,
    }
    return render(request, 'task_description_app/tasks/task_list.html', context)


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
    return render(request, 'task_description_app/tasks/task_detail.html', context)


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
                    logger.error(f"Ошибка чтения файла при попытке полученя кода ученика: {e}")

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
                # task_folder = task_form.cleaned_data['task_folder'].strip()

                # Создаем задачу в БД
                task = task_form.save(commit=False)
                task.created_by = request.user
                task.save()

                # СОЗДАЕМ ПАПКУ ДЛЯ ЗАДАЧИ В НОВОМ МЕСТЕ (tasks/ID/)
                task_dir = os.path.join(settings.TASKS_ROOT, str(task.id))
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
                level_node = get_or_create_structure_node(class_name, topic, lesson, level)
                # class_node, _ = ClassStructure.objects.get_or_create(
                #     name=class_name,
                #     level=0,
                #     parent=None
                # )
                #
                # topic_node, _ = ClassStructure.objects.get_or_create(
                #     name=topic,
                #     level=1,
                #     parent=class_node
                # )
                #
                # lesson_node, _ = ClassStructure.objects.get_or_create(
                #     name=lesson,
                #     level=2,
                #     parent=topic_node
                # )
                #
                # level_node, _ = ClassStructure.objects.get_or_create(
                #     name=level,
                #     level=3,
                #     parent=lesson_node
                # )

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
        return render(request, 'task_description_app/tasks/task_add.html', context)


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
        task_dir = os.path.join(settings.TASKS_ROOT, str(task.id))
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


@login_required
@user_passes_test(is_teacher)
def task_edit(request, task_id):
    """Редактирование существующей задачи"""
    task = get_object_or_404(Task, id=task_id)

    # Получаем путь к папке задачи (из структуры или из settings.TASKS_ROOT)
    task_dir = os.path.join(settings.TASKS_ROOT, str(task.id))

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
        return redirect('tasks_&_collections:tasks:edit', task_id=task.id)

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
    return render(request, 'task_description_app/tasks/task_edit.html', context)


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
        tests_path = os.path.join(settings.TASKS_ROOT, str(task_id))

        # Сохраняем путь к файлу для последующего удаления
        file_path = uploaded_program.program_file.path

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

        # 🔥 УДАЛЯЕМ ВРЕМЕННЫЙ ФАЙЛ ПОСЛЕ ТЕСТИРОВАНИЯ
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Удален временный файл после тестирования: {file_path}")

                # Также удаляем директорию, если она пуста
                dir_path = os.path.dirname(file_path)
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    logger.info(f"Удалена пустая директория: {dir_path}")
        except Exception as e:
            logger.error(f"Ошибка удаления файла {file_path}: {e}")

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
