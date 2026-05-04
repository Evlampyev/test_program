data = list(map(int, input().split(', ')))

count = 0
i = 0
while count < 2 and i < len(data):
    if data[i] % 5 == 0:
        count += 1
    i += 1
if count == 2:
    print(i-1)
else:
    print(-1)
