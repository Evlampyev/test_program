import os
import sys
import django
import json
from pathlib import Path

# Настройка Django окружения
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TempTestsProgram.settings')
django.setup()

# Импортируем модели после настройки Django
from django.contrib.auth import get_user_model
from django.db import models
from task_description_app.models import Task, DifficultyLevel, ClassStructure, TaskPlacement
from make_json import scan_tasks_simple
import shutil
from django.conf import settings

User = get_user_model()


def migrate_new_tasks_only():
    """Миграция только новых задач (создание структуры и добавление задач с id > 59)"""
    print("=" * 60)
    print("МИГРАЦИЯ НОВЫХ ЗАДАЧ")
    print("=" * 60)

    # 1. Проверяем наличие уровней сложности
    ensure_difficulty_levels()

    # 2. Получаем структуру из файлов
    print("\n📁 Сканирование файловой структуры...")
    structure = scan_tasks_simple('tasks_for_tests')

    # 3. Создаем корневую папку для задач, если её нет
    tasks_root = os.path.join(settings.TASKS_ROOT, 'tasks')
    os.makedirs(tasks_root, exist_ok=True)

    # 4. Словарь для отслеживания уже созданных задач
    task_cache = {}  # ключ: путь к папке задачи, значение: ID задачи

    # Загружаем существующие задачи в кэш
    for task in Task.objects.all():
        if task.path:
            # Нормализуем путь при загрузке в кэш
            normalized_path = task.path.replace('\\', '/')
            task_cache[normalized_path] = task.id

    # 5. Проходим по структуре и создаем узлы
    print("\n🏗️  Создание структуры классов/тем/уроков...")

    # Счетчики для статистики
    stats = {
        'nodes_created': 0,
        'tasks_processed': 0,
        'tasks_created': 0,
        'tasks_skipped': 0,
        'links_created': 0,
        'files_copied_for_existing': 0
    }

    for class_name, topics in structure.items():
        print(f"\n📚 Класс: {class_name}")

        # Создаем узел класса
        class_node, created = ClassStructure.objects.get_or_create(
            name=class_name,
            level=0,
            parent=None
        )
        if created:
            stats['nodes_created'] += 1
            print(f"  ✅ Создан класс: {class_name}")

        for topic_name, lessons in topics.items():
            print(f"  📖 Тема: {topic_name}")

            # Создаем узел темы
            topic_node, created = ClassStructure.objects.get_or_create(
                name=topic_name,
                level=1,
                parent=class_node
            )
            if created:
                stats['nodes_created'] += 1
                print(f"    ✅ Создана тема: {topic_name}")

            for lesson_name, levels in lessons.items():
                print(f"    📝 Урок: {lesson_name}")

                # Создаем узел урока
                lesson_node, created = ClassStructure.objects.get_or_create(
                    name=lesson_name,
                    level=2,
                    parent=topic_node
                )
                if created:
                    stats['nodes_created'] += 1
                    print(f"      ✅ Создан урок: {lesson_name}")

                for level_name, task_folders in levels.items():
                    print(f"      📊 Уровень: {level_name}")

                    # Создаем узел уровня
                    level_node, created = ClassStructure.objects.get_or_create(
                        name=level_name,
                        level=3,
                        parent=lesson_node
                    )
                    if created:
                        stats['nodes_created'] += 1
                        print(f"        ✅ Создан уровень: {level_name}")

                    # Обрабатываем задачи в этом уровне
                    for task_folder in task_folders:
                        stats['tasks_processed'] += 1
                        print(f"        🔹 Задача: {task_folder}")

                        # Формируем полный путь к папке задачи в старой структуре
                        old_task_path = os.path.join(
                            class_name,
                            topic_name,
                            lesson_name,
                            level_name,
                            task_folder
                        )
                        full_old_task_path = os.path.join(settings.TASKS_ROOT, old_task_path)

                        # НОРМАЛИЗУЕМ ПУТЬ (заменяем обратные слеши на прямые)
                        normalized_path = old_task_path.replace('\\', '/')

                        # Проверяем, существует ли папка
                        if not os.path.exists(full_old_task_path):
                            print(f"        ❌ Папка не найдена: {full_old_task_path}")
                            continue

                        # Проверяем, есть ли задача в кэше (по нормализованному пути)
                        if normalized_path in task_cache:
                            task_id = task_cache[normalized_path]
                            print(f"        ⏩ Задача уже существует в БД (ID: {task_id})")

                            # Проверяем, не превышает ли ID 59
                            if task_id <= 59:
                                print(f"        ⏩ Задача с ID {task_id} <= 59, пропускаем создание новой")
                                stats['tasks_skipped'] += 1

                                # КОПИРУЕМ ФАЙЛЫ для существующей задачи
                                task = Task.objects.get(id=task_id)
                                files_copied = copy_files_for_existing_task(
                                    task,
                                    full_old_task_path,
                                    task_folder
                                )
                                if files_copied:
                                    stats['files_copied_for_existing'] += 1
                                    print(f"        ✅ Файлы скопированы для существующей задачи ID: {task_id}")

                                # Создаем связь для существующей задачи
                                _, created = TaskPlacement.objects.get_or_create(
                                    task_id=task_id,
                                    structure_node=level_node
                                )
                                if created:
                                    stats['links_created'] += 1
                                    print(f"        ✅ Связь создана для существующей задачи")
                                continue
                            else:
                                # Задача с ID > 59, но уже есть в БД - возможно, нужно обновить
                                print(f"        ⚠️ Задача с ID {task_id} > 59 уже есть в БД")
                                task = Task.objects.get(id=task_id)

                                # Обновляем путь и копируем файлы
                                task.path = normalized_path
                                task.save(update_fields=['path'])

                                files_copied = copy_files_for_existing_task(
                                    task,
                                    full_old_task_path,
                                    task_folder
                                )
                                if files_copied:
                                    stats['files_copied_for_existing'] += 1

                                # Создаем связь
                                _, created = TaskPlacement.objects.get_or_create(
                                    task=task,
                                    structure_node=level_node
                                )
                                if created:
                                    stats['links_created'] += 1
                                continue

                        # Проверяем, может быть задача уже есть в БД по старому пути
                        existing_task = Task.objects.filter(path=old_task_path).first()
                        if existing_task:
                            print(f"        ⏩ Задача уже есть в БД по пути (ID: {existing_task.id})")
                            task_cache[normalized_path] = existing_task.id

                            if existing_task.id <= 59:
                                print(f"        ⏩ Задача с ID {existing_task.id} <= 59, пропускаем создание новой")
                                stats['tasks_skipped'] += 1

                                # КОПИРУЕМ ФАЙЛЫ для существующей задачи
                                files_copied = copy_files_for_existing_task(
                                    existing_task,
                                    full_old_task_path,
                                    task_folder
                                )
                                if files_copied:
                                    stats['files_copied_for_existing'] += 1

                                # Создаем связь
                                _, created = TaskPlacement.objects.get_or_create(
                                    task=existing_task,
                                    structure_node=level_node
                                )
                                if created:
                                    stats['links_created'] += 1
                                    print(f"        ✅ Связь создана для существующей задачи")
                                continue

                        # Если дошли сюда - это новая задача, нужно создать
                        print(f"        🆕 Создание новой задачи...")
                        task = create_task_from_folder(full_old_task_path, task_folder, normalized_path)

                        if task:
                            task_cache[normalized_path] = task.id
                            stats['tasks_created'] += 1

                            # Создаем связь задачи с узлом структуры
                            _, created = TaskPlacement.objects.get_or_create(
                                task=task,
                                structure_node=level_node
                            )
                            if created:
                                stats['links_created'] += 1

                            print(f"        ✅ Новая задача создана (ID: {task.id})")
                        else:
                            print(f"        ❌ Ошибка создания задачи")

    print("\n" + "=" * 60)
    print("МИГРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)

    # Выводим статистику
    print(f"\n📊 Статистика:")
    print(f"   Создано узлов структуры: {stats['nodes_created']}")
    print(f"   Обработано задач: {stats['tasks_processed']}")
    print(f"   Создано новых задач: {stats['tasks_created']}")
    print(f"   Пропущено задач (id <= 59): {stats['tasks_skipped']}")
    print(f"   Создано связей: {stats['links_created']}")
    print(f"   Скопировано файлов для существующих задач: {stats['files_copied_for_existing']}")

    # Итоговая информация
    print(f"\n📈 Итог:")
    print(f"   Всего задач в БД: {Task.objects.count()}")
    print(f"   Всего узлов структуры: {ClassStructure.objects.count()}")
    print(f"   Всего связей: {TaskPlacement.objects.count()}")


def copy_files_for_existing_task(task, source_folder, task_folder_name):
    """
    Копирует файлы для существующей задачи в папку tasks/id/
    """
    try:
        # Создаем папку для задачи
        new_task_dir = os.path.join(settings.TASKS_ROOT, 'tasks', str(task.id))
        os.makedirs(new_task_dir, exist_ok=True)

        # Копируем task.md
        md_path = os.path.join(source_folder, 'task.md')
        if os.path.exists(md_path):
            shutil.copy2(md_path, os.path.join(new_task_dir, 'task.md'))

        # Копируем task.py
        py_path = os.path.join(source_folder, 'task.py')
        if os.path.exists(py_path):
            shutil.copy2(py_path, os.path.join(new_task_dir, 'task.py'))

        # Копируем тесты и собираем список
        test_files = []
        for filename in os.listdir(source_folder):
            if filename.startswith('test') and (filename.endswith('.in') or filename.endswith('.out')):
                shutil.copy2(
                    os.path.join(source_folder, filename),
                    os.path.join(new_task_dir, filename)
                )
                test_files.append(filename)

        # Обновляем поле test_files в задаче
        task.test_files = test_files
        task.save(update_fields=['test_files'])

        print(f"        📁 Файлы скопированы в: {new_task_dir}")
        print(f"        📋 Тесты: {test_files}")

        return True

    except Exception as e:
        print(f"        ❌ Ошибка при копировании файлов: {e}")
        return False


def ensure_difficulty_levels():
    """Создает уровни сложности, если их нет"""
    print("\n📊 Проверка уровней сложности...")

    levels = [
        {'name': 'easy', 'display': 'Легкий', 'order': 1},
        {'name': 'medium', 'display': 'Средний', 'order': 2},
        {'name': 'hard', 'display': 'Сложный', 'order': 3},
        {'name': 'very_hard', 'display': 'Очень сложный', 'order': 4},
        {'name': 'expert', 'display': 'Эксперт', 'order': 5},
    ]

    for level_data in levels:
        level, created = DifficultyLevel.objects.get_or_create(
            level_name=level_data['name'],
            defaults={
                'display_name': level_data['display'],
                'level_order': level_data['order']
            }
        )
        if created:
            print(f"  ✅ Создан уровень: {level.display_name}")


def create_task_from_folder(folder_path, task_folder_name, relative_path):
    """
    Создает новую задачу из папки и копирует файлы
    """
    try:
        # Читаем task.md для получения названия
        md_path = os.path.join(folder_path, 'task.md')
        if not os.path.exists(md_path):
            print(f"        ❌ Нет файла task.md в {folder_path}")
            return None

        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Извлекаем название из первой строки
        first_line = md_content.split('\n')[0].strip()
        title = first_line.replace('#', '').strip()
        if not title:
            title = f"Задача {task_folder_name}"

        # Читаем task.py
        py_path = os.path.join(folder_path, 'task.py')
        py_content = ""
        if os.path.exists(py_path):
            with open(py_path, 'r', encoding='utf-8') as f:
                py_content = f.read()

        # Определяем уровень сложности
        difficulty = DifficultyLevel.objects.first()

        # Пытаемся найти задачу по ID из первой строки
        try:
            str_task_id = md_content.split('\n')[0].strip()
            id_task = int(str_task_id.replace('#', '').strip())

            # Проверяем, существует ли задача с таким ID
            task = Task.objects.filter(id=id_task).first()

            if task:
                print(f"        🔍 Найдена существующая задача с ID {id_task}")
                task.path = relative_path
                task.title = title
                task.difficulty = difficulty
                task.save(update_fields=['path', 'title', 'difficulty'])
                print(f"        ✅ Задача с id={id_task} обновлена")
            else:
                print(f"        🔍 Задача с ID {id_task} не найдена, создаю новую")
                task = Task.objects.create(
                    title=title,
                    difficulty=difficulty,
                    description=f"Задача из папки {task_folder_name}",
                    is_public=True,
                    path=relative_path
                )
                print(f"        ✅ Новая задача создана с ID {task.id}")

        except Exception as e:
            print(f"        ⚠️ Не удалось извлечь ID из файла: {e}")
            # Создаем новую задачу без конкретного ID
            task = Task.objects.create(
                title=title,
                difficulty=difficulty,
                description=f"Задача из папки {task_folder_name}",
                is_public=True,
                path=relative_path
            )
            print(f"        ✅ Новая задача создана с ID {task.id}")

        # Создаем папку для задачи в новом месте
        new_task_dir = os.path.join(settings.TASKS_ROOT, 'tasks', str(task.id))
        os.makedirs(new_task_dir, exist_ok=True)

        # Копируем task.md
        shutil.copy2(md_path, os.path.join(new_task_dir, 'task.md'))

        # Копируем task.py
        if py_content:
            shutil.copy2(py_path, os.path.join(new_task_dir, 'task.py'))

        # Копируем тесты и собираем список
        test_files = []
        for filename in os.listdir(folder_path):
            if filename.startswith('test') and (filename.endswith('.in') or filename.endswith('.out')):
                shutil.copy2(
                    os.path.join(folder_path, filename),
                    os.path.join(new_task_dir, filename)
                )
                test_files.append(filename)

        task.test_files = test_files
        task.save(update_fields=['test_files'])

        print(f"        📁 Файлы скопированы в: {new_task_dir}")
        print(f"        📋 Тесты: {test_files}")

        return task

    except Exception as e:
        print(f"        ❌ Ошибка при создании задачи: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    migrate_new_tasks_only()
