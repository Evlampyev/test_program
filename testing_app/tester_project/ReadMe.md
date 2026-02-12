🚀 Использование
1. Базовое тестирование c папкой тестов по умолчанию (tests) и выводом результатов в консоль tests
   >python tester.py student_code.py
2. Тестирование с другой папкой тестов
   >python tester.py student_code.py my_tests/
3. Подробный вывод для неудачных тестов
   >python tester.py student_code.py --verbose
4. Создание примеров тестов
    >python tester.py --create-samples
5. Использование в другой программе
   ```python
   from tester import PythonCodeTester
      
   tester = PythonCodeTester("student_code.py", "tests")
   results = tester.run_all_tests()
    ```
📊 Особенности работы
1. Безопасность: Код ученика запускается в изолированном процессе

2. Таймаут: Программа ограничена 5 секундами на выполнение

3. Нормализация вывода: Убираются лишние пробелы и пустые строки

4. Гибкость: Поддерживаются разные форматы тестовых файлов

5. Подробные отчеты: Показывается, что пошло не так