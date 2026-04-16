data = list(map(int, input().split(', ')))
indices = []
for i, num in enumerate(data):
    if num % 3 == 0 and num % 10 == 1:
        indices.append(i)
print(*indices, sep=', ')