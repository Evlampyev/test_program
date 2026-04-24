from random import randint


def print_matrix(my_list):
    for row in my_list:
        for x in row:
            print(f"{x:4d}", end="")
        print()


matrix = []
n = 5
m = 8
for i in range(n):
    matrix.append([randint(0, 100) for j in range(m)])

print_matrix(matrix)
