def sum_digit(num):
    temp = [int(i) for i in str(num)]
    return sum(temp)


data = [int(i) for i in input().split()]
maks = 0
i_maks = -1
for i, el in enumerate(data):
    sum_dig = sum_digit(el)
    if sum_dig > sum_digit(maks):
        maks = el
        i_maks = i

print(maks, i_maks)
