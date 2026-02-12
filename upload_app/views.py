# upload_app/views.py
import os
import random
import string

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from temp_tests.models import UploadedProgram
from temp_tests.models import Task


def generate_random_id(length=6):
    """Генерация случайного 6-значного ID"""
    return ''.join(random.choices(string.digits, k=length))

@csrf_exempt
def upload_python_file(request):
    """Обработчик загрузки Python файлов"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Только POST запросы'}, status=405)

    try:
        uploaded_file = request.FILES.get('file')
        task_id = request.POST.get('task_id')  # Получаем ID задачи

        if not uploaded_file:
            return JsonResponse({'success': False, 'message': 'Файл не найден'}, status=400)

        if not task_id:
            return JsonResponse({'success': False, 'message': 'Не указан ID задачи'}, status=400)

        # Получаем задачу
        task = get_object_or_404(Task, id=task_id)

        # Проверяем расширение файла
        if not uploaded_file.name.lower().endswith('.py'):
            return JsonResponse({'success': False, 'message': 'Только файлы .py разрешены'}, status=400)

        # Сохраняем файл
        folder_id = generate_random_id()
        upload_dir = os.path.join('student_programs', str(task.id), folder_id)
        file_path = os.path.join(upload_dir, uploaded_file.name)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Создаем или обновляем запись UploadedProgram
        program = UploadedProgram.objects.create(
            user=request.user if request.user.is_authenticated else None,
            task=task,  # Связываем с задачей
            program_file=file_path,
            program_path=full_path,
            status='uploaded'
        )

        return JsonResponse({
            'success': True,
            'message': 'Файл успешно сохранён',
            'program_id': program.id,
            'task_id': task.id,
            'full_path': full_path,
            'redirect_url': f'/tester/run-tests/{program.id}/'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при сохранении файла: {str(e)}'
        }, status=500)