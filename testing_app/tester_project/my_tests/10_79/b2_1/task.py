from math import pi

cube_edge, height, diameter, water_volume = map(float, input().split())
v1 = cube_edge ** 3
v2 = height * pi * ((diameter / 2) ** 2)
print(f"Vкуба = {v1}, Vцилиндра =  {v2}")
if (water_volume <= v1) and (water_volume <= v2):
    print("обе")
elif (water_volume <= v1) and (water_volume > v2):
    print("куб")
elif (water_volume > v1) and (water_volume <= v2):
    print("цилиндр")
else:
    print("нигде")
