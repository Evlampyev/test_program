n = int(input())
total = 0
F, Fn = 0, 1
while n > Fn:
    F, Fn = Fn, F + Fn
    total += F
print(total)
