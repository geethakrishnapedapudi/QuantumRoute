import math
from locations import locations


def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


names = list(locations.keys())

distance_matrix = {}

for from_location in names:
    distance_matrix[from_location] = {}

    for to_location in names:
        distance_matrix[from_location][to_location] = calculate_distance(
            locations[from_location],
            locations[to_location]
        )


for from_location in names:
    print(from_location, distance_matrix[from_location])