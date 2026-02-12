a, b = map(int, input().split())
print(f"({a}) * ({b}) = ", end="")
minus = ""
if ((a < 0) and (b > 0)) or ((a > 0) and (b < 0)):
    minus = "-"

a, b = abs(a), abs(b)
total = 0
while a > 0:
    total += b
    a -= 1
print(f"{minus}{total}")
