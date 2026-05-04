summ = 0

for n in range(1, int(input()) + 1):
    for i in range(1, n):
        if n % i == 0:
            summ += i
    if summ == n:
        print(n, end=" ")
    summ = 0
