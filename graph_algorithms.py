"""
Graph Algorithms: Single-Source Shortest Path (Dijkstra), Minimum Spanning Tree (Kruskal),
                  and DFS Topological Sort / Cycle Detection.

Author: Project 2
Language: Python 3
"""

import heapq
import sys
from collections import defaultdict, deque


# ─────────────────────────────────────────────
# 1. GRAPH DATA STRUCTURE
# ─────────────────────────────────────────────
class Graph:
    """
    Adjacency-list weighted graph.

    Data structures chosen and their impact on runtime:
      • adjacency list  → O(V + E) space;  iterating neighbours is O(deg(v))
      • dict of lists   → O(1) average vertex lookup
      • edge list       → needed by Kruskal; stored alongside adjacency list

    Fields
    ------
    directed : bool
    vertices : set
    adj      : dict[node → list[(neighbour, weight)]]
    edges    : list[(weight, u, v)]   — for Kruskal
    """

    def __init__(self, directed: bool = False):
        self.directed = directed
        self.vertices: set = set()
        self.adj: dict = defaultdict(list)
        self.edges: list = []          # (weight, u, v)

    def add_edge(self, u, v, w: float):
        self.vertices.add(u)
        self.vertices.add(v)
        self.adj[u].append((v, w))
        if not self.directed:
            self.adj[v].append((u, w))
        self.edges.append((w, u, v))

    # ── I/O ──────────────────────────────────
    @staticmethod
    def from_file(path: str) -> tuple["Graph", str | None]:
        """
        Parse the project input format:
            <V> <E> <U|D>
            u v w
            ...
            [source]        ← optional last line (single token, not an edge)
        Returns (graph, source_or_None).
        """
        with open(path) as fh:
            lines = [l.strip() for l in fh if l.strip()]

        header = lines[0].split()
        directed = header[2].upper() == "D"
        g = Graph(directed=directed)

        # read edges
        source = None
        edge_lines = lines[1:]

        # detect optional source line: single token, no weight
        if edge_lines and len(edge_lines[-1].split()) == 1:
            source = edge_lines[-1].strip()
            edge_lines = edge_lines[:-1]

        for line in edge_lines:
            parts = line.split()
            u, v, w = parts[0], parts[1], float(parts[2])
            g.add_edge(u, v, w)

        return g, source

    def to_file(self, path: str, source: str | None = None):
        """Write graph back to the project file format."""
        v_count = len(self.vertices)
        e_count = len(self.edges)
        kind = "D" if self.directed else "U"
        with open(path, "w") as fh:
            fh.write(f"{v_count} {e_count} {kind}\n")
            for w, u, v in self.edges:
                fh.write(f"{u} {v} {int(w) if w == int(w) else w}\n")
            if source is not None:
                fh.write(f"{source}\n")


# ─────────────────────────────────────────────
# 2. DIJKSTRA – Single-Source Shortest Path
# ─────────────────────────────────────────────
"""
Algorithm Analysis
──────────────────
Dijkstra's algorithm finds the shortest path from a source to every other
vertex in a graph with non-negative edge weights.

Pseudocode
----------
DIJKSTRA(G, s):
    for each v in G.V:
        dist[v] ← ∞
        prev[v] ← None
    dist[s] ← 0
    Q ← min-heap containing (0, s)

    while Q is not empty:
        (d, u) ← EXTRACT-MIN(Q)
        if d > dist[u]:          // stale entry
            continue
        for each (v, w) in G.adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] ← dist[u] + w
                prev[v]  ← u
                INSERT(Q, (dist[v], v))

    return dist, prev

Data Structures & Runtime
--------------------------
• Min-heap (heapq)  → EXTRACT-MIN in O(log V)
• Adjacency list    → iterating neighbours in O(E) total across all extractions

Time complexity:  O((V + E) log V)
  - Each vertex is extracted at most once: O(V log V)
  - Each edge causes at most one INSERT: O(E log V)
  Total: O((V + E) log V)

Space complexity: O(V + E)
  - dist / prev arrays: O(V)
  - heap: O(V) entries at most at one time
  - adjacency list: O(V + E)
"""


def dijkstra(graph: Graph, source) -> tuple[dict, dict]:
    """
    Returns
    -------
    dist : dict[node → shortest distance from source]
    prev : dict[node → predecessor on shortest-path tree]
    """
    dist = {v: float("inf") for v in graph.vertices}
    prev = {v: None for v in graph.vertices}
    dist[source] = 0

    # min-heap of (distance, vertex)
    heap = [(0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:          # stale entry — skip
            continue
        for v, w in graph.adj[u]:
            relaxed = dist[u] + w
            if relaxed < dist[v]:
                dist[v] = relaxed
                prev[v] = u
                heapq.heappush(heap, (relaxed, v))

    return dist, prev


def reconstruct_path(prev: dict, source, target) -> list:
    """Walk the predecessor map backwards to recover the shortest path."""
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    if path and path[0] == source:
        return path
    return []          # no path exists


def print_shortest_paths(graph: Graph, source):
    """Pretty-print all shortest paths from *source*."""
    dist, prev = dijkstra(graph, source)
    print(f"\n{'─'*55}")
    print(f"  DIJKSTRA  |  Source: {source}")
    print(f"{'─'*55}")
    print(f"  {'Destination':<14} {'Distance':>10}   Path")
    print(f"  {'───────────':<14} {'────────':>10}   ────")
    for v in sorted(graph.vertices):
        if v == source:
            continue
        path = reconstruct_path(prev, source, v)
        path_str = " → ".join(path) if path else "unreachable"
        d_str = str(dist[v]) if dist[v] != float("inf") else "∞"
        print(f"  {v:<14} {d_str:>10}   {path_str}")
    print()


# ─────────────────────────────────────────────
# 3. KRUSKAL – Minimum Spanning Tree
# ─────────────────────────────────────────────
"""
Algorithm Analysis
──────────────────
Kruskal's algorithm greedily selects the minimum-weight edge that does
not create a cycle, using a Union-Find (Disjoint-Set Union) structure.

Pseudocode
----------
KRUSKAL(G):
    for each v in G.V:
        MAKE-SET(v)
    sort G.E by weight ascending       // O(E log E)
    mst ← []
    for each (u, v, w) in sorted G.E:
        if FIND(u) ≠ FIND(v):          // different components
            mst.append((u, v, w))
            UNION(u, v)
    return mst

Data Structures & Runtime
--------------------------
• Union-Find with path compression + union by rank
    - FIND  : O(α(V))  ≈ O(1) amortised (inverse Ackermann)
    - UNION : O(α(V))  ≈ O(1) amortised

Time complexity:  O(E log E)  dominated by sorting
  - Sorting edges:  O(E log E)
  - E × FIND/UNION: O(E α(V)) ≈ O(E)
  Total: O(E log E)  ≡  O(E log V)  (since E ≤ V²)

Space complexity: O(V + E)
  - Union-Find parent/rank arrays: O(V)
  - Sorted edge list: O(E)
  - MST result: O(V-1) edges
"""


class UnionFind:
    """
    Disjoint-Set Union with
      • path compression  (FIND flattens the tree)
      • union by rank     (smaller tree merged under larger)
    Both together guarantee O(α(n)) per operation.
    """

    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank   = {n: 0  for n in nodes}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])   # path compression
        return self.parent[x]

    def union(self, x, y) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False          # already in same set → would form a cycle
        # union by rank
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


def kruskal(graph: Graph) -> tuple[list, float]:
    """
    Returns
    -------
    mst_edges : list[(u, v, w)]
    total_cost : float
    """
    uf = UnionFind(graph.vertices)
    sorted_edges = sorted(graph.edges)    # sort by weight (first element of tuple)
    mst_edges = []
    total_cost = 0.0

    for w, u, v in sorted_edges:
        if uf.union(u, v):
            mst_edges.append((u, v, w))
            total_cost += w
            if len(mst_edges) == len(graph.vertices) - 1:
                break              # MST complete

    return mst_edges, total_cost


def print_mst(graph: Graph):
    """Pretty-print the MST edges and total cost."""
    mst_edges, total_cost = kruskal(graph)
    print(f"\n{'─'*55}")
    print(f"  KRUSKAL MST")
    print(f"{'─'*55}")
    if not mst_edges:
        print("  Graph is not connected — no spanning tree.")
        return
    print(f"  {'Edge':<20} {'Weight':>8}")
    print(f"  {'────':<20} {'──────':>8}")
    for u, v, w in mst_edges:
        print(f"  {u} ─── {v:<15} {w:>8.1f}")
    print(f"  {'':20} {'────────':>8}")
    print(f"  {'Total cost':<20} {total_cost:>8.1f}")
    print()


# ─────────────────────────────────────────────
# 4. DFS – Topological Sort & Cycle Detection
# ─────────────────────────────────────────────
"""
Algorithm Analysis
──────────────────
Depth-First Search drives both topological sorting and cycle detection.

Pseudocode (DFS with colouring)
--------------------------------
Colour each vertex:  WHITE (unvisited) | GRAY (in progress) | BLACK (done)

DFS(G):
    for each v in G.V:
        colour[v] ← WHITE
    finish_stack ← []
    cycles ← []

    for each v in G.V:
        if colour[v] == WHITE:
            DFS-VISIT(G, v, [], finish_stack, cycles)

    topological_order ← reverse(finish_stack)   // valid only if no cycles

DFS-VISIT(G, u, path, finish_stack, cycles):
    colour[u] ← GRAY
    path.append(u)
    for each (v, _) in G.adj[u]:
        if colour[v] == GRAY:                    // back edge → cycle!
            cycle_start = path.index(v)
            cycles.append(path[cycle_start:] + [v])
        elif colour[v] == WHITE:
            DFS-VISIT(G, v, path, finish_stack, cycles)
    colour[u] ← BLACK
    path.pop()
    finish_stack.append(u)

Data Structures & Runtime
--------------------------
• colour dict      : O(1) lookup
• recursion stack  : O(V) depth in worst case
• finish_stack     : list, O(1) append
• cycle paths      : list of lists, accumulated during search

Time complexity:  O(V + E)
  - Every vertex is coloured exactly once (WHITE→GRAY→BLACK)
  - Every edge is examined exactly once from its source vertex
  Total: O(V + E)

Space complexity: O(V + E)
  - Colour / finish arrays: O(V)
  - Recursion depth: O(V)
  - Adjacency list: O(V + E)
"""

WHITE, GRAY, BLACK = 0, 1, 2


def dfs_visit(graph: Graph, u, colour: dict, path: list,
              finish_stack: list, cycles: list, cycle_set: set):
    colour[u] = GRAY
    path.append(u)

    for v, _ in graph.adj[u]:
        if colour[v] == GRAY:
            # Back edge → cycle found; extract the cycle from path
            idx = path.index(v)
            cycle = path[idx:] + [v]
            key = tuple(sorted(cycle[:-1]))     # canonical form for dedup
            if key not in cycle_set:
                cycle_set.add(key)
                cycles.append(cycle)
        elif colour[v] == WHITE:
            dfs_visit(graph, v, colour, path, finish_stack, cycles, cycle_set)

    colour[u] = BLACK
    path.pop()
    finish_stack.append(u)


def dfs_full(graph: Graph) -> tuple[list, list]:
    """
    Run DFS over the whole graph.

    Returns
    -------
    topo_order : list — valid topological order (empty if cycles exist)
    cycles     : list of lists — each inner list is one cycle [a,b,c,a]
    """
    colour = {v: WHITE for v in graph.vertices}
    finish_stack = []
    cycles = []
    cycle_set = set()

    # Use a deterministic vertex order for reproducibility
    for v in sorted(graph.vertices):
        if colour[v] == WHITE:
            dfs_visit(graph, v, colour, [], finish_stack, cycles, cycle_set)

    topo_order = list(reversed(finish_stack)) if not cycles else []
    return topo_order, cycles


def print_dfs_results(graph: Graph):
    """Pretty-print topological order or all cycles."""
    if not graph.directed:
        print("  DFS topological sort / cycle detection requires a directed graph.")
        return

    topo_order, cycles = dfs_full(graph)

    print(f"\n{'─'*55}")
    print(f"  DFS: Topological Sort / Cycle Detection")
    print(f"{'─'*55}")

    if not cycles:
        print("  Graph is ACYCLIC.")
        print("  Topological order:")
        print("    " + " → ".join(topo_order))
    else:
        print(f"  Graph contains {len(cycles)} cycle(s):\n")
        for i, cycle in enumerate(cycles, 1):
            length = len(cycle) - 1           # number of edges in the cycle
            path_str = " → ".join(cycle)
            print(f"  Cycle {i}  (length {length}):  {path_str}")
    print()


# ─────────────────────────────────────────────
# 5. DEMO: five test graphs
# ─────────────────────────────────────────────

def build_graph1_undirected() -> tuple[Graph, str]:
    """
    Undirected weighted graph — city metro network.
    22 nodes, 45 edges.  Source: A
    """
    g = Graph(directed=False)
    edges = [
        ("A","B",4),  ("A","C",2),  ("A","D",7),  ("B","C",1),
        ("B","E",5),  ("B","F",3),  ("C","D",3),  ("C","G",6),
        ("D","H",2),  ("D","I",4),  ("E","F",2),  ("E","J",8),
        ("F","G",1),  ("F","K",4),  ("G","H",3),  ("G","L",5),
        ("H","I",2),  ("H","M",6),  ("I","N",3),  ("J","K",2),
        ("J","O",7),  ("K","L",3),  ("K","P",5),  ("L","M",4),
        ("L","Q",6),  ("M","N",1),  ("M","R",4),  ("N","S",5),
        ("O","P",3),  ("O","T",6),  ("P","Q",2),  ("P","U",4),
        ("Q","R",3),  ("Q","V",5),  ("R","S",2),  ("S","T",7),
        ("T","U",3),  ("U","V",4),  ("A","J",9),  ("B","K",6),
        ("C","L",8),  ("D","M",5),  ("E","N",4),  ("F","O",7),
        ("G","P",3),
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, "A"


def build_graph2_undirected() -> tuple[Graph, str]:
    """
    Undirected weighted graph — logistics hub network.
    22 nodes, 46 edges.  Source: 1
    """
    g = Graph(directed=False)
    edges = [
        ("1","2",4),   ("1","3",8),   ("1","4",6),   ("2","3",2),
        ("2","5",7),   ("2","6",5),   ("3","4",3),   ("3","7",9),
        ("4","8",4),   ("4","9",2),   ("5","6",1),   ("5","10",6),
        ("6","7",3),   ("6","11",5),  ("7","8",2),   ("7","12",4),
        ("8","9",3),   ("8","13",7),  ("9","14",5),  ("10","11",2),
        ("10","15",8), ("11","12",4), ("11","16",3), ("12","13",1),
        ("12","17",6), ("13","14",3), ("13","18",4), ("14","19",5),
        ("15","16",3), ("15","20",6), ("16","17",2), ("16","21",4),
        ("17","18",3), ("17","22",5), ("18","19",2), ("19","20",7),
        ("20","21",3), ("21","22",4), ("1","10",11), ("2","11",9),
        ("3","12",7),  ("4","13",8),  ("5","14",6),  ("6","15",10),
        ("7","16",5),  ("8","17",4),
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, "1"


def build_graph3_directed_acyclic() -> tuple[Graph, str]:
    """
    Directed Acyclic Graph — software build pipeline.
    20 nodes, 40 edges.  Source: A
    All edges point from earlier stages to later stages (no cycles).
    """
    g = Graph(directed=True)
    edges = [
        # Layer 0 → Layer 1
        ("A","B",1), ("A","C",2), ("A","D",3),
        # Layer 1 → Layer 2
        ("B","E",1), ("B","F",2), ("C","E",3), ("C","G",1),
        ("D","F",2), ("D","H",4),
        # Layer 2 → Layer 3
        ("E","I",2), ("E","J",1), ("F","J",3), ("F","K",2),
        ("G","K",1), ("G","L",3), ("H","L",2), ("H","M",1),
        # Layer 3 → Layer 4
        ("I","N",2), ("J","N",3), ("J","O",1), ("K","O",2),
        ("K","P",3), ("L","P",1), ("L","Q",4), ("M","Q",2),
        # Layer 4 → Layer 5
        ("N","R",1), ("O","R",2), ("O","S",3), ("P","S",1),
        ("P","T",2), ("Q","T",3),
        # Cross-layer shortcuts
        ("A","E",5), ("A","F",4), ("B","I",3), ("C","J",2),
        ("D","K",4), ("E","N",6), ("F","O",5), ("G","P",3),
        ("H","Q",2), ("I","R",4),
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, "A"


def build_graph4_directed_cyclic() -> tuple[Graph, str]:
    """
    Directed graph with multiple cycles — dependency network.
    20 nodes, 41 edges.  Source: A
    Contains several distinct cycles of varying lengths.
    """
    g = Graph(directed=True)
    edges = [
        # Cycle 1: A→B→C→A  (length 3)
        ("A","B",2),  ("B","C",3),  ("C","A",1),
        # Cycle 2: B→D→E→F→B  (length 4)
        ("B","D",4),  ("D","E",2),  ("E","F",3),  ("F","B",1),
        # Cycle 3: C→G→H→C  (length 3)
        ("C","G",5),  ("G","H",2),  ("H","C",3),
        # Cycle 4: D→I→J→K→D  (length 4)
        ("D","I",3),  ("I","J",2),  ("J","K",4),  ("K","D",1),
        # Cycle 5: G→L→M→G  (length 3)
        ("G","L",4),  ("L","M",3),  ("M","G",2),
        # Cycle 6: E→N→O→E  (length 3)
        ("E","N",2),  ("N","O",5),  ("O","E",1),
        # Cycle 7: H→P→Q→H  (length 3)
        ("H","P",3),  ("P","Q",2),  ("Q","H",4),
        # Interconnects
        ("A","I",6),  ("B","L",5),  ("C","N",3),
        ("F","P",4),  ("K","M",2),  ("J","O",3),
        ("L","N",5),  ("M","P",4),  ("I","G",3),
        ("N","K",2),  ("O","Q",1),  ("P","D",5),
        # Entry from A to other regions
        ("A","R",3),  ("R","S",2),  ("S","T",4),  ("T","R",1),  # Cycle 8: R→S→T→R
        ("A","N",7),  # extra cross-region edge
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, "A"


def build_graph5_undirected_large() -> tuple[Graph, str]:
    """
    Undirected weighted graph — regional road network.
    22 nodes, 47 edges.  Source: S
    """
    g = Graph(directed=False)
    edges = [
        ("S","A",7),  ("S","B",2),  ("S","C",3),  ("S","D",5),
        ("A","B",3),  ("A","E",4),  ("A","F",6),
        ("B","C",1),  ("B","G",4),  ("B","H",2),
        ("C","D",2),  ("C","I",5),  ("C","J",3),
        ("D","K",4),  ("D","L",6),
        ("E","F",2),  ("E","M",5),  ("E","G",3),
        ("F","N",4),  ("F","M",3),
        ("G","H",1),  ("G","O",6),
        ("H","I",3),  ("H","P",4),
        ("I","J",2),  ("I","Q",5),
        ("J","K",3),  ("J","R",4),
        ("K","L",1),  ("K","S2",5),
        ("L","T",6),  ("L","U",3),
        ("M","N",2),  ("M","O",4),
        ("N","P",3),  ("N","V",5),
        ("O","P",2),  ("O","Q",4),
        ("P","Q",1),  ("P","R",5),
        ("Q","R",3),  ("Q","S2",4),
        ("R","T",2),  ("S2","U",3),
        ("T","U",4),  ("U","V",2),
        ("V","S",8),
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, "S"


# ─────────────────────────────────────────────
# 6. FILE I/O HELPERS
# ─────────────────────────────────────────────

def save_graph_to_file(graph: Graph, path: str, source: str | None = None):
    graph.to_file(path, source)
    print(f"  [saved] {path}")


def run_from_file(path: str, problems: str = "123"):
    """
    Load a graph from *path* and run the requested problems.
    problems: string of digits '1','2','3' (default: all)
    """
    print(f"\n{'═'*55}")
    print(f"  Loading graph from: {path}")
    print(f"{'═'*55}")
    graph, source = Graph.from_file(path)
    print(f"  Vertices : {len(graph.vertices)}")
    print(f"  Edges    : {len(graph.edges)}")
    print(f"  Directed : {graph.directed}")
    print(f"  Source   : {source}")

    if "1" in problems:
        if source:
            print_shortest_paths(graph, source)
        else:
            print("  [!] No source specified — skipping Dijkstra.")

    if "2" in problems:
        if not graph.directed:
            print_mst(graph)
        else:
            print("  [!] Kruskal requires an undirected graph — skipping MST.")

    if "3" in problems:
        print_dfs_results(graph)


# ─────────────────────────────────────────────
# 7. MAIN – run all five test cases
# ─────────────────────────────────────────────

def run_all_demos():
    separator = "\n" + "═"*55

    # ── Graph 1: City metro network ──────────
    print(separator)
    print("  GRAPH 1  |  City metro network (undirected, 22 nodes, 45 edges)")
    print("═"*55)
    g1, s1 = build_graph1_undirected()
    save_graph_to_file(g1, "graph1.txt", s1)
    print_shortest_paths(g1, s1)
    print_mst(g1)

    # ── Graph 2: Logistics hub network ───────
    print(separator)
    print("  GRAPH 2  |  Logistics hub network (undirected, 22 nodes, 46 edges)")
    print("═"*55)
    g2, s2 = build_graph2_undirected()
    save_graph_to_file(g2, "graph2.txt", s2)
    print_shortest_paths(g2, s2)
    print_mst(g2)

    # ── Graph 3: DAG — build pipeline ────────
    print(separator)
    print("  GRAPH 3  |  Build pipeline DAG (directed, 20 nodes, 40 edges)")
    print("═"*55)
    g3, s3 = build_graph3_directed_acyclic()
    save_graph_to_file(g3, "graph3.txt", s3)
    print_shortest_paths(g3, s3)
    print_dfs_results(g3)

    # ── Graph 4: Cyclic dependency network ───
    print(separator)
    print("  GRAPH 4  |  Cyclic dependency network (directed, 20 nodes, 41 edges)")
    print("═"*55)
    g4, s4 = build_graph4_directed_cyclic()
    save_graph_to_file(g4, "graph4.txt", s4)
    print_shortest_paths(g4, s4)
    print_dfs_results(g4)

    # ── Graph 5: Regional road network ───────
    print(separator)
    print("  GRAPH 5  |  Regional road network (undirected, 22 nodes, 47 edges)")
    print("═"*55)
    g5, s5 = build_graph5_undirected_large()
    save_graph_to_file(g5, "graph5.txt", s5)
    print_shortest_paths(g5, s5)
    print_mst(g5)

    print(separator)
    print("  All five test cases complete.")
    print("═"*55 + "\n")


if __name__ == "__main__":
    # If a file path is given on the command line, load it directly.
    # Usage:  python graph_algorithms.py <file> [problems]
    #   e.g.  python graph_algorithms.py graph1.txt 12
    if len(sys.argv) >= 2:
        probs = sys.argv[2] if len(sys.argv) >= 3 else "123"
        run_from_file(sys.argv[1], probs)
    else:
        run_all_demos()