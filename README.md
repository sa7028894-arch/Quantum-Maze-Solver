# Quantum Maze Solver — Web App

Full-stack version of the Quantum Maze Solver: a Flask backend that runs
real Qiskit circuits, and a browser frontend that calls it.

- **Backend** (`app.py`, `maze.py`, `quantum_solver.py`): generates mazes,
  runs classical BFS, and builds + executes actual Grover's algorithm
  circuits on Qiskit's Aer simulator.
- **Frontend** (`static/index.html`): renders the maze on canvas, calls the
  backend's JSON API, and animates the round-by-round probability
  amplification as Grover's algorithm runs.

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deploying to get a public URL

See [DEPLOY.md](DEPLOY.md) for step-by-step instructions (Render, Railway,
PythonAnywhere).

## API

| Endpoint | Description |
|---|---|
| `GET /api/maze?size=8&seed=42` | Generates a maze, returns its walls, start/exit, and the classical BFS shortest path |
| `GET /api/grover?size=8&seed=42&shots=2048` | Runs a real Qiskit Grover search for the exit cell; returns round-by-round probabilities and the final measurement histogram |

Both endpoints accept `size` of `4`, `8`, or `16`.
