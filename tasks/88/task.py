n = int(input())
data = [int(x) for x in input().split()]

print(*data[:n], sep='*')
print(*data[n:], sep='*')