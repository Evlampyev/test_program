# testing_app/views.py
import os


from django.shortcuts import render, get_object_or_404
from temp_tests.models import UploadedProgram
import subprocess

from testing_app.tester_project.tester import PythonCodeTester
from manage import logger
# def run_tests(request, program_id):
#     """Запуск тестов для загруженной программы"""
#     program = get_object_or_404(UploadedProgram, id=program_id)
#
#     # Обновляем статус
#     program.status = 'testing'
#     program.save()
#
#     # Получаем путь к тестам из задачи
#     task = program.task
#     test_file_path = task.test_path
#
#     if not os.path.exists(test_file_path):
#         return render(request, 'testing_app/error.html', {
#             'error': 'Файл с тестами не найден'
#         })
#
#     try:
#         # Запускаем тесты
#         # Вариант 1: Запуск pytest с файлом программы
#         result = subprocess.run(
#             ['pytest', test_file_path,
#              '--program-path', program.program_path,
#              '--task-id', str(task.id)],
#             capture_output=True,
#             text=True,
#             timeout=30
#         )
#
#         # Вариант 2: Запуск программы ученика с тестами
#         # result = subprocess.run(
#         #     ['python', test_file_path, program.program_path],
#         #     capture_output=True,
#         #     text=True,
#         #     timeout=30
#         # )
#
#         test_results = {
#             'stdout': result.stdout,
#             'stderr': result.stderr,
#             'return_code': result.returncode,
#             'passed': result.returncode == 0
#         }
#
#         # Сохраняем результаты
#         program.test_results = test_results
#         program.status = 'passed' if result.returncode == 0 else 'failed'
#         program.save()
#
#     except subprocess.TimeoutExpired:
#         test_results = {
#             'error': 'Таймаут выполнения тестов',
#             'passed': False
#         }
#         program.test_results = test_results
#         program.status = 'failed'
#         program.save()
#     except Exception as e:
#         test_results = {
#             'error': str(e),
#             'passed': False
#         }
#         program.test_results = test_results
#         program.status = 'failed'
#         program.save()
#
#     return render(request, 'testing_app/results.html', {
#         'program': program,
#         'test_results': test_results,
#         'task': task
#     })

def run_tests(request, program_id):
    """Запуск тестов для загруженной программы"""
    program = get_object_or_404(UploadedProgram, id=program_id)
    logger.info(f"{program_id = }")

    # Обновляем статус
    program.status = 'testing'
    program.save()

    # Получаем путь к тестам из задачи
    task = program.task
    task_id = program.task_id
    test_file_path = task.test_path + '/' + str(task_id)
    program_file = program.program_file

    logger.info(f"{task_id} {test_file_path=}; {program_file=}")

    if not os.path.exists(test_file_path):
        return render(request, 'testing_app/error.html', {
            'error': 'Файл с тестами не найден'
        })

    try:
        # Запускаем тесты
        # Вариант 1: Запуск pytest с файлом программы
        result = subprocess.run(
            ['pytest', test_file_path,
             '--program-path', program.program_path,
             '--task-id', str(task.id)],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Вариант 2: Запуск программы ученика с тестами
        # result = subprocess.run(
        #     ['python', test_file_path, program.program_path],
        #     capture_output=True,
        #     text=True,
        #     timeout=30
        # )

        test_results = {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode,
            'passed': result.returncode == 0
        }

        # Сохраняем результаты
        program.test_results = test_results
        program.status = 'passed' if result.returncode == 0 else 'failed'
        program.save()

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

    return render(request, 'testing_app/results.html', {
        'program': program,
        'test_results': test_results,
        'task': task
    })