def solve():
    a,b  = map (int, input().split())
    print("сумма квадратов =", a*a+b*b)
    print("разность квадратов =", a*a-b*b)
    print("произведение квадратов =", a*a*b*b)
    print("частное квадратов =", round((a*a)/(b*b),5))
    print("среднее арифметическое квадратов =", int((a*a+b*b)/2))




if __name__ == "__main__":
    solve()