from math import sin, cos

a, b, c = map(int, input().split())
res = (sin(a ** 2) / c) + (a / (cos(b)**2))
print(f"{res:.3f}")