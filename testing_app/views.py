# testing_app/views.py
import os
import json

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from task_description_app.models import UploadedProgram, Task, TaskAttempt
import subprocess

from testing_app.tester_project.tester import PythonCodeTester
from manage import logger


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
        real_task_id=program.task_id,
        # code=code,
        status='pending'
    )

    # Получаем путь к тестам из задачи
    task = program.task
    task_id = program.task_id
    tests_path = os.path.join(settings.TASKS_ROOT, task.test_path)
    student_code_path = program.program_file.path

    logger.info(f"Задача №{task_id}; папка с тестами: {tests_path};\nпуть к коду ученика: {student_code_path}")

    if not os.path.exists(tests_path):
        return render(request, 'testing_app/error.html', {
            'error': 'Файл с тестами не найден',
            'title': "Ошибка тестирования",
            'support_email': 'AEvlampev@1pku.ru',
        })

    try:
        # Запускаем тесты
        print(f"📁 Папка с тестами: {tests_path}; \nпуть к коду ученика: {student_code_path}")
        tester = PythonCodeTester(student_code_path, tests_path)
        results = tester.run_all_tests()
        logger.info(f"Результаты тестов: {results}")

        # Вычисляем статистику
        total_tests = len(results)
        passed_count = sum(1 for r in results if r.get('passed', False))
        failed_count = total_tests - passed_count
        success_rate = int((passed_count / total_tests * 100)) if total_tests > 0 else 0

        # Сохраняем результаты
        # program = get_object_or_404(UploadedProgram, id=program_id)
        # print(f"{program = }")
        program.test_results = results
        program.status = 'passed' if failed_count==0 else 'failed'
        program.save()
        # print("++++++++++++++++++++++")
        # print(f"{program.status = }")

        attempt.status = 'correct' if program.status == 'passed' else 'incorrect'
        print(f"{attempt.status = }")
        attempt.result = json.dumps(results, ensure_ascii=False)
        attempt.is_solved = True if attempt.status == 'correct' else False
        attempt.save()
        print("_______________________")




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
    #
    #     # Вычисляем статистику
    # total_tests = len(results)
    # passed_count = sum(1 for r in results if r.get('passed', False))
    # failed_count = total_tests - passed_count
    # success_rate = int((passed_count / total_tests * 100)) if total_tests > 0 else 0
    task_data = get_object_or_404(Task, id=task_id)
    user = request.user.student_profile
    print(f"{user = }")
    print(f"{task_id = }")
    user.add_solved_task(task_id)
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
