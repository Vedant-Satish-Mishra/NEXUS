topic: dsa

# Dynamic Programming: Memoization and Tabulation Patterns

Dynamic Programming (DP) solves complex problems by breaking them down into overlapping subproblems with optimal substructure.

## Core Approaches
1. **Top-Down with Memoization:** Recursive function that caches intermediate results in a hash table or array, eliminating redundant recursive calls.
2. **Bottom-Up with Tabulation:** Iterative approach that fills a DP table starting from the smallest base cases, avoiding call stack overhead.

## Canonical Pattern: 0/1 Knapsack
Given items with weights $w_i$ and values $v_i$, maximize total value within weight capacity $W$.

```python
# 0/1 Knapsack Tabulation (Space Optimized to 1D array)
def knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    dp = [0] * (capacity + 1)
    
    for w, v in zip(weights, values):
        # Traverse backwards to prevent using the same item multiple times
        for j in range(capacity, w - 1, -1):
            dp[j] = max(dp[j], dp[j - w] + v)
            
    return dp[capacity]
```

## Key State Transition Formulas
- **Longest Common Subsequence (LCS):**
  $$DP[i][j] = DP[i-1][j-1] + 1 \quad \text{if } s_1[i-1] == s_2[j-1]$$
  $$DP[i][j] = \max(DP[i-1][j], DP[i][j-1]) \quad \text{otherwise}$$
- **Coin Change (Minimum coins):**
  $$DP[i] = \min(DP[i], DP[i - c] + 1) \quad \forall c \le i$$
