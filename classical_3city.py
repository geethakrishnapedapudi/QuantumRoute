import itertools
import math
from locations import locations

CITIES = ["A", "B", "C"]


def dist(a, b):
    x1, y1 = locations[a]
    x2, y2 = locations[b]
    return math.hypot(x2 - x1, y2 - y1)


best_route = None
best_distance = float("inf")

for permutation in itertools.permutations(CITIES):
    route = ("Depot",) + permutation + ("Depot",)

    distance = sum(
        dist(a, b)
        for a, b in zip(route, route[1:])
    )

    if distance < best_distance:
        best_route = route
        best_distance = distance


print(
    "Best 3-city classical route:",
    " → ".join(best_route)
)
print(f"Distance: {best_distance:.4f}")