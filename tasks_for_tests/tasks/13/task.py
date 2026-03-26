def sum_two_numbers (a,b):
    return a + b

first = int(input())
second = 0
while first != 0:
    second = sum_two_numbers(first, second)
    first = int(input())
print(second)
