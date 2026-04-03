data = "Молоко_-_это_очень_вкусно_и_полезно"
count = 4
char = 'о'
temp = 0

for i in range(count):
    temp = data.find(char, temp + 1, len(data) - 1)

print(data[temp + 1:])
