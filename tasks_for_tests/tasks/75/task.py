data = list(map(int, input().split()))[::-1]
new=[]
for i in range(len(data) - 1):
    for j in range(i + 1, len(data)):
        if data[i] == data[j]:
            if data[i] not in new:
                new.append(data[i])

if len(new) == 0:
    print("НЕТ")
else:
    print(*new, sep=',')
