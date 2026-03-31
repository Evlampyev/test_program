def sum_digit(num):
    ans = 0
    while num > 0:
        ans += num % 10
        num //= 10
    return ans


data = list(map(int, input().split()))


fl = 0
for i in range(0, 36):
    count = 0
    for el in data:
        if sum_digit(el) == i:
            count += 1
    if count > 1:
        print(f"{i} - {count}")
        fl += 1
if fl == 0:
    print("НЕТ")
