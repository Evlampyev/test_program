data = int(input())
i = 1
result=0
while data > 0:
    if i %2 ==0:
        number = data % 10
        result += number
    data //= 10
    i += 1
print(result)