import datetime
import io
import os
import shutil

import pytz
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone



def create_task_files(task_id, md_content, py_content, tests):
    """
    Создает файлы для задачи в папке tasks/ID/
    """
    task_dir = os.path.join(settings.TASKS_ROOT, str(task_id))
    os.makedirs(task_dir, exist_ok=True)

    # Сохраняем task.md
    with open(os.path.join(task_dir, 'task.md'), 'w', encoding='utf-8') as f:
        f.write(md_content)

    # Сохраняем task.py
    with open(os.path.join(task_dir, 'task.py'), 'w', encoding='utf-8') as f:
        f.write(py_content)

    # Сохраняем тесты
    for i, (input_data, output_data) in enumerate(tests, 1):
        with open(os.path.join(task_dir, f'test{i}.in'), 'w', encoding='utf-8') as f:
            f.write(input_data)
        with open(os.path.join(task_dir, f'test{i}.out'), 'w', encoding='utf-8') as f:
            f.write(output_data)

    return task_dir


def copy_task_for_teacher(task_id, teacher_id):
    """
    Копирует задачу для учителя (если нужно сделать приватную копию)
    """
    original_dir = os.path.join(settings.TASKS_ROOT, str(task_id))
    new_dir = os.path.join(settings.TASKS_ROOT, 'teachers', str(teacher_id), 'tasks', str(task_id))

    if os.path.exists(original_dir):
        shutil.copytree(original_dir, new_dir)
        return new_dir
    return None


def get_task_files(task_id):
    """
    Возвращает пути к файлам задачи
    """
    task_dir = os.path.join(settings.TASKS_ROOT, str(task_id))

    files = {
        'md': os.path.join(task_dir, 'task.md'),
        'py': os.path.join(task_dir, 'task.py'),
        'tests': []
    }

    # Ищем тесты
    if os.path.exists(task_dir):
        for filename in os.listdir(task_dir):
            if filename.startswith('test') and (filename.endswith('.in') or filename.endswith('.out')):
                files['tests'].append(os.path.join(task_dir, filename))

    return files


def create_uploaded_file_from_code(code, filename=None, task_id=None):
    """
    Создает InMemoryUploadedFile из строки кода

    Args:
        code: строка с кодом решения
        filename: имя файла (опционально)
        task_id: ID задачи (для формирования имени)

    Returns:
        InMemoryUploadedFile: объект файла
    """
    timezone.activate(pytz.timezone(settings.TIME_ZONE))
    if filename is None:
        if task_id:
            filename = f"solution_task_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        else:
            filename = f"solution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

    # Создаем файловый объект в памяти
    file_content = code.encode('utf-8')
    file_io = io.BytesIO(file_content)

    # Создаем InMemoryUploadedFile
    uploaded_file = InMemoryUploadedFile(
        file=file_io,
        field_name='program_file',
        name=filename,
        content_type='application/octet-stream',
        size=len(file_content),
        charset='utf-8'
    )

    return uploaded_file