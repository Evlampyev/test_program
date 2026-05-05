from random import randint


def print_matrix(data):
    for row in data:
        for el in row:
            print(f"{el:4d}", end=" ")
        print()


matrix = []
for _ in range(6):
    matrix.append([randint(1,100) for i in range(4)])

print_matrix(matrix)
