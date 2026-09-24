import json
import os


RESULT_FILE = "enhanced_results.json"


def main():

    if not os.path.exists(RESULT_FILE):

        print(
            f"{RESULT_FILE} not found."
        )

        print(
            "Run quantum_solver.py first."
        )

        return

    with open(
        RESULT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        result = json.load(file)

    experiment = result["experiment"]
    classical = result["classical"]
    quantum = result["quantum"]
    evidence = result["evidence"]

    print("=== QuantumRoute Benchmark ===")

    print()
    print("Classical benchmark")
    print(
        "Route:",
        " → ".join(classical["route"]),
    )
    print(
        "Operational score:",
        f"{classical['operational_score']:.10f}",
    )

    print()
    print("QAOA experiment")
    print(
        "Qubits:",
        experiment["qubits"],
    )
    print(
        "Depth:",
        experiment["qaoa_depth"],
    )
    print(
        "Gamma:",
        f"{experiment['gamma']:.2f}",
    )
    print(
        "Beta:",
        f"{experiment['beta']:.2f}",
    )
    print(
        "Expected energy:",
        f"{experiment['expected_energy']:.4f}",
    )

    print()
    print(
        "Shots:",
        experiment["total_shots"],
    )

    print(
        "Valid solutions:",
        f"{quantum['valid_solutions']}"
        f"/{experiment['total_shots']}",
    )

    print(
        "Valid rate:",
        f"{quantum['valid_rate']:.2%}",
    )

    print(
        "Time-feasible solutions:",
        f"{quantum['time_feasible_solutions']}"
        f"/{experiment['total_shots']}",
    )

    print(
        "Time-feasible rate:",
        f"{quantum['time_feasible_rate']:.2%}",
    )

    print(
        "Optimal solutions:",
        f"{quantum['optimal_solutions']}"
        f"/{experiment['total_shots']}",
    )

    print(
        "Optimal rate:",
        f"{quantum['optimal_rate']:.2%}",
    )

    print(
        "Runs finding optimum:",
        f"{quantum['runs_with_optimum']}"
        f"/{experiment['runs']}",
    )

    print()

    if quantum["best_route"]:

        print(
            "Best observed feasible route:",
            " → ".join(
                quantum["best_route"]
            ),
        )

        print(
            "Best operational score:",
            f"{quantum['best_operational_score']:.10f}",
        )

        print(
            "Optimality gap:",
            f"{quantum['optimality_gap']:.10f}",
        )

        print(
            "Time-window feasible:",
            quantum["time_window_report"]["feasible"],
        )

    else:

        print(
            "No time-feasible quantum route observed."
        )

    print()
    print(
        "Evidence level:",
        evidence["type"],
    )

    print(
        "Simulator:",
        evidence["simulator"],
    )

    print(
        "Traffic data:",
        evidence["traffic_data"],
    )

    print(
        "Time-window data:",
        evidence["time_window_data"],
    )

    print(
        "Quantum advantage:",
        "Not claimed",
    )


if __name__ == "__main__":
    main()