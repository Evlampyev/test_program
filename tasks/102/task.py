num = int(input())
first = num // 100
second = num % 100 // 10
third = num % 10
print(f"{first}, {second}, {third}")
