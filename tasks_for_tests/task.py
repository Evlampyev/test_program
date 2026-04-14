with open("read.me", "r", encoding="UTF-8") as file:
    data =[]
    for line in file:
        data.append(line.strip())

print(data)

with open("write.me", "w", encoding="UTF-8") as file:
    for element in data:
        file.write(f"{element}\n")



