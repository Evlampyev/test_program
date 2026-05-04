def solve():
    data = list(map(int, input().split(', ')))
    new_data = [el for el in data if el % 2 == 0]
    if new_data:
        print(len(new_data))
    else:
        print("НЕТ")


if __name__ == "__main__":
    solve()
