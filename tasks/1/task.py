result = 0
for _ in range(int(input())):
    x, y = map(int, input().split())
    result += x * y
print(result)
