# upload_app/views.py
import os
import random
import string
import tempfile
import shutil
import atexit
from datetime import datetime, timedelta

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from task_description_app.models import UploadedProgram
from task_description_app.models import Task
from manage import logger

# Глобальный список для отслеживания временных файлов
_temp_files = []
_temp_dirs = []


def cleanup_temp_files():
    """Очистка всех временных файлов при остановке сервера"""
    # print("\n🧹 Очистка временных файлов...")

    # Удаляем временные файлы
    for file_path in _temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # print(f"   Удален файл: {file_path}")
                logger.info(f"   Удален файл: {file_path}")
        except Exception as e:
            # print(f"   Ошибка удаления файла {file_path}: {e}")
            logger.error(f"   Ошибка удаления файла {file_path}: {e}")
    # Удаляем временные директории
    for dir_path in _temp_dirs:
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                # print(f"   Удалена директория: {dir_path}")
                logger.info(f"   Удалена директория: {dir_path}")
        except Exception as e:
            logger.error(f"   Ошибка удаления директории {dir_path}: {e}")
            # print(f"   Ошибка удаления директории {dir_path}: {e}")

    # Также очищаем старые файлы из стандартной директории
    cleanup_old_files()

    print("✅ Очистка завершена")


def cleanup_old_files(days=1):
    """Удаление файлов старше указанного количества дней"""
    student_programs_dir = os.path.join(settings.MEDIA_ROOT, 'student_programs')

    if not os.path.exists(student_programs_dir):
        return

    now = datetime.now()

    for root, dirs, files in os.walk(student_programs_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Проверяем время создания файла
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if now - file_time > timedelta(days=days):
                    os.remove(file_path)
                    # print(f"   Удален старый файл: {file_path}")
                    logger.info(f"   Удален старый файл: {file_path}")
            except Exception as e:
                # print(f"   Ошибка удаления {file_path}: {e}")
                logger.error(f"   Ошибка удаления {file_path}: {e}")

        # Удаляем пустые директории
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                if not os.listdir(dir_path):  # если директория пуста
                    os.rmdir(dir_path)
                    # print(f"   Удалена пустая директория: {dir_path}")
                    logger.info(f"   Удалена пустая директория: {dir_path}")
            except Exception as e:
                logger.error(f"   Ошибка удаления директории {dir_path}: {e}")
                # print(f"   Ошибка удаления директории {dir_path}: {e}")


# Регистрируем функцию очистки при остановке
atexit.register(cleanup_temp_files)


def generate_random_id(length=6):
    """Генерация случайного 6-значного ID"""
    return ''.join(random.choices(string.digits, k=length))


def get_temp_upload_path(instance, filename):
    """Генерация пути для временного файла"""
    # Используем системную временную директорию
    temp_dir = tempfile.mkdtemp(prefix='student_program_')
    _temp_dirs.append(temp_dir)  # Добавляем в список для очистки
    return os.path.join(temp_dir, filename)


def result_upload(user, uploaded_file, task_id) -> JsonResponse:

    print(f"{user = }, {uploaded_file = }, {task_id = }")
    if not uploaded_file:
        return JsonResponse({'success': False, 'message': 'Файл не найден'}, status=400)

    if not task_id:
        return JsonResponse({'success': False, 'message': 'Не указан ID задачи'}, status=400)

    # Получаем задачу
    task = get_object_or_404(Task, id=task_id)

    # Проверяем расширение файла
    if not uploaded_file.name.lower().endswith('.py'):
        return JsonResponse({'success': False, 'message': 'Только файлы .py разрешены'}, status=400)

    folder_id = generate_random_id()
    upload_dir = os.path.join('student_programs', str(task.id), folder_id)
    file_path = os.path.join(settings.MEDIA_ROOT, upload_dir, uploaded_file.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    print(f"путь до файла из upload_app: {file_path = }")
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    # Добавляем файл в список для очистки
    _temp_files.append(file_path)

    # Создаем запись в БД
    program = UploadedProgram.objects.create(
        user=user,
        task=task,
        program_file=file_path,  # или upload_dir для варианта Б
        program_path=file_path,
        status='uploaded'
    )

    return JsonResponse({
        'success': True,
        'message': 'Файл успешно сохранён',
        'program_id': program.id,
        'task_id': task.id,
        'full_path': file_path,
        'is_temporary': True,  # Флаг, что файл временный
        'redirect_url': f'/tester/run-tests/{program.id}/'
    })


@csrf_exempt
def upload_python_file(request):
    """Обработчик загрузки Python файлов"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Только POST запросы'}, status=405)

    try:
        uploaded_file = request.FILES.get('file')
        print(f"Загруженные файл: {uploaded_file = }  и его тип  {type(uploaded_file) = }")
        task_id = request.POST.get('task_id')
        user = request.user if request.user.is_authenticated else None
        result = result_upload(user, uploaded_file, task_id)
        return result

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при сохранении файла: {str(e)}'
        }, status=500)
