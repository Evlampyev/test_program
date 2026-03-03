# testing_app/views.py
import os
import json

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from task_description_app.models import UploadedProgram, Task, TaskAttempt
import subprocess

from testing_app.tester_project.tester import PythonCodeTester
from manage import logger
from task_description_app.models import update_solved_tasks





def run_tests(request, program_id):
    """Запуск тестов для загруженной программы"""
    program = get_object_or_404(UploadedProgram, id=program_id)
    logger.info(f"Выбрана задача №{program_id = }")

    # Обновляем статус
    program.status = 'testing'
    program.save()

    # Создаем запись о попытке
    attempt = TaskAttempt.objects.create(
        user=request.user,
        task_path=program.program_path,
        task_id=program_id,
        # code=code,
        status='pending'
    )

    # Получаем путь к тестам из задачи
    task = program.task
    task_id = program.task_id
    # task_data = get_object_or_404(Task, id=task_id)
    # test_path = task_data.test_path
    # print(f"{test_path = }")
    # print(f"{task.test_path}")
    # tests_path = task.test_path
    tests_path = os.path.join(settings.TASKS_ROOT, task.test_path)
    student_code_path = program.program_file.path

    logger.info(f"Задача №{task_id}; папка с тестами: {tests_path}; путь к коду ученика: {student_code_path}")

    if not os.path.exists(tests_path):
        return render(request, 'testing_app/error.html', {
            'error': 'Файл с тестами не найден',
            'title': "Ошибка тестирования",
            'support_email': 'AEvlampev@1pku.ru',
        })

    try:
        # Запускаем тесты
        print(f"📁 Папка с тестами: {tests_path}; путь к коду ученика: {student_code_path}")
        tester = PythonCodeTester(student_code_path, tests_path)
        results = tester.run_all_tests()

        logger.info(f"Результаты тестов: {results}")
        # Сохраняем результаты
        program.test_results = results
        program.status = 'passed' if results.returncode == 0 else 'failed'
        program.save()
# проблема здесь, не обновляется статус попытки, нужно разобрать словарь results

        # Обновляем статус попытки
        attempt.status = 'correct' if results.get('success') else 'incorrect'
        attempt.result = json.dumps(results, ensure_ascii=False)
        attempt.is_solved = results.get('success', False)
        attempt.save()

    except subprocess.TimeoutExpired:
        test_results = {
            'error': 'Таймаут выполнения тестов',
            'passed': False
        }
        program.test_results = test_results
        program.status = 'failed'
        program.save()
    except Exception as e:
        test_results = {
            'error': str(e),
            'passed': False
        }
        program.test_results = test_results
        program.status = 'failed'
        program.save()

        # Вычисляем статистику
    total_tests = len(results)
    passed_count = sum(1 for r in results if r.get('passed', False))
    failed_count = total_tests - passed_count
    success_rate = int((passed_count / total_tests * 100)) if total_tests > 0 else 0
    task_data = get_object_or_404(Task, id=task_id)
    # user = request.user
    # print(f"{user=}")
    if success_rate == 100:
        task_data.update_statistics('passed')
        # update_solved_tasks(request, program)
    else:
        task_data.update_statistics('failed')

    return render(request, 'testing_app/results.html', {
        'program': program,
        'test_results': results,
        'task': task,
        'total_tests': total_tests,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'success_rate': success_rate,

    })
