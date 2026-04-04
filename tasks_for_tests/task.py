from random import randint

data = [randint(0, 9) for i in range(10)]
print("1)", data)

data.pop(3)
print("1)", data)

