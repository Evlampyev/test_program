# views.py (приложение tasks)
import os

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Task
import markdown


def task_list(request):
    """Страница со списком всех задач"""
    tasks = Task.objects.all()
    context = {
        'tasks': tasks,
        'title': 'Список задач'
    }
    return render(request, 'temp_tests/task_list.html', context)


def task_detail(request, task_id):
    """Отображение конкретной задачи с Markdown"""
    task = get_object_or_404(Task, id=task_id)

    # Читаем и конвертируем Markdown файл
    md_content = ""
    if task.md_file and os.path.exists(task.md_path):
        with open(task.md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

    # Конвертируем Markdown в HTML
    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])

    # Создаем экземпляр UploadedProgram для этой задачи и пользователя
    from temp_tests.models import UploadedProgram

    # Проверяем, есть ли уже загруженная программа для этой задачи
    if request.user.is_authenticated:
        uploaded_program = UploadedProgram.objects.filter(
            task=task,
            user=request.user
        ).order_by('-upload_time').first()
    else:
        uploaded_program = None

    context = {
        'task': task,
        'md_html': html_content,
        'uploaded_program': uploaded_program,
        'title': task.title
    }
    return render(request, 'temp_tests/task_detail.html', context)


def get_task_info(request, task_id):
    """API для получения информации о задаче (AJAX)"""
    task = get_object_or_404(Task, id=task_id)

    return JsonResponse({
        'task_id': task.id,
        'task_title': task.title,
        'md_path': task.md_path if task.md_file else None,
        'test_path': task.test_path if task.test_file else None,
    })
