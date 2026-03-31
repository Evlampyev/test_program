from random import randint

my_list = [randint(100, 999) for x in range(10)]
big_list = [el for el in my_list if el < 500]
litle_list = [el for el in my_list if el >= 500]
print(sum(big_list) / len(big_list))
print(sum(litle_list) / len(litle_list))

str_data = "Hello, world!"
new_data = str_data.replace('l', '*', 2)
print(new_data)
