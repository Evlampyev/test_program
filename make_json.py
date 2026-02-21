import os
import json


def scan_tasks_simple(root_dir='tasks_for_tests'):
    """Максимально простой скрипт для создания нужной структуры"""
    structure = {}

    for root, dirs, files in os.walk(root_dir):
        if 'task.md' in files:
            # Получаем путь относительно корня
            rel_path = os.path.relpath(root, root_dir)
            if rel_path == '.' or rel_path.startswith('._'):
                continue

            # Разбиваем путь
            parts = rel_path.split(os.sep)
            parts = [p for p in parts if not p.startswith('._')]

            if len(parts) >= 5:  # класс/тема/урок/уровень/task_XXX
                class_name = parts[0]
                topic = parts[1]
                lesson = parts[2]
                level = parts[3]
                task = parts[4]

                # Создаем структуру
                if class_name not in structure:
                    structure[class_name] = {}
                if topic not in structure[class_name]:
                    structure[class_name][topic] = {}
                if lesson not in structure[class_name][topic]:
                    structure[class_name][topic][lesson] = {}
                if level not in structure[class_name][topic][lesson]:
                    structure[class_name][topic][lesson][level] = []

                # Добавляем задачу
                if task not in structure[class_name][topic][lesson][level]:
                    structure[class_name][topic][lesson][level].append(task)

    return structure


if __name__ == '__main__':
    structure = scan_tasks_simple('tasks_for_tests')

    # Сохраняем JSON
    with open('structure.json', 'w', encoding='utf-8') as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

