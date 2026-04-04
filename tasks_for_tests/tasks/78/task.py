data = list(map(int, input().split()))
new_data = [x for x in data if x > 0]
print(sum(new_data), len(new_data))
