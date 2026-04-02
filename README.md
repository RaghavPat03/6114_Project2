# 6114_Project2

Implementation of three fundamental graph algorithms in Python 3:

- **Dijkstra's Algorithm** — Single-source shortest path (directed & undirected)
- **Kruskal's Algorithm** — Minimum spanning tree (undirected only)
- **DFS** — Topological sorting & cycle detection (directed only)

---

## Requirements

- Python 3.8 or later
- No external libraries — uses only the standard library (`heapq`, `collections`, `sys`)

---

## How to Run

### Option 1: Run all five built-in demo graphs

This runs all five pre-built graphs (22+ nodes each) automatically:

```bash
python3 graph_algorithms.py
```

### Option 2: Load a graph from a text file

```bash
python3 graph_algorithms.py <filepath> [problems]
```

The optional `problems` argument is a string of digits selecting which algorithms to run:

| Digit | Algorithm |
|-------|-----------|
| `1`   | Dijkstra's shortest path |
| `2`   | Kruskal's MST (undirected graphs only) |
| `3`   | DFS topological sort / cycle detection (directed graphs only) |

**Examples:**

```bash
# Run all three algorithms on graph1.txt
python3 graph_algorithms.py graph1.txt

# Run only Dijkstra and Kruskal
python3 graph_algorithms.py graph1.txt 12

# Run only DFS on a directed graph
python3 graph_algorithms.py graph3.txt 3
```

---

## Input File Format

```
<V> <E> <U|D>
<u1> <v1> <w1>
<u2> <v2> <w2>
...
<source>
```

- **Line 1:** number of vertices, number of edges, and graph type (`U` = undirected, `D` = directed)
- **Lines 2–N:** each edge defined by two endpoints and a weight
- **Last line (optional):** source vertex for Dijkstra

**Example (`graph1.txt`):**

```
6 10 U
A B 1
A C 2
B C 1
B D 3
B E 2
C D 1
C E 2
D E 4
D F 3
E F 3
A
```

Vertex names can be strings (`A`, `B`, `S`) or integers (`1`, `2`, `3`).

---

## Expected Output

### Dijkstra (Problem 1)

Prints the shortest distance and path from the source to every other reachable vertex.

```
───────────────────────────────────────────────────────
  DIJKSTRA  |  Source: A
───────────────────────────────────────────────────────
  Destination      Distance   Path
  ───────────      ────────   ────
  B                     1.0   A → B
  C                     2.0   A → C
  D                     3.0   A → C → D
  E                     3.0   A → B → E
  F                     6.0   A → C → D → F
```

### Kruskal MST (Problem 2 — undirected graphs only)

Prints the edges included in the minimum spanning tree and the total cost.

```
  Edge         Weight
  A ─── B         1.0
  B ─── C         1.0
  C ─── D         1.0
  B ─── E         2.0
  D ─── F         3.0
  Total cost:     8.0
```

### DFS (Problem 3 — directed graphs only)

If the graph is **acyclic**, prints the topological ordering:

```
  Graph is ACYCLIC. Topological order:
  A → C → E → B → G → D → F
```

If the graph **contains cycles**, prints each cycle and its length:

```
  Graph contains 3 cycle(s):
  Cycle #   Length   Path
  1         3        A → B → C → A
  2         3        B → D → E → B
  3         3        C → F → G → C
```

---

## Notes

- Kruskal's MST is automatically skipped for directed graphs.
- DFS topological sort / cycle detection is automatically skipped for undirected graphs.
- If no source vertex is specified in the input file, Dijkstra is skipped with a notice.