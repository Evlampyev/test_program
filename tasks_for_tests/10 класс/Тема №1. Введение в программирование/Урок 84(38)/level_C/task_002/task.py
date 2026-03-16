number = int(input())
delete = int(input())
leng = len(str(number))
total = str("")
count = 0
for i in range(leng, 0, -1):
    first = number // 10 ** (i - 1)
    number = number % 10 ** (i - 1)
    if first == delete:
        count = count + 1
    else:
        total += str(first)
print(total)
