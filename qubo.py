import math

from locations import locations


CITIES = ["A", "B", "C"]
N = len(CITIES)

CONSTRAINT_PENALTY = 100.0
TIME_WINDOW_PENALTY = 8.0


# Synthetic congestion multipliers for the proof of concept.
# 1.0 = normal traffic
# 1.3 = moderate traffic
# 1.6 = severe traffic
TRAFFIC_FACTORS = {
    "Depot": {
        "A": 1.0,
        "B": 1.3,
        "C": 1.0,
    },
    "A": {
        "Depot": 1.0,
        "B": 1.6,
        "C": 1.1,
    },
    "B": {
        "Depot": 1.3,
        "A": 1.6,
        "C": 1.0,
    },
    "C": {
        "Depot": 1.0,
        "A": 1.1,
        "B": 1.0,
    },
}


# Illustrative delivery windows.
# These are synthetic demonstration values, not live traffic data.
TIME_WINDOWS = {
    "A": (0.0, 15.0),
    "B": (5.0, 20.0),
    "C": (10.0, 25.0),
}


# Position-level arrival targets.
#
# This is intentionally a compact surrogate because the current
# 3-city proof of concept must remain a 9-variable QUBO.
#
# Exact arrival-time feasibility is checked classically after
# the quantum state is decoded.
POSITION_TIME_TARGETS = [
    6.0,
    13.0,
    20.0,
]


def dist(a, b):
    x1, y1 = locations[a]
    x2, y2 = locations[b]

    return math.hypot(
        x2 - x1,
        y2 - y1,
    )


def traffic_factor(a, b):
    if a == b:
        return 1.0

    return TRAFFIC_FACTORS.get(a, {}).get(b, 1.0)


def travel_cost(a, b):
    return dist(a, b) * traffic_factor(a, b)


def var(city, position):
    return CITIES.index(city) * N + position


def add(Q, i, j, value):
    i, j = sorted((i, j))

    Q[(i, j)] = Q.get((i, j), 0.0) + value


def window_penalty(city, position):
    target = POSITION_TIME_TARGETS[position]
    earliest, latest = TIME_WINDOWS[city]

    if target < earliest:
        return (earliest - target) ** 2

    if target > latest:
        return (target - latest) ** 2

    return 0.0


def build_qubo():
    Q = {}

    # ---------------------------------------------------------
    # Constraint 1:
    # Every city appears exactly once.
    # ---------------------------------------------------------

    for city in CITIES:

        ids = [
            var(city, position)
            for position in range(N)
        ]

        for i in ids:
            add(
                Q,
                i,
                i,
                -CONSTRAINT_PENALTY,
            )

        for a in range(N):
            for b in range(a + 1, N):
                add(
                    Q,
                    ids[a],
                    ids[b],
                    2 * CONSTRAINT_PENALTY,
                )

    # ---------------------------------------------------------
    # Constraint 2:
    # Every route position contains exactly one city.
    # ---------------------------------------------------------

    for position in range(N):

        ids = [
            var(city, position)
            for city in CITIES
        ]

        for i in ids:
            add(
                Q,
                i,
                i,
                -CONSTRAINT_PENALTY,
            )

        for a in range(N):
            for b in range(a + 1, N):
                add(
                    Q,
                    ids[a],
                    ids[b],
                    2 * CONSTRAINT_PENALTY,
                )

    # ---------------------------------------------------------
    # Travel cost:
    # Depot -> first delivery.
    # ---------------------------------------------------------

    for city in CITIES:

        add(
            Q,
            var(city, 0),
            var(city, 0),
            travel_cost("Depot", city),
        )

    # ---------------------------------------------------------
    # Travel cost:
    # Delivery -> delivery.
    # ---------------------------------------------------------

    for position in range(N - 1):

        for source in CITIES:

            for target in CITIES:

                if source == target:
                    continue

                add(
                    Q,
                    var(source, position),
                    var(target, position + 1),
                    travel_cost(source, target),
                )

    # ---------------------------------------------------------
    # Travel cost:
    # Final delivery -> Depot.
    # ---------------------------------------------------------

    for city in CITIES:

        add(
            Q,
            var(city, N - 1),
            var(city, N - 1),
            travel_cost(city, "Depot"),
        )

    # ---------------------------------------------------------
    # Time-window surrogate.
    #
    # This encourages a city to occupy a route position whose
    # nominal arrival target is compatible with its window.
    #
    # Exact route arrival times are checked later by validator.py.
    # ---------------------------------------------------------

    for city in CITIES:

        for position in range(N):

            penalty = (
                TIME_WINDOW_PENALTY
                * window_penalty(city, position)
            )

            if penalty > 0:

                add(
                    Q,
                    var(city, position),
                    var(city, position),
                    penalty,
                )

    return Q


def energy(bits, Q):
    return sum(
        value * bits[i] * bits[j]
        for (i, j), value in Q.items()
    )


Q = build_qubo()


if __name__ == "__main__":

    print("=== QuantumRoute Enhanced QUBO ===")
    print(f"Delivery nodes       : {N}")
    print(f"Binary variables     : {N * N}")
    print("Traffic-aware cost   : enabled")
    print("Time-window surrogate: enabled")
    print("Exact time validation: classical")
    print(f"QUBO terms           : {len(Q)}")