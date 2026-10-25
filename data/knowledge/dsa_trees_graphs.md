topic: dsa

# Tree Traversals and Graph Search Algorithms

Non-linear data structures model hierarchical relationships and complex networks.

## 1. Binary Tree Traversals
- **Depth-First Search (DFS):**
  - *In-Order (Left, Root, Right):* Yields values in sorted order for Binary Search Trees (BST).
  - *Pre-Order (Root, Left, Right):* Used for tree cloning and serialization.
  - *Post-Order (Left, Right, Root):* Used for bottom-up computation (e.g. tree height, directory size).
- **Breadth-First Search (BFS):** Level-order traversal using a queue to find shortest path on unweighted graphs.

## 2. Graph Algorithms
- **Dijkstra's Algorithm:** Computes single-source shortest path on graphs with non-negative edge weights using a min-heap priority queue ($O((V + E) \log V)$).
- **Topological Sorting (Kahn's Algorithm):** Linear ordering of vertices in a Directed Acyclic Graph (DAG) such that for every directed edge $u \to v$, $u$ comes before $v$.

```python
# Kahn's Algorithm for Topological Sort
from collections import deque

def topological_sort(num_nodes: int, edges: list[tuple[int, int]]) -> list[int]:
    adj = {i: [] for i in range(num_nodes)}
    in_degree = [0] * num_nodes
    
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
        
    queue = deque([i for i in range(num_nodes) if in_degree[i] == 0])
    order = []
    
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    if len(order) != num_nodes:
        raise ValueError("Graph contains a cycle")
    return order
```
