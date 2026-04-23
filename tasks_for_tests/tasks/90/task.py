def print_matrix(my_list: list, n: int) -> None:
    for i in range(len(my_list)):
        for j in range(len(my_list[i])):
            print(str(my_list[i][j]).rjust(n + 1, ' '), end="")
        print()


def solve():
    n, m = map(int, input().split())
    data = []
    for _ in range(n):
        data.append([0] * m)
    num = 1
    i = j = 0
    move_l_r = 0
    move_u_d = 0
    res = n * m + 1
    while num < res:
        for x in range(m):
            if j != 0 or i != 0 or x != 0:
                if move_l_r % 2 == 0:
                    j += 1
                else:
                    j -= 1
            data[i][j] = num
            num += 1
        move_l_r += 1
        m -= 1
        for z in range(n - 1):
            if move_u_d % 2 == 0:
                i += 1
            else:
                i -= 1
            data[i][j] = num
            num += 1
        move_u_d += 1
        n -= 1

    print_matrix(data, len(str(res)))


if __name__ == "__main__":
    solve()
