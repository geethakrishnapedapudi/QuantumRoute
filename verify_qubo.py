from itertools import product
from qubo import Q, N, CITIES, var, energy

best = (None, float("inf"))

for bits in product([0, 1], repeat=N * N):
    e = energy(bits, Q)
    if e < best[1]:
        best = (bits, e)

bits, e = best

route = []
valid = True

for t in range(N):
    selected = [city for city in CITIES if bits[var(city, t)]]
    if len(selected) != 1:
        valid = False
    else:
        route.append(selected[0])

print("Best QUBO energy:", round(e, 4))
print("Valid route:", valid)

if valid:
    print("Route:", "Depot → " + " → ".join(route) + " → Depot")