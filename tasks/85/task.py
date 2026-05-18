data = [int(i) for i in input().split()]

result = True
for i in range(len(data)):
    if -15 > data[i] or data[i] > 20:
        result = False
    data[i] *= 3
print(result)
print(data)
