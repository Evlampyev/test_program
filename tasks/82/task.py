def solve():
    data = list(map(int, input().split(',')))
    ans = []
    for i in range(1, len(data)):
        if data[i] == data[0]:
            ans.append(i)
    if ans:
        print(*ans, sep=":")
    else:
        print("НЕТ")


if __name__ == "__main__":
    solve()
