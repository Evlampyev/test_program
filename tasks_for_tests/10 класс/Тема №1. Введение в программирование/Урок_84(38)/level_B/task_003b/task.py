a, b = map(int, input().split())

for number in range(a, b + 1):
    number_divisors = 0
    print(f"{number}:", end=" ")
    for divisor in range(2, number):
        if number % divisor == 0:
            number_divisors += 1
            print(divisor, end=" ")
    if number_divisors == 0:
        print("простое")
    print()
