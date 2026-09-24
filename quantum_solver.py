import cmath
import json
import math
import random

from benchmark import exact_tsp
from qubo import (
    N,
    Q,
    energy,
)
from validator import (
    decode_route,
    operational_score,
    route_distance,
    time_window_report,
)


QUBITS = N * N
STATES = 1 << QUBITS

SHOTS = 1000
RUNS = 10

RESULT_FILE = "enhanced_results.json"

GAMMA_VALUES = [
    step * 0.02
    for step in range(1, 101)
]

BETA_VALUES = [
    step * 0.02
    for step in range(1, 51)
]

TOP_CANDIDATES = 20


def bits_from_index(index):
    return [
        (index >> i) & 1
        for i in range(QUBITS)
    ]


def cost(bits):
    return energy(bits, Q)


def qaoa(gamma, beta):
    state = [
        1 / math.sqrt(STATES)
        for _ in range(STATES)
    ]

    for index in range(STATES):
        bits = bits_from_index(index)

        state[index] *= cmath.exp(
            -1j * gamma * cost(bits)
        )

    cos_beta = math.cos(beta)
    minus_i_sin_beta = -1j * math.sin(beta)

    for qubit in range(QUBITS):
        new_state = state[:]

        for index in range(STATES):
            partner = index ^ (1 << qubit)

            new_state[index] = (
                cos_beta * state[index]
                + minus_i_sin_beta * state[partner]
            )

        state = new_state

    return state


def expected_energy(state):
    total = 0.0

    for index, amplitude in enumerate(state):
        probability = abs(amplitude) ** 2

        total += (
            probability
            * cost(bits_from_index(index))
        )

    return total


def state_quality(state, classical_score):
    valid_probability = 0.0
    feasible_probability = 0.0
    optimal_probability = 0.0

    for index, amplitude in enumerate(state):
        probability = abs(amplitude) ** 2

        if probability <= 0.0:
            continue

        bits = bits_from_index(index)
        route = decode_route(bits)

        if route is None:
            continue

        valid_probability += probability

        report = time_window_report(route)

        if not report["feasible"]:
            continue

        feasible_probability += probability

        score = operational_score(route)

        if abs(score - classical_score) < 1e-9:
            optimal_probability += probability

    return {
        "valid_probability": valid_probability,
        "feasible_probability": feasible_probability,
        "optimal_probability": optimal_probability,
    }


def route_probability_distribution(
    state,
    all_routes,
):
    """
    Calculate the exact statevector probability assigned
    to each of the six classical routes.
    """

    probabilities = {
        tuple(result["route"]): 0.0
        for result in all_routes
    }

    for index, amplitude in enumerate(state):
        probability = abs(amplitude) ** 2

        if probability <= 0.0:
            continue

        bits = bits_from_index(index)
        route = decode_route(bits)

        if route is None:
            continue

        route_key = tuple(route)

        if route_key in probabilities:
            probabilities[route_key] += probability

    distribution = []

    for result in all_routes:
        route_key = tuple(result["route"])

        distribution.append({
            "route": result["route"],
            "probability": probabilities[route_key],
            "time_window_feasible": (
                result["time_window_feasible"]
            ),
            "travel_cost": result["travel_cost"],
            "operational_score": (
                result["operational_score"]
            ),
            "optimal": (
                result["route"]
                == all_routes[
                    0
                ]["route"]
            ),
        })

    return distribution


def optimize_qaoa(classical_score):
    candidates = []

    total_candidates = (
        len(GAMMA_VALUES)
        * len(BETA_VALUES)
    )

    print(
        f"Searching {total_candidates} "
        "QAOA parameter pairs..."
    )

    for gamma in GAMMA_VALUES:
        for beta in BETA_VALUES:
            state = qaoa(
                gamma,
                beta,
            )

            current_energy = expected_energy(
                state
            )

            candidates.append({
                "gamma": gamma,
                "beta": beta,
                "expected_energy": current_energy,
                "state": state,
            })

    candidates.sort(
        key=lambda candidate:
        candidate["expected_energy"]
    )

    finalists = candidates[
        :TOP_CANDIDATES
    ]

    evaluated = []

    for candidate in finalists:
        quality = state_quality(
            candidate["state"],
            classical_score,
        )

        evaluated.append({
            **candidate,
            **quality,
        })

    evaluated.sort(
        key=lambda candidate: (
            -candidate["optimal_probability"],
            -candidate["feasible_probability"],
            candidate["expected_energy"],
        )
    )

    best = evaluated[0]

    return (
        best["expected_energy"],
        best["gamma"],
        best["beta"],
        best["state"],
        {
            "grid_size": total_candidates,
            "candidates_checked": total_candidates,
            "top_energy_candidates": TOP_CANDIDATES,
            "selected_valid_probability": (
                best["valid_probability"]
            ),
            "selected_feasible_probability": (
                best["feasible_probability"]
            ),
            "selected_optimal_probability": (
                best["optimal_probability"]
            ),
        },
    )


def sample_state(state, shots):
    probabilities = [
        abs(amplitude) ** 2
        for amplitude in state
    ]

    cumulative = []
    total = 0.0

    for probability in probabilities:
        total += probability
        cumulative.append(total)

    samples = []

    for _ in range(shots):
        random_value = random.random()

        low = 0
        high = len(cumulative) - 1

        while low < high:
            middle = (low + high) // 2

            if random_value <= cumulative[middle]:
                high = middle
            else:
                low = middle + 1

        samples.append(low)

    return samples


def run_experiment(
    state,
    classical_score,
):
    total_valid = 0
    total_time_feasible = 0
    total_optimal = 0

    runs_with_optimum = 0

    best_route = None
    best_score = float("inf")
    best_distance = float("inf")

    batch_results = []

    for run in range(1, RUNS + 1):
        samples = sample_state(
            state,
            SHOTS,
        )

        valid = 0
        time_feasible = 0
        optimal = 0

        run_best_route = None
        run_best_score = float("inf")

        for index in samples:
            bits = bits_from_index(index)
            route = decode_route(bits)

            if route is None:
                continue

            valid += 1

            report = time_window_report(route)

            if report["feasible"]:
                time_feasible += 1

            score = operational_score(route)

            if (
                report["feasible"]
                and score < run_best_score
            ):
                run_best_score = score
                run_best_route = route

            if (
                report["feasible"]
                and abs(score - classical_score) < 1e-9
            ):
                optimal += 1

        total_valid += valid
        total_time_feasible += time_feasible
        total_optimal += optimal

        if optimal > 0:
            runs_with_optimum += 1

        if (
            run_best_route is not None
            and run_best_score < best_score
        ):
            best_score = run_best_score
            best_route = run_best_route
            best_distance = route_distance(
                run_best_route
            )

        batch_results.append({
            "run": run,
            "shots": SHOTS,
            "valid": valid,
            "time_feasible": time_feasible,
            "optimal": optimal,
            "best_route": run_best_route,
            "best_score": (
                run_best_score
                if run_best_route is not None
                else None
            ),
        })

    return {
        "shots_per_run": SHOTS,
        "runs": RUNS,
        "total_shots": SHOTS * RUNS,
        "total_valid": total_valid,
        "total_time_feasible": total_time_feasible,
        "total_optimal": total_optimal,
        "runs_with_optimum": runs_with_optimum,
        "best_route": best_route,
        "best_score": (
            best_score
            if best_route is not None
            else None
        ),
        "best_distance": (
            best_distance
            if best_route is not None
            else None
        ),
        "batches": batch_results,
    }


def main():
    (
        classical_route,
        classical_score,
        all_routes,
    ) = exact_tsp()

    (
        best_energy,
        gamma,
        beta,
        state,
        optimization_info,
    ) = optimize_qaoa(
        classical_score
    )

    experiment = run_experiment(
        state,
        classical_score,
    )

    route_distribution = route_probability_distribution(
        state,
        all_routes,
    )

    total_shots = experiment["total_shots"]

    valid_rate = (
        experiment["total_valid"]
        / total_shots
    )

    feasible_rate = (
        experiment["total_time_feasible"]
        / total_shots
    )

    optimal_rate = (
        experiment["total_optimal"]
        / total_shots
    )

    best_route = experiment["best_route"]

    if best_route is not None:
        best_score = experiment["best_score"]

        optimality_gap = (
            best_score - classical_score
        )

        best_report = time_window_report(
            best_route
        )

    else:
        best_score = None
        optimality_gap = None
        best_report = None

    for route_result in route_distribution:
        route_result["optimal"] = (
            route_result["route"]
            == classical_route
        )

    result = {
        "experiment": {
            "qubits": QUBITS,
            "qaoa_depth": 1,
            "gamma": gamma,
            "beta": beta,
            "expected_energy": best_energy,
            "shots_per_run": SHOTS,
            "runs": RUNS,
            "total_shots": total_shots,
            "parameter_search": {
                "gamma_min": min(GAMMA_VALUES),
                "gamma_max": max(GAMMA_VALUES),
                "gamma_step": (
                    GAMMA_VALUES[1]
                    - GAMMA_VALUES[0]
                ),
                "beta_min": min(BETA_VALUES),
                "beta_max": max(BETA_VALUES),
                "beta_step": (
                    BETA_VALUES[1]
                    - BETA_VALUES[0]
                ),
                "grid_size": (
                    optimization_info["grid_size"]
                ),
                "top_energy_candidates": (
                    optimization_info[
                        "top_energy_candidates"
                    ]
                ),
            },
            "selected_state_quality": {
                "valid_probability": (
                    optimization_info[
                        "selected_valid_probability"
                    ]
                ),
                "feasible_probability": (
                    optimization_info[
                        "selected_feasible_probability"
                    ]
                ),
                "optimal_probability": (
                    optimization_info[
                        "selected_optimal_probability"
                    ]
                ),
            },
        },
        "classical": {
            "route": classical_route,
            "operational_score": classical_score,
            "all_routes": all_routes,
        },
        "quantum": {
            "best_route": best_route,
            "best_operational_score": best_score,
            "best_travel_cost": (
                experiment["best_distance"]
            ),
            "optimality_gap": optimality_gap,
            "valid_solutions": (
                experiment["total_valid"]
            ),
            "valid_rate": valid_rate,
            "time_feasible_solutions": (
                experiment["total_time_feasible"]
            ),
            "time_feasible_rate": feasible_rate,
            "optimal_solutions": (
                experiment["total_optimal"]
            ),
            "optimal_rate": optimal_rate,
            "runs_with_optimum": (
                experiment["runs_with_optimum"]
            ),
            "time_window_report": best_report,
            "route_probability_distribution": (
                route_distribution
            ),
        },
        "batches": experiment["batches"],
        "evidence": {
            "type": "QAOA proof-of-concept",
            "simulator": "Pure Python statevector",
            "quantum_advantage_claimed": False,
            "traffic_data": "Synthetic",
            "time_window_data": "Synthetic",
            "time_window_qaoa_model": (
                "Position-level surrogate"
            ),
            "exact_time_validation": (
                "Classical post-processing"
            ),
            "parameter_selection": (
                "Expected-energy search followed "
                "by feasible/optimal probability "
                "screening among low-energy candidates"
            ),
        },
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

    print()
    print("=== QuantumRoute Enhanced QAOA ===")
    print(f"Qubits: {QUBITS}")
    print("QAOA depth: p=1")
    print(f"Gamma: {gamma:.2f}")
    print(f"Beta: {beta:.2f}")

    print(
        f"Expected energy: "
        f"{best_energy:.4f}"
    )

    print()
    print(
        "Parameter search:",
        f"{optimization_info['grid_size']} pairs",
    )

    print(
        "Top energy candidates:",
        optimization_info[
            "top_energy_candidates"
        ],
    )

    print(
        "Selected feasible state probability:",
        f"{optimization_info['selected_feasible_probability']:.4%}",
    )

    print(
        "Selected optimal state probability:",
        f"{optimization_info['selected_optimal_probability']:.4%}",
    )

    print()
    print(
        f"Total shots: {total_shots}"
    )

    print(
        f"Valid solutions: "
        f"{experiment['total_valid']}"
        f"/{total_shots}"
        f" ({valid_rate:.2%})"
    )

    print(
        f"Time-feasible solutions: "
        f"{experiment['total_time_feasible']}"
        f"/{total_shots}"
        f" ({feasible_rate:.2%})"
    )

    print(
        f"Optimal solutions: "
        f"{experiment['total_optimal']}"
        f"/{total_shots}"
        f" ({optimal_rate:.2%})"
    )

    print(
        f"Runs finding optimum: "
        f"{experiment['runs_with_optimum']}/{RUNS}"
    )

    print()

    if best_route:
        print(
            "Best feasible route:",
            " → ".join(best_route),
        )

        print(
            f"Operational score: "
            f"{best_score:.10f}"
        )

        print(
            f"Optimality gap: "
            f"{optimality_gap:.10f}"
        )

        print(
            "Time-window feasible:",
            best_report["feasible"],
        )

    else:
        print(
            "No time-feasible quantum route "
            "was observed."
        )

    print()
    print("=== Quantum Route Probabilities ===")

    for route_result in route_distribution:
        route_text = " → ".join(
            route_result["route"]
        )

        status = (
            "FEASIBLE"
            if route_result[
                "time_window_feasible"
            ]
            else "INFEASIBLE"
        )

        optimal = (
            " | OPTIMAL"
            if route_result["optimal"]
            else ""
        )

        print(
            f"{route_text:<43}"
            f"{route_result['probability']:>10.4%}"
            f"  {status}"
            f"{optimal}"
        )

    print()
    print(
        "Saved:",
        RESULT_FILE,
    )

    print(
        "Quantum advantage: NOT CLAIMED"
    )


if __name__ == "__main__":
    main()