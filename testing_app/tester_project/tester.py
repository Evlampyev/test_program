import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from manage import logger

class PythonCodeTester:
    """
    Класс для тестирования Python-программ учеников.
    """

    def __init__(self, student_code_path: str, test_dir):
        """
        Инициализация тестера.

        Args:
            student_code_path: путь к файлу с кодом ученика
            test_dir: директория с тестами (по умолчанию 'tests')
        """
        self.student_code_path = Path(student_code_path)
        self.test_dir = Path(test_dir)

        if not self.student_code_path.exists():
            raise FileNotFoundError(f"Файл с кодом ученика не найден: {student_code_path}")

        if not self.test_dir.exists():
            raise FileNotFoundError(f"Директория с тестами не найдена: {test_dir}")

    def find_test_files(self) -> List[Tuple[Path, Optional[Path]]]:
        """
        Ищет пары тестовых файлов: входные (.in) и выходные (.out).

        Returns:
            Список кортежей (input_file, expected_output_file)
        """
        test_pairs = []

        # Сначала ищем все входные файлы
        input_files = list(self.test_dir.glob("*.in"))

        for input_file in input_files:
            # Формируем ожидаемое имя файла с выходными данными
            output_file = input_file.with_suffix('.out')

            if not output_file.exists():
                # print(f"⚠ Предупреждение: для входного файла {input_file.name} не найден выходной файл")
                logger.info(f"⚠ Предупреждение: для входного файла {input_file.name} не найден выходной файл")
                output_file = None

            test_pairs.append((input_file, output_file))

        # Также ищем файлы с расширением .input
        input_files_alt = list(self.test_dir.glob("*.input"))

        for input_file in input_files_alt:
            # Пробуем найти соответствующий .output файл
            output_file = input_file.with_suffix('.output')

            if not output_file.exists():
                # Пробуем вариант .out
                output_file = input_file.with_suffix('.out')
                if not output_file.exists():

                    # print(f"⚠ Предупреждение: для {input_file.name} не найден выходной файл")
                    logger.info(f"⚠ Предупреждение: для входного файла {input_file.name} не найден выходной файл")
                    output_file = None


            test_pairs.append((input_file, output_file))

        return sorted(test_pairs)

    def run_student_code(self, input_data: str) -> Tuple[str, str, int]:
        """
        Запускает код ученика с заданными входными данными.

        Args:
            input_data: строка с входными данными

        Returns:
            Кортеж (stdout, stderr, return_code)
        """
        try:
            # Запускаем программу ученика
            result = subprocess.run(
                [sys.executable, str(self.student_code_path)],
                input=input_data,
                text=True,
                capture_output=True,
                timeout=5  # 5 секунд на выполнение
            )

            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired:
            return "", "TIMEOUT: Программа выполнялась слишком долго (>5 секунд)", -1
        except Exception as e:
            return "", f"Ошибка запуска: {str(e)}", -1

    def normalize_output(self, output: str) -> str:
        """
        Нормализует вывод для сравнения:
        - Убирает лишние пробелы в конце строк
        - Убирает пустые строки в конце
        - Приводит к единому формату переносов строк
        """
        lines = output.splitlines()

        # Убираем пробелы в конце каждой строки
        lines = [line.rstrip() for line in lines]

        # Убираем пустые строки в конце
        while lines and lines[-1] == "":
            lines.pop()

        return '\n'.join(lines)

    def run_test(self, input_file: Path, expected_output_file: Optional[Path] = None) -> Dict:
        """
        Запускает один тест.

        Returns:
            Словарь с результатами теста
        """
        result = {
            'test_name': input_file.name,
            'passed': False,
            'input': '',
            'expected': '',
            'actual': '',
            'error': '',
            'return_code': 0
        }

        try:
            # Читаем входные данные
            with open(input_file, 'r', encoding='utf-8') as f:
                input_data = f.read()
            result['input'] = input_data

            with open(expected_output_file, 'r', encoding='utf-8') as f:
                output_data = f.read()
            result['expected'] = output_data

            # Запускаем код ученика
            stdout, stderr, return_code = self.run_student_code(input_data)
            result['return_code'] = return_code
            result['actual'] = stdout

            if return_code != 0:
                result['error'] = f"Программа завершилась с кодом {return_code}\n{stderr}"
                return result

            # Нормализуем вывод
            actual_normalized = self.normalize_output(stdout)

            if expected_output_file is None:
                result['error'] = "Отсутствует файл с ожидаемым выводом"
                return result

            # Читаем ожидаемые выходные данные
            with open(expected_output_file, 'r', encoding='utf-8') as f:
                expected_output = f.read()

            result['expected'] = expected_output
            expected_normalized = self.normalize_output(expected_output)

            # Сравниваем
            if actual_normalized == expected_normalized:
                result['passed'] = True
            else:
                result['error'] = "Вывод не совпадает с ожидаемым"

        except Exception as e:
            result['error'] = f"Ошибка при выполнении теста: {str(e)}"

        return result

    def run_all_tests(self) -> List[Dict]:
        """
        Запускает все тесты.

        Returns:
            Список результатов тестов
        """
        test_pairs = self.find_test_files()

        if not test_pairs:
            print("❌ Не найдено тестовых файлов!")
            logger.error("❌ Не найдено тестовых файлов!")
            # print("   Ожидаются файлы с расширениями .in/.input для входных данных")
            # print("   и .out/.output для ожидаемых выходных данных")
            return []

        print(f"📁 Найдено тестов: {len(test_pairs)}")
        logger.info(f"📁 Найдено тестов: {len(test_pairs)}")

        results = []
        passed_count = 0

        for i, (input_file, output_file) in enumerate(test_pairs, 1):
            # print(f"\n🔍 Тест {i}/{len(test_pairs)}: {input_file.name}")

            result = self.run_test(input_file, output_file)
            results.append(result)

            if result['passed']:
                # print("   ✅ ПРОЙДЕН")
                passed_count += 1
            else:
                # print("   ❌ НЕ ПРОЙДЕН")
                if result['error']:
                    # print(f"   Ошибка: {result['error']}")
                    pass

        # Выводим итоговую статистику
        # print("\n" + "="*50)
        # print(f"📊 ИТОГИ ТЕСТИРОВАНИЯ")
        # print("="*50)
        # print(f"Всего тестов: {len(test_pairs)}")
        # print(f"Пройдено: {passed_count}")
        # print(f"Не пройдено: {len(test_pairs) - passed_count}")
        #
        # if passed_count == len(test_pairs):
        #     print("🎉 Все тесты пройдены успешно!")
        # elif passed_count == 0:
        #     print("💥 Ни один тест не пройден")
        # else:
        #     print(f"📈 Успешность: {passed_count/len(test_pairs)*100:.1f}%")

        return results

    def print_detailed_failure(self, result: Dict):
        """
        Выводит подробную информацию о неудачном тесте.
        """
        print("\n" + "="*50)
        print(f"📄 Тест: {result['test_name']}")
        print("="*50)

        if result['error']:
            print(f"❌ Ошибка: {result['error']}")

        if result['input']:
            print("\n📥 Входные данные:")
            print("-" * 30)
            print(result['input'])

        if result['expected']:
            print("\n📤 Ожидаемый вывод:")
            print("-" * 30)
            print(result['expected'])

        if result['actual']:
            print("\n💻 Фактический вывод:")
            print("-" * 30)
            print(result['actual'])

        print("="*50)


def create_sample_tests(test_dir: str = "tests"):
    """
    Создает пример тестовых файлов для демонстрации.
    """
    import os
    os.makedirs(test_dir, exist_ok=True)

    # Пример 1: Простое суммирование двух чисел
    with open(os.path.join(test_dir, "test1.in"), 'w') as f:
        f.write("2 3")
    with open(os.path.join(test_dir, "test1.out"), 'w') as f:
        f.write("5")

    # Пример 2: Проверка четности числа
    with open(os.path.join(test_dir, "test2.in"), 'w') as f:
        f.write("7")
    with open(os.path.join(test_dir, "test2.out"), 'w') as f:
        f.write("Нечетное")

    # Пример 3: Несколько строк ввода
    with open(os.path.join(test_dir, "test3.in"), 'w') as f:
        f.write("3\n1 2 3")
    with open(os.path.join(test_dir, "test3.out"), 'w') as f:
        f.write("6")


def main():
    """
    Основная функция для запуска тестирования.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Тестирование программы ученика на Python',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:
  %(prog)s student_code.py              # тестирование с тестами из папки tests/
  %(prog)s student_code.py my_tests/    # тестирование с тестами из указанной папки
  %(prog)s --create-samples            # создание примеров тестов
        '''
    )

    parser.add_argument('student_code', nargs='?', help='Путь к файлу с кодом ученика')
    parser.add_argument('test_dir', nargs='?', default='tests',
                        help='Папка с тестами (по умолчанию: tests)')
    parser.add_argument('--create-samples', action='store_true',
                        help='Создать примеры тестовых файлов')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Подробный вывод для неудачных тестов')

    args = parser.parse_args()

    if args.create_samples:
        print("📁 Создаю примеры тестовых файлов...")
        create_sample_tests()
        print("✅ Примеры созданы в папке 'tests/'")
        return

    if not args.student_code:
        parser.print_help()
        print("\n❌ Не указан файл с кодом ученика!")
        return

    try:
        # Создаем тестер и запускаем тесты
        tester = PythonCodeTester(args.student_code, args.test_dir)
        results = tester.run_all_tests()

        # Если нужно, выводим подробную информацию о неудачных тестах
        if args.verbose:
            for result in results:
                if not result['passed']:
                    tester.print_detailed_failure(result)

        # Возвращаем код выхода в зависимости от результатов
        all_passed = all(r['passed'] for r in results if 'passed' in r)
        sys.exit(0 if all_passed else 1)

    except FileNotFoundError as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()