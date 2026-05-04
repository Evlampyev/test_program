def arithmetic_mean(a, b, c):
    return f"{(a + b + c) / 3:.1f}"


num_1, num_2, num_3 = map(int, input().split())
print(arithmetic_mean(num_1, num_2, num_3))
