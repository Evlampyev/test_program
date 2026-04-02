data = "оооооо"
count = 4
char = 'о'
i = count - 2
res = 0
while res < count:
    i += 1
    res = data.count(char, 0, i)
print(data[i:])

data = "оооооо"
count = 4
char = 'о'
i = 0
while count != 0:
    if data[i] == char:
        count -= 1
    i = i + 1
print(data[i:])
