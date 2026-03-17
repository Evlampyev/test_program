# views.py (приложение tasks)
import os
import re
import textwrap

from django.core.cache import cache
from django.db.models import Max
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
import markdown
import json
import logging

from .forms import TaskAddForm, TaskContentForm
from .models import Task, DifficultyLevel, ClassStructure, TaskPlacement
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