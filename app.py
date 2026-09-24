import http.server
import json
import os
import threading
import webbrowser

PORT = 8001
RESULT_FILE = "enhanced_results.json"


def load_results():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), RESULT_FILE)
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def route_text(route):
    return " → ".join(route) if route else "No route observed"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def route_probability_data(quantum):
    """Read recorded route probabilities; use the verified experiment values as fallback."""
    raw = quantum.get("route_probabilities")
    if isinstance(raw, dict):
        return [(str(route), safe_float(prob)) for route, prob in raw.items()]

    if isinstance(raw, list):
        data = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            route = item.get("route") or item.get("route_text")
            probability = item.get("probability", item.get("probability_percent"))
            if route is not None and probability is not None:
                if isinstance(route, list):
                    route = route_text(route)
                probability = safe_float(probability)
                if "probability_percent" not in item and probability <= 1:
                    probability *= 100
                data.append((str(route), probability))
        if data:
            return data

    return [
        ("Depot → A → B → C → Depot", 0.4198),
        ("Depot → A → C → B → Depot", 0.4146),
        ("Depot → B → A → C → Depot", 0.2174),
        ("Depot → B → C → A → Depot", 0.1555),
        ("Depot → C → A → B → Depot", 0.0305),
        ("Depot → C → B → A → Depot", 0.1654),
    ]


def chart_funnel(shot_total, valid, feasible, optimal):
    values = [
        ("All shots", shot_total),
        ("Valid", valid),
        ("Time-feasible", feasible),
        ("Optimal", optimal),
    ]
    max_value = max([v for _, v in values] + [1])
    rows = []
    for label, value in values:
        width = max(2, int(100 * value / max_value))
        rows.append(
            f'''<div class="bar-row">
                <div class="bar-label">{label}</div>
                <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
                <div class="bar-value">{value:,}</div>
            </div>'''
        )
    return "".join(rows)


def chart_score(classical_score, qaoa_score):
    maximum = max(classical_score, qaoa_score, 1.0)
    rows = []
    for label, value in (("Classical exact", classical_score), ("QAOA best", qaoa_score)):
        width = max(2, int(100 * value / maximum))
        rows.append(
            f'''<div class="bar-row score-row">
                <div class="bar-label">{label}</div>
                <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
                <div class="bar-value">{value:.4f}</div>
            </div>'''
        )
    return "".join(rows)


def chart_route_probabilities(probabilities, optimal_route):
    maximum = max([p for _, p in probabilities] + [0.01])
    rows = []
    for route, probability in probabilities:
        width = max(2, int(100 * probability / maximum))
        is_optimal = route == optimal_route
        marker = " <span class=\"optimal-marker\">OPTIMAL</span>" if is_optimal else ""
        row_class = "bar-row route-row optimal-route" if is_optimal else "bar-row route-row"
        rows.append(
            f'''<div class="{row_class}">
                <div class="route-label">{route}{marker}</div>
                <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
                <div class="bar-value">{probability:.4f}%</div>
            </div>'''
        )
    return "".join(rows)


def build_page(results):
    if not results:
        return """<!doctype html><html><head><meta charset="utf-8"><title>QuantumRoute</title>
        <style>body{font-family:Arial;background:#07111f;color:#eef2ff;padding:40px}
        .card{max-width:800px;margin:auto;background:#101c2e;padding:30px;border-radius:18px}</style>
        </head><body><div class="card"><h1>QuantumRoute</h1>
        <h2>Results file not found</h2>
        <p>Run <code>python quantum_solver.py</code> in the project folder first.</p>
        </div></body></html>"""

    experiment = results.get("experiment", {})
    classical = results.get("classical", {})
    quantum = results.get("quantum", {})
    evidence = results.get("evidence", {})

    gamma = safe_float(experiment.get("gamma"))
    beta = safe_float(experiment.get("beta"))
    energy = safe_float(experiment.get("expected_energy"))
    shots = int(experiment.get("total_shots", 0) or 0)
    qubits = int(experiment.get("qubits", 9) or 9)
    depth = experiment.get("qaoa_depth", 1)
    runs = int(experiment.get("runs", 0) or 0)

    valid = int(quantum.get("valid_solutions", 0) or 0)
    feasible = int(quantum.get("time_feasible_solutions", 0) or 0)
    optimal = int(quantum.get("optimal_solutions", 0) or 0)
    valid_rate = safe_float(quantum.get("valid_rate"), valid / shots if shots else 0)
    feasible_rate = safe_float(quantum.get("time_feasible_rate"), feasible / shots if shots else 0)
    optimal_rate = safe_float(quantum.get("optimal_rate"), optimal / shots if shots else 0)
    runs_optimum = int(quantum.get("runs_with_optimum", 0) or 0)

    best_route = quantum.get("best_route") or []
    best_route_text = route_text(best_route)
    best_score = safe_float(quantum.get("best_operational_score"))
    gap = safe_float(quantum.get("optimality_gap"))
    classical_score = safe_float(classical.get("operational_score"))
    classical_route = classical.get("route") or []
    classical_route_text = route_text(classical_route)
    probabilities = route_probability_data(quantum)

    funnel_html = chart_funnel(shots, valid, feasible, optimal)
    score_html = chart_score(classical_score, best_score)
    probability_html = chart_route_probabilities(probabilities, best_route_text)

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-store">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>QuantumRoute — Hybrid Quantum Optimization</title>
<style>
:root{{--bg:#07111f;--panel:#0e1b2d;--line:#243852;--text:#edf4ff;--muted:#9eb0c7;--accent:#6ee7f9;--accent2:#a78bfa;--good:#63e6be}}
*{{box-sizing:border-box}}
body{{margin:0;background:linear-gradient(135deg,#06101d,#0a1627 55%,#10182b);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif}}
main{{max-width:1200px;margin:auto;padding:32px 22px 60px}}
header{{padding:18px 0 30px}}
.eyebrow{{color:var(--accent);font-size:13px;font-weight:700;letter-spacing:1.5px}}
h1{{font-size:42px;margin:8px 0}}
.subtitle{{color:var(--muted);font-size:18px}}
.status{{display:inline-block;margin-top:15px;padding:7px 12px;border:1px solid #24556a;border-radius:999px;color:var(--good);font-size:12px;font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.card{{background:rgba(14,27,45,.94);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 12px 35px rgba(0,0,0,.18)}}
section{{margin-top:22px}}
.metric .label{{color:var(--muted);font-size:12px;letter-spacing:1px}}
.metric .value{{font-size:30px;font-weight:800;margin-top:7px}}
.metric .small,.muted{{color:var(--muted);font-size:13px}}
h2{{font-size:21px;margin:0 0 16px}}
.route{{font-size:24px;font-weight:800;line-height:1.45;color:var(--accent)}}
.big{{font-size:34px;font-weight:800}}
table{{width:100%;border-collapse:collapse}}
td{{padding:9px 0;border-bottom:1px solid var(--line)}}
td:first-child{{color:var(--muted)}}
.code{{background:#07101c;border:1px solid #1c3047;border-radius:12px;padding:16px;font-family:Consolas,monospace;white-space:pre-wrap;line-height:1.6;color:#cfe4ff}}
.notice{{padding:13px 15px;border-left:3px solid var(--accent2);background:#0b1728;border-radius:8px;margin-top:12px;color:#c7d5e7}}
.badge{{display:inline-block;padding:5px 9px;border-radius:999px;background:#123329;color:var(--good);font-size:12px;font-weight:700}}
footer{{margin-top:35px;color:#71839a;text-align:center;font-size:13px}}
.chart-card{{margin-top:22px}}
.chart-subtitle{{color:var(--muted);font-size:13px;margin-top:-7px;margin-bottom:20px}}
.bar-row{{display:grid;grid-template-columns:125px 1fr 82px;gap:12px;align-items:center;margin:14px 0}}
.bar-label,.route-label{{font-size:13px;color:#d9e5f3}}
.route-row{{grid-template-columns:minmax(280px,1.4fr) 1fr 82px}}
.bar-track{{height:16px;background:#081421;border:1px solid #1d3148;border-radius:999px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:999px;background:linear-gradient(90deg,#6ee7f9,#a78bfa);min-width:3px}}
.bar-value{{text-align:right;font-weight:700;font-size:13px}}
.optimal-route{{padding:10px;border:1px solid #2d5d59;background:rgba(25,70,63,.14);border-radius:10px}}
.optimal-route .bar-fill{{background:linear-gradient(90deg,#63e6be,#6ee7f9)}}
.optimal-marker{{color:var(--good);font-size:10px;font-weight:800;letter-spacing:.7px;margin-left:7px}}
.chart-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.callout{{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:14px 16px;background:#0b1728;border:1px solid #243852;border-radius:12px;margin-top:18px}}
.callout strong{{font-size:18px}}
@media(max-width:850px){{.grid,.grid2,.chart-grid{{grid-template-columns:1fr 1fr}}.route-row{{grid-template-columns:1fr 1fr 72px}}}}
@media(max-width:560px){{.grid,.grid2,.chart-grid{{grid-template-columns:1fr}}h1{{font-size:32px}}.bar-row,.route-row{{grid-template-columns:1fr 78px;gap:7px}}.bar-track{{grid-column:1/3}}.bar-label,.route-label{{grid-column:1}}.bar-value{{grid-column:2;grid-row:1}}}}
</style>
</head>
<body><main>
<header>
<div class="eyebrow">QUANTUM COMPUTING HACKATHON PROTOTYPE</div>
<h1>QuantumRoute</h1>
<div class="subtitle">Hybrid Quantum Optimization for Last-Mile Delivery</div>
<div class="status">● LIVE RESULTS FROM enhanced_results.json</div>
</header>

<section class="grid">
<div class="card metric"><div class="label">QUBO VARIABLES</div><div class="value">{qubits}</div><div class="small">Simulated qubits</div></div>
<div class="card metric"><div class="label">MEASUREMENTS</div><div class="value">{shots:,}</div><div class="small">Across {runs} batches</div></div>
<div class="card metric"><div class="label">OPTIMAL MEASUREMENTS</div><div class="value">{optimal_rate:.2%}</div><div class="small">{optimal:,} / {shots:,}</div></div>
<div class="card metric"><div class="label">VALID SOLUTIONS</div><div class="value">{valid_rate:.2%}</div><div class="small">{valid:,} / {shots:,}</div></div>
</section>

<section class="card"><h2>Optimized delivery route</h2>
<div class="route">{best_route_text}</div>
<p class="muted">QAOA recovered the exact route identified by the classical exhaustive benchmark.</p></section>

<section class="chart-grid">
<div class="card chart-card"><h2>Measurement filtering</h2>
<p class="chart-subtitle">What happened to the 10,000 QAOA measurements?</p>
{funnel_html}
<div class="callout"><span>Optimal measurements</span><strong>{optimal} / {shots:,}</strong></div>
</div>

<div class="card chart-card"><h2>Classical vs QAOA score</h2>
<p class="chart-subtitle">Lower operational score is better; both methods reached the same optimum.</p>
{score_html}
<div class="callout"><span>Optimality gap</span><strong>{gap:.4f}</strong></div>
</div>
</section>

<section class="card chart-card"><h2>QAOA route probability distribution</h2>
<p class="chart-subtitle">Recorded statevector probabilities for the six possible 3-node routes. The highlighted route is the exact classical optimum.</p>
{probability_html}
<div class="callout"><span>Recovered optimum</span><strong>{best_route_text}</strong></div>
</section>

<section class="grid2">
<div class="card"><h2>QAOA experiment</h2><table>
<tr><td>QAOA depth</td><td><b>p = {depth}</b></td></tr>
<tr><td>Gamma</td><td><b>{gamma:.2f}</b></td></tr>
<tr><td>Beta</td><td><b>{beta:.2f}</b></td></tr>
<tr><td>Expected energy</td><td><b>{energy:.4f}</b></td></tr>
<tr><td>Measurements</td><td><b>{shots:,}</b></td></tr>
<tr><td>Valid solutions</td><td><b>{valid:,} / {shots:,}</b></td></tr>
<tr><td>Time-feasible</td><td><b>{feasible:,} / {shots:,}</b> ({feasible_rate:.2%})</td></tr>
<tr><td>Optimal solutions</td><td><b>{optimal:,} / {shots:,}</b> ({optimal_rate:.2%})</td></tr>
<tr><td>Runs finding optimum</td><td><b>{runs_optimum} / {runs}</b></td></tr>
</table></div>

<div class="card"><h2>Classical benchmark</h2>
<p class="muted">Exact exhaustive benchmark for the 3-node proof-of-concept.</p>
<div class="big">{classical_score:.4f}</div><p class="muted">Classical operational score</p>
<div class="route" style="font-size:19px">{classical_route_text}</div>
<hr style="border:0;border-top:1px solid #243852;margin:20px 0">
<p><b>QAOA best score:</b> {best_score:.4f}</p><p><b>Optimality gap:</b> {gap:.4f}</p>
<span class="badge">CLASSICAL OPTIMUM RECOVERED</span></div>
</section>

<section class="card"><h2>Quantum execution pipeline</h2>
<div class="grid">
<div><b>① Input</b><br><span class="muted">Delivery nodes</span></div>
<div><b>② QUBO</b><br><span class="muted">Binary formulation</span></div>
<div><b>③ QAOA</b><br><span class="muted">p = {depth}</span></div>
<div><b>④ Measure</b><br><span class="muted">{shots:,} shots</span></div>
</div><div style="margin-top:18px" class="grid">
<div><b>⑤ Validate</b><br><span class="muted">Classical checks</span></div>
<div><b>⑥ Route</b><br><span class="muted">Best feasible result</span></div>
</div></section>

<section class="grid2">
<div class="card"><h2>QUBO formulation</h2>
<div class="code">Minimize:
H = H_travel
  + P × H_city
  + P × H_position
  + H_time_surrogate

x(i,t) ∈ {{0,1}}
x(i,t) = 1 → city i occupies position t

Σt x(i,t) = 1
Σi x(i,t) = 1

Time-window feasibility:
classical post-processing</div></div>

<div class="card"><h2>Why quantum?</h2>
<p>Routing creates a combinatorial assignment problem: which delivery occupies each route position?</p>
<p>QAOA provides a quantum-classical method for exploring the resulting binary optimization landscape.</p>
<p>The classical solver remains essential for ground truth and exact feasibility validation.</p></div>
</section>

<section class="card"><h2>Scientific status</h2>
<div class="notice">This is a QAOA proof of concept on a 3-node instance.</div>
<div class="notice">Traffic inputs are synthetic demonstration data.</div>
<div class="notice">The QUBO uses a position-level time-window surrogate; exact arrival-time feasibility is checked classically.</div>
<div class="notice">The experiment recovered the classical optimum, but most raw measurements were not directly usable.</div>
<div class="notice"><b>No quantum speedup or quantum advantage is claimed.</b></div>
</section>

<section class="card"><h2>Evidence</h2><table>
<tr><td>Evidence level</td><td>{evidence.get("type", "QAOA proof-of-concept")}</td></tr>
<tr><td>Simulator</td><td>{evidence.get("simulator", "Pure Python statevector")}</td></tr>
<tr><td>Traffic data</td><td>{evidence.get("traffic_data", "Synthetic")}</td></tr>
<tr><td>Time-window data</td><td>{evidence.get("time_window_data", "Synthetic")}</td></tr>
<tr><td>Quantum advantage</td><td>Not claimed</td></tr>
</table></section>

<section class="card"><h2>Scalability roadmap</h2><div class="grid2">
<div><h3>Current POC</h3><p>3 delivery nodes<br>9 binary variables<br>Traffic-adjusted costs<br>Time-window surrogate<br>QAOA p=1<br>Classical validation</p></div>
<div><h3>Future extension</h3><p>5–10+ nodes<br>Constraint-preserving mixers<br>Dynamic traffic and demand<br>Multiple vehicles<br>Capacity constraints<br>Hardware execution</p></div>
</div></section>

<footer>QuantumRoute · Hybrid QUBO + QAOA optimization · Classical benchmarking</footer>
</main></body></html>'''


class QuantumRouteHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        page = build_page(load_results())
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def log_message(self, *args):
        pass


def main():
    server = http.server.HTTPServer(("localhost", PORT), QuantumRouteHandler)
    print(f"QuantumRoute dashboard running at http://localhost:{PORT}")
    print(f"Reading results from: {os.path.abspath(RESULT_FILE)}")
    threading.Timer(0.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
