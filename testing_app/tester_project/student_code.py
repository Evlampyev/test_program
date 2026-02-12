# Пример простой программы ученика
def main():
    try:
        # Чтение входных данных
        data = input().strip()

        if ' ' in data:
            # Если есть пробел - суммируем два числа
            a, b = map(int, data.split())
            print(a + b)
        else:
            # Иначе проверяем четность
            n = int(data)
            if n % 2 == 0:
                print("Четное")
            else:
                print("Нечетное")
    except:
        print("Ошибка ввода")

if __name__ == "__main__":
    main()