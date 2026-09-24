from qubo import (
    CITIES,
    N,
    TIME_WINDOWS,
    var,
    travel_cost,
)


def decode_route(bits):
    route = []

    for position in range(N):

        selected = [
            city
            for city in CITIES
            if bits[var(city, position)] == 1
        ]

        if len(selected) != 1:
            return None

        route.append(selected[0])

    if len(set(route)) != N:
        return None

    return [
        "Depot",
        *route,
        "Depot",
    ]


def route_times(route):
    current_time = 0.0
    arrivals = {}

    for source, target in zip(route, route[1:]):

        current_time += travel_cost(
            source,
            target,
        )

        if target != "Depot":
            arrivals[target] = current_time

    return arrivals


def time_window_report(route):
    arrivals = route_times(route)

    violations = []

    for city, arrival in arrivals.items():

        earliest, latest = TIME_WINDOWS[city]

        if arrival < earliest:

            violations.append({
                "city": city,
                "arrival": arrival,
                "earliest": earliest,
                "latest": latest,
                "lateness": 0.0,
                "early": earliest - arrival,
            })

        elif arrival > latest:

            violations.append({
                "city": city,
                "arrival": arrival,
                "earliest": earliest,
                "latest": latest,
                "lateness": arrival - latest,
                "early": 0.0,
            })

    return {
        "feasible": len(violations) == 0,
        "arrivals": arrivals,
        "violations": violations,
    }


def route_distance(route):
    return sum(
        travel_cost(source, target)
        for source, target in zip(route, route[1:])
    )


def operational_score(route):
    report = time_window_report(route)

    penalty = 0.0

    for violation in report["violations"]:
        penalty += (
            violation["lateness"] ** 2
            + violation["early"] ** 2
        )

    return route_distance(route) + 8.0 * penalty


def is_valid(bits):
    route = decode_route(bits)

    if route is None:
        return False

    return time_window_report(route)["feasible"]