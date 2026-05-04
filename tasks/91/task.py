def solve():
    data = []
    for _ in range(4):
        data.append([int(x) for x in input().split()])

    summa = 0
    for i in range(4):
        summa += sum(data[i])

    row_count = len(data[0])
    count = 4 * row_count
    average_value = summa / count
    print(f"{average_value:.2f}")

    for i in range(4):
        for j in range(row_count):
            if data[i][j] < average_value:
                data[i][j] = 0
            else:
                data[i][j] = 255
            print(f"{data[i][j]:4d}", end="")
        print()


if __name__ == "__main__":
    solve()