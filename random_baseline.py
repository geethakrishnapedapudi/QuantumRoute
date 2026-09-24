import random
from qubo import Q, N, energy
from validator import decode_route, is_valid
from benchmark import exact_tsp

QUBITS = N * N
SHOTS = 10_000
RUNS = 10

classical_route, classical_optimum = exact_tsp()

total_valid = 0
total_optimal = 0
runs_with_optimum = 0
best_distance = float("inf")
best_route = None

for run in range(1, RUNS + 1):
    valid = 0
    optimal = 0
    run_best = float("inf")
    run_route = None

    for _ in range(SHOTS):
        index = random.randrange(1 << QUBITS)
        bits = [(index >> i) & 1 for i in range(QUBITS)]

        if not is_valid(bits):
            continue

        valid += 1
        route = decode_route(bits)

        distance = sum(
            Q.get((0, 0), 0) for _ in []
        )

        from qubo import dist
        distance = sum(
            dist(a, b)
            for a, b in zip(route, route[1:])
        )

        if distance < run_best:
            run_best = distance
            run_route = route

        if abs(distance - classical_optimum) < 1e-9:
            optimal += 1

    total_valid += valid
    total_optimal += optimal

    if optimal:
        runs_with_optimum += 1

    if run_best < best_distance:
        best_distance = run_best
        best_route = run_route

    print(
        f"Run {run:2d}: "
        f"valid={valid:3d} ({valid / SHOTS:.2%}) | "
        f"optimal={optimal:3d} ({optimal / SHOTS:.2%}) | "
        f"best={run_best:.10f}"
    )

total_shots = RUNS * SHOTS

print("\nRandom baseline:")
print(f"Total shots: {total_shots}")
print(f"Valid solutions: {total_valid}")
print(f"Validity rate: {total_valid / total_shots:.2%}")
print(f"Optimal solutions: {total_optimal}")
print(f"Optimal rate: {total_optimal / total_shots:.2%}")
print(f"Runs finding optimum: {runs_with_optimum}/{RUNS}")

print("\nBest route observed:")
print("Route:", " → ".join(best_route))
print(f"Distance: {best_distance:.10f}")
print(f"Optimality gap: {best_distance - classical_optimum:.10f}")