def print_matrix(matrix, count):
    for row in matrix:
        for el in row:
            print(f"{el:{count}d}", end="")
        print()


n, m = map(int, input().split())
data = [[0] * m for _ in range(n)]

num = 1
col = 0
direction = 1
while num <= n * m:
    if direction == 1:
        for i in range(n):
            data[i][col] = num
            num += 1
    else:
        for i in range(n - 1, -1, -1):
            data[i][col] = num
            num += 1
    col += 1
    direction *= -1

print_matrix(data, len(str(n * m)) + 1)
