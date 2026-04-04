def solve():
    count = 0
    for i, num in enumerate(arr):
        # Проверяем, является ли число кратным 5
        # Используем abs() для отрицательных чисел
        if isinstance(num, (int, float)) and num % 5 == 0:
            count += 1
            if count == 2:
                return i
    return -1
if __name__ == "__main__":
    solve()