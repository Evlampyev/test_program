
summ =0
for n in range(1, 10001):
    for i in range(1, n):
        if n % i == 0:
            summ +=i
    if summ == n:
        print(f"{n} - perfect!")
    summ=0