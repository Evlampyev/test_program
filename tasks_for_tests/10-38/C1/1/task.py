a = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
b = 1
for i in range(0, 11):
    b = a[i]
    print(f'{a[i]} - ', end='')
    while b > 1:
        if b % 2 == 0:
            b = b / 2
            print(f"|{int(b)}|", end=' ')
        else:
            b = (b * 3 + 1) / 2
            print(f"|{int(b)}|", end=' ')
    print()
