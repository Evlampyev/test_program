# testing_app/views.py
import os

from django.shortcuts import render, get_object_or_404
from temp_tests.models import UploadedProgram
import subprocess

from testing_app.tester_project.tester import PythonCodeTester
from manage import logger


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
    tests_path = task.test_path + '/' + str(task_id) + '/'
    student_code_path = program.program_file.path

    logger.info(f"Задача №{task_id}, папка с тестами: {tests_path}; {student_code_path=}")

    if not os.path.exists(tests_path):
        return render(request, 'testing_app/error.html', {
            'error': 'Файл с тестами не найден'
        })

    try:
        # Запускаем тесты
        tester = PythonCodeTester(student_code_path, tests_path)
        results = tester.run_all_tests()

        logger.info(f"Результаты тестов: {results}")

        # Сохраняем результаты
        program.test_results = results
        program.status = 'passed' if results.returncode == 0 else 'failed'
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

        # Вычисляем статистику
    total_tests = len(results)
    passed_count = sum(1 for r in results if r.get('passed', False))
    failed_count = total_tests - passed_count
    success_rate = int((passed_count / total_tests * 100)) if total_tests > 0 else 0

    return render(request, 'testing_app/results.html', {
        'program': program,
        'test_results': results,
        'task': task,
        'total_tests': total_tests,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'success_rate': success_rate,
    })
