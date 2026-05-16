from random import randint

def print_matrix(matrix):
    count=4
    for row in matrix:
        for el in row:
            print("{:count}".format(el), end="")
        print()


n, m = 13, 8
data = []
for i in range(n):
    data.append([randint(0, 140) for j in range(m)])

print_matrix(data)
