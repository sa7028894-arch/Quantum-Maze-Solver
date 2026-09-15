#!/usr/bin/env python3
"""
app.py
-------
Flask backend for the Quantum Maze Solver web app.

Two API endpoints:
  GET /api/maze    -- generates a maze + classical BFS path (no quantum work)
  GET /api/grover  -- runs REAL Qiskit circuits (Aer simulator) to find the
                      maze exit via Grover's algorithm, and returns the
                      round-by-round probability progression plus final
                      measurement histogram.

The frontend (static/index.html) calls these endpoints and renders the
results -- all quantum computation happens here on the server via Qiskit,
not in client-side JavaScript.
"""

import os
from flask import Flask, jsonify, request, send_from_directory

from maze import generate_maze
from quantum_solver import run_grover_search, run_grover_progressive, optimal_iterations

app = Flask(__name__, static_folder="static", static_url_path="")

MAX_QUBITS = 8  # cap search space (size<=16 => 8 qubits => 256 states) to keep response times reasonable


def maze_to_json(maze, path):
    size = maze.size
    edges = []
    for r in range(size):
        for c in range(size):
            if c + 1 < size:
                edges.append({"a": [r, c], "b": [r, c + 1], "open": not maze.is_wall((r, c), (r, c + 1))})
            if r + 1 < size:
                edges.append({"a": [r, c], "b": [r + 1, c], "open": not maze.is_wall((r, c), (r + 1, c))})
    return {
        "size": size,
        "start": list(maze.start),
        "exit": list(maze.exit),
        "edges": edges,
        "path": [list(p) for p in path] if path else None,
        "qubits": maze.total_qubits(),
    }


def parse_size_seed():
    size = int(request.args.get("size", 8))
    seed = int(request.args.get("seed", 42))
    if size not in (4, 8, 16):
        size = 8
    n_qubits = 2 * (size - 1).bit_length()
    if n_qubits > MAX_QUBITS:
        size = 8
    return size, seed


@app.route("/api/maze")
def api_maze():
    size, seed = parse_size_seed()
    maze = generate_maze(size=size, seed=seed)
    path = maze.bfs_shortest_path()
    return jsonify(maze_to_json(maze, path))


@app.route("/api/grover")
def api_grover():
    size, seed = parse_size_seed()
    shots = min(4096, max(256, int(request.args.get("shots", 2048))))

    maze = generate_maze(size=size, seed=seed)
    n_qubits = maze.total_qubits()
    n_total = 2 ** n_qubits
    exit_bits = maze.cell_to_bitstring(maze.exit)

    iters = optimal_iterations(n_total, 1)

    # Round-by-round progression (real Qiskit circuits, one per round count)
    progressive_shots = max(256, shots // 4)
    progression = run_grover_progressive(n_qubits, [exit_bits], shots=progressive_shots, max_iterations=iters)

    # Final, full-shot run for the histogram
    counts, circuit, iters_used = run_grover_search(n_qubits, [exit_bits], shots=shots, iterations=iters)
    marked_total = counts.get(exit_bits, 0)
    final_prob = 100 * marked_total / shots
    classical_baseline = 100 / n_total
    top_states = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:8]

    return jsonify({
        "n_qubits": n_qubits,
        "n_total": n_total,
        "exit_bits": exit_bits,
        "iterations": iters_used,
        "shots": shots,
        "circuit_depth": circuit.depth(),
        "progression": [{"round": r, "prob": p} for r, p in progression],
        "top_states": [{"bits": b, "count": c, "prob": 100 * c / shots} for b, c in top_states],
        "final_prob": final_prob,
        "classical_baseline": classical_baseline,
        "amplification": (final_prob / classical_baseline) if classical_baseline > 0 else None,
        "classical_expected_tries": n_total,
    })


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
