import itertools
import json

from qubo import CITIES
from validator import (
    operational_score,
    route_distance,
    time_window_report,
)


RESULT_FILE = "classical_results.json"


def exact_tsp():
    """
    Exhaustively evaluate every possible delivery-node permutation.

    Only time-window-feasible routes are eligible for the
    classical optimum.
    """

    all_routes = []
    feasible_routes = []

    for permutation in itertools.permutations(CITIES):
        route = (
            "Depot",
            *permutation,
            "Depot",
        )

        report = time_window_report(route)
        travel_cost = route_distance(route)
        score = operational_score(route)

        route_result = {
            "route": list(route),
            "travel_cost": travel_cost,
            "operational_score": score,
            "time_window_feasible": report["feasible"],
            "arrivals": report["arrivals"],
            "violations": report["violations"],
        }

        all_routes.append(route_result)

        if report["feasible"]:
            feasible_routes.append(route_result)

    if not feasible_routes:
        raise RuntimeError(
            "No time-window-feasible route exists."
        )

    best = min(
        feasible_routes,
        key=lambda item: item["operational_score"],
    )

    return (
        best["route"],
        best["operational_score"],
        all_routes,
    )


def print_route_table(all_routes, best_route):
    print()
    print("=== All Classical Routes ===")
    print()

    print(
        f"{'Route':<43}"
        f"{'Cost':>14}"
        f"{'Feasible':>12}"
        f"{'Optimal':>10}"
    )

    print("-" * 79)

    for result in all_routes:
        route_text = " → ".join(result["route"])

        feasible = (
            "YES"
            if result["time_window_feasible"]
            else "NO"
        )

        optimal = (
            "YES"
            if result["route"] == best_route
            else ""
        )

        print(
            f"{route_text:<43}"
            f"{result['travel_cost']:>14.4f}"
            f"{feasible:>12}"
            f"{optimal:>10}"
        )

    print()


def main():
    (
        best_route,
        best_score,
        all_routes,
    ) = exact_tsp()

    best_result = next(
        item
        for item in all_routes
        if item["route"] == best_route
    )

    result = {
        "method": (
            "Exact exhaustive enumeration "
            "of all delivery-node permutations"
        ),
        "delivery_nodes": [
            "A",
            "B",
            "C",
        ],
        "number_of_routes": len(all_routes),
        "number_of_feasible_routes": sum(
            item["time_window_feasible"]
            for item in all_routes
        ),
        "route": best_route,
        "operational_score": best_score,
        "travel_cost": best_result["travel_cost"],
        "time_window_feasible": (
            best_result["time_window_feasible"]
        ),
        "arrivals": best_result["arrivals"],
        "violations": best_result["violations"],
        "all_routes": all_routes,
    }

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=2,
        )

    print("=== Exact Classical Benchmark ===")

    print(
        "Routes evaluated:",
        len(all_routes),
    )

    print(
        "Feasible routes:",
        result["number_of_feasible_routes"],
    )

    print(
        "Route:",
        " → ".join(best_route),
    )

    print(
        f"Traffic-adjusted cost: "
        f"{best_result['travel_cost']:.10f}"
    )

    print(
        f"Operational score: "
        f"{best_score:.10f}"
    )

    print(
        "Time-window feasible:",
        best_result["time_window_feasible"],
    )

    print_route_table(
        all_routes,
        best_route,
    )

    print(
        "Saved:",
        RESULT_FILE,
    )


if __name__ == "__main__":
    main()