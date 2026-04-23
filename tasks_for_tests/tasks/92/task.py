def solve():
    data = []
    for _ in range(4):
        data.append([int(x) for x in input().split()])
    iMin = jMin = 0
    iMax = jMax = 0
    for i in range(4):
        for j in range(4):
            if data[i][j] < data[iMin][jMin]:
                iMin = i
                jMin = j
            if data[i][j] > data[iMax][jMax]:
                iMax = i
                jMax = j
    print(f"Min[{iMin},{jMin}]={data[iMin][jMin]}")
    print(f"Max[{iMax},{jMax}]={data[iMax][jMax]}")


if __name__ == "__main__":
    solve()
