import itertools, math
from locations import locations

def dist(a, b):
    x1, y1 = locations[a]; x2, y2 = locations[b]
    return math.hypot(x2 - x1, y2 - y1)

cities = [x for x in locations if x != "Depot"]

best_route, best_distance = None, float("inf")

for perm in itertools.permutations(cities):
    route = ("Depot",) + perm + ("Depot",)
    d = sum(dist(a, b) for a, b in zip(route, route[1:]))
    if d < best_distance:
        best_route, best_distance = route, d

print("Best classical route:", " → ".join(best_route))
print(f"Distance: {best_distance:.2f}")