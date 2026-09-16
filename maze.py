maze.py
Defines a small grid maze and a classical BFS solver.

The maze is a square grid of size N x N (N is a power of 2, so each
cell's (row, col) position can be encoded exactly in qubits: n qubits
for rows + n qubits for cols, where N = 2^n).

Walls are edges between adjacent cells that cannot be crossed.
The classical BFS is used only to compute which cells lie on a valid
shortest path from START to EXIT -- this becomes the "marked states"
that the quantum oracle amplifies with Grover's algorithm.


import random
from collections import deque


class Maze:
    def __init__(self, size, walls, start, exit_):
        """
        size   : int, grid is size x size (size must be a power of 2)
        walls  : set of frozenset({(r1,c1), (r2,c2)}) -- blocked edges
        start  : (row, col) tuple
        exit_  : (row, col) tuple
        """
        self.size = size
        self.walls = walls
        self.start = start
        self.exit = exit_
        self.n_bits_per_axis = (size - 1).bit_length() 

    def in_bounds(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def is_wall(self, a, b):
        return frozenset((a, b)) in self.walls

    def neighbors(self, cell):
        r, c = cell
        candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        for nxt in candidates:
            if self.in_bounds(*nxt) and not self.is_wall(cell, nxt):
                yield nxt

    def bfs_shortest_path(self):
        """Classical baseline: returns the list of cells on the shortest
        path from start to exit (inclusive), or None if unreachable."""
        q = deque([self.start])
        came_from = {self.start: None}
        while q:
            cur = q.popleft()
            if cur == self.exit:
                path = []
                node = cur
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                return list(reversed(path))
            for nxt in self.neighbors(cur):
                if nxt not in came_from:
                    came_from[nxt] = cur
                    q.append(nxt)
        return None

    def cell_to_index(self, cell):
        """Flatten (row, col) -> single integer index 0..size*size-1"""
        r, c = cell
        return r * self.size + c

    def index_to_cell(self, idx):
        return divmod(idx, self.size)

    def cell_to_bitstring(self, cell):
        """Encode (row, col) as a bitstring: row bits followed by col bits."""
        r, c = cell
        nb = self.n_bits_per_axis
        return format(r, f"0{nb}b") + format(c, f"0{nb}b")

    def total_qubits(self):
        return 2 * self.n_bits_per_axis

    def render(self, path=None):
        """Return an ASCII rendering of the maze, optionally highlighting a path."""
        path_set = set(path) if path else set()
        lines = []
       
        lines.append("+" + "---+" * self.size)
        for r in range(self.size):
            row_line = "|"
            wall_line = "+"
            for c in range(self.size):
                cell = (r, c)
                if cell == self.start:
                    ch = " S "
                elif cell == self.exit:
                    ch = " E "
                elif cell in path_set:
                    ch = " * "
                else:
                    ch = "   "
                row_line += ch
              
                right = (r, c + 1)
                if self.in_bounds(*right) and not self.is_wall(cell, right):
                    row_line += " "
                else:
                    row_line += "|"
               
                below = (r + 1, c)
                if self.in_bounds(*below) and not self.is_wall(cell, below):
                    wall_line += "   +"
                else:
                    wall_line += "---+"
            lines.append(row_line)
            lines.append(wall_line)
        return "\n".join(lines)


def generate_maze(size=8, seed=42, start=(0, 0), exit_=None):
    """
    Generates a maze on a size x size grid using randomized depth-first
    search (the "recursive backtracker" algorithm). This carves a
    spanning tree over the grid cells, guaranteeing exactly one unique
    path between any two cells -- a classic, well-formed maze.

    size must be a power of 2 so each axis encodes cleanly into qubits.
    """
    assert (size & (size - 1)) == 0, "size must be a power of 2"
    if exit_ is None:
        exit_ = (size - 1, size - 1)

    rng = random.Random(seed)
    visited = {start}
    open_edges = set()  
    stack = [start]

    def unvisited_neighbors(cell):
        r, c = cell
        candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        result = [n for n in candidates if 0 <= n[0] < size and 0 <= n[1] < size and n not in visited]
        rng.shuffle(result)
        return result

    while stack:
        current = stack[-1]
        neighbors = unvisited_neighbors(current)
        if neighbors:
            nxt = neighbors[0]
            open_edges.add(frozenset((current, nxt)))
            visited.add(nxt)
            stack.append(nxt)
        else:
            stack.pop()

  
    all_edges = set()
    for r in range(size):
        for c in range(size):
            if c + 1 < size:
                all_edges.add(frozenset(((r, c), (r, c + 1))))
            if r + 1 < size:
                all_edges.add(frozenset(((r, c), (r + 1, c))))
    walls = all_edges - open_edges

    return Maze(size=size, walls=walls, start=start, exit_=exit_)


def make_default_maze():
    """
    A 4x4 maze (needs 2 qubits per axis -> 4 qubits total -> 16 basis states).
    Grid:
        (0,0) (0,1) (0,2) (0,3)
        (1,0) (1,1) (1,2) (1,3)
        (2,0) (2,1) (2,2) (2,3)
        (3,0) (3,1) (3,2) (3,3)

    Walls block certain edges to force a specific non-trivial path.
    Start = (0,0), Exit = (3,3)
    """
    size = 4
    blocked_edges = [
        ((0, 1), (0, 2)),
        ((0, 1), (1, 1)),
        ((1, 0), (1, 1)),
        ((1, 1), (2, 1)),
        ((2, 1), (2, 2)),
        ((1, 2), (1, 3)),
        ((2, 2), (3, 2)),
        ((1, 2), (2, 2)),
        ((2, 3), (3, 3)),
    ]
    walls = {frozenset(e) for e in blocked_edges}
    return Maze(size=size, walls=walls, start=(0, 0), exit_=(3, 3))
