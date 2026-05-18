from math import sqrt

a, b, c = map(int, input().split())

print("корень из суммы квадратов =", round(sqrt(a * a + b * b + c * c), 3))
print("корень из квадрата суммы =", round(sqrt((a + b + c) * (a + b + c)), 3))
print("корень из произведения квадратов =", round(sqrt(a * a * b * b * c * c), 3))
print("корень из квадрата произведения =", round(sqrt((a * b * c) * (a * b * c)), 3))
print("корень из среднего арифметического квадратов =", round(sqrt((a * a + b * b + c * c) / 3), 3))