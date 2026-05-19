a = int(input())
factorial = 1
for i in range(1, a + 1):
    factorial *= i
print(f"{a}! = {factorial}")