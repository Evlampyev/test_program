num = int(input())
count = 0
a = 1

while a <= num:
    if num % a == 0:
        print(a, end=" ")
        count += 1
    a += 1
print()
if count == 2:
    print("Простое")
else:
    print("Не простое")
