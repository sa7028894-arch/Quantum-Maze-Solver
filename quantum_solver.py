quantum_solver.py
Implements Grover's search algorithm (via Qiskit) to solve the "find the
valid path cells in the maze" problem.

Approach

Every cell of the NxN maze is encoded as a basis state of n = 2*log2(N)
qubits (row bits followed by column bits). The classical BFS solution
(maze.bfs_shortest_path) tells us which cells are "marked" -- i.e. lie
on the shortest path from start to exit.

We then build a Grover oracle that flips the phase of exactly those
marked basis states, build the standard Grover diffusion operator, and
repeat (oracle -> diffusion) for the optimal number of iterations:

    r ~= floor( (pi/4) * sqrt(N_total / N_marked) )

Measuring the resulting state amplifies the probability of the marked
(path) cells far above the 1/N_total baseline of unstructured classical
random guessing -- this is the quantum speedup Grover's algorithm
provides for unstructured search problems.


import math
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import MCMTGate, ZGate
from qiskit_aer import AerSimulator


def build_oracle(n_qubits, marked_bitstrings):
    """Builds a phase-flip oracle that marks each bitstring in
    marked_bitstrings (list of strings like '0101') by flipping its
    phase (multiplying its amplitude by -1)."""
    qc = QuantumCircuit(n_qubits, name="Oracle")
    for bitstring in marked_bitstrings:
       
        bits = bitstring[::-1]
        zero_positions = [i for i, b in enumerate(bits) if b == "0"]

        
        for i in zero_positions:
            qc.x(i)

       
        if n_qubits == 1:
            qc.z(0)
        else:
            qc.append(MCMTGate(ZGate(), n_qubits - 1, 1), list(range(n_qubits)))

      
        for i in zero_positions:
            qc.x(i)
        qc.barrier()
    return qc


def build_diffuser(n_qubits):
    """Standard Grover diffusion operator: inversion about the mean."""
    qc = QuantumCircuit(n_qubits, name="Diffuser")
    qc.h(range(n_qubits))
    qc.x(range(n_qubits))
    if n_qubits == 1:
        qc.z(0)
    else:
        qc.append(MCMTGate(ZGate(), n_qubits - 1, 1), list(range(n_qubits)))
    qc.x(range(n_qubits))
    qc.h(range(n_qubits))
    return qc


def run_grover_progressive(n_qubits, marked_bitstrings, shots=1024, max_iterations=None):
    
    Runs Grover's algorithm separately for iteration counts 0, 1, 2, ...
    up to max_iterations, returning the probability of measuring a marked
    state at each step. This lets a live demo show the amplitude
    amplification build up round by round, instead of only the final
    result.

    Returns: list of (iteration_count, probability_percent) tuples.
    
    n_total = 2 ** n_qubits
    if max_iterations is None:
        max_iterations = optimal_iterations(n_total, len(marked_bitstrings))

    results = []
    for i in range(max_iterations + 1):
        counts, _, _ = run_grover_search(n_qubits, marked_bitstrings, shots=shots, iterations=i)
        marked_total = sum(c for b, c in counts.items() if b in marked_bitstrings)
        prob = 100 * marked_total / shots
        results.append((i, prob))
    return results


def optimal_iterations(n_total_states, n_marked):
    if n_marked <= 0:
        return 0
    ratio = n_total_states / n_marked
    return max(1, math.floor((math.pi / 4) * math.sqrt(ratio)))


def run_grover_search(n_qubits, marked_bitstrings, shots=2048, iterations=None):
    """Builds and runs the full Grover circuit. Returns (counts, circuit, iterations_used)."""
    n_total = 2 ** n_qubits
    if iterations is None:
        iterations = optimal_iterations(n_total, len(marked_bitstrings))

    oracle = build_oracle(n_qubits, marked_bitstrings)
    diffuser = build_diffuser(n_qubits)

    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(range(n_qubits)) 
    for _ in range(iterations):
        qc.append(oracle.to_instruction(), range(n_qubits))
        qc.append(diffuser.to_instruction(), range(n_qubits))
    qc.measure(range(n_qubits), range(n_qubits))

    sim = AerSimulator()
    transpiled_qc = transpile(qc, sim)
    result = sim.run(transpiled_qc, shots=shots).result()
    counts = result.get_counts()
    return counts, qc, iterations
