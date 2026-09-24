# QuantumRoute

## Hybrid Quantum Optimization for Last-Mile Delivery

QuantumRoute is a hybrid quantum-classical proof-of-concept for optimizing last-mile delivery routes under traffic and time-window constraints.

The project formulates a small vehicle-routing problem as a **QUBO (Quadratic Unconstrained Binary Optimization)** model and solves it using a custom **QAOA (Quantum Approximate Optimization Algorithm)** statevector simulator.

The quantum result is validated against an **exact classical exhaustive-search baseline**.

> **Scientific note:** This project does not claim quantum advantage or quantum speedup. It demonstrates how a routing problem can be formulated for quantum optimization and experimentally evaluated against a classical baseline.

---

## Problem

Last-mile delivery routing becomes difficult as the number of delivery locations and operational constraints increases.

A practical route may need to consider:

- Travel distance
- Traffic conditions
- Delivery time windows
- Route ordering
- Operational feasibility

QuantumRoute explores whether a quantum optimization formulation can represent these routing decisions in a compact QUBO model.

---

## Solution

QuantumRoute uses a hybrid workflow:

```text
Delivery Data
      ↓
Classical Preprocessing
      ↓
QUBO Formulation
      ↓
QAOA Quantum Simulation
      ↓
Measurement
      ↓
Classical Route Decoding
      ↓
Time-Window Validation
      ↓
Operational Result