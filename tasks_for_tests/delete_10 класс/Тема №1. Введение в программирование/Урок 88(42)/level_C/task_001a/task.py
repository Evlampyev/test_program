import math


def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)



n = int(input())
result = 0
a, b = map(float, input().split())
for i in range(n):
    c, d = map(float, input().split())
    result += distance(a, b, c, d)
    a, b = c, d
print(f"{result:.2f}")
