topic: dsa

# Data Structures: Array and String Problem Patterns

Arrays and strings represent contiguous memory blocks that form the backbone of technical coding interviews.

## 1. Two-Pointer Technique
Used on sorted arrays to reduce $O(n^2)$ pairwise brute force to $O(n)$ linear scans.
- **Opposite Direction:** Left pointer starts at index 0, right at index $n-1$. Move inwards based on target comparison (e.g. Two Sum on sorted input, Container With Most Water).
- **Same Direction (Fast & Slow):** Trailing pointer tracks boundaries (e.g. removing duplicates in-place).

## 2. Sliding Window Pattern
Maintains a dynamic subarray window $[L, R]$ over a sequential stream.
- **Fixed Window:** Window size $K$ remains constant (e.g. Maximum sum subarray of length $k$).
- **Variable Window:** Expand $R$ to satisfy a constraint; shrink $L$ when invalid (e.g. Longest Substring Without Repeating Characters).

```python
# Sliding Window: Longest Substring Without Repeating Characters
def length_of_longest_substring(s: str) -> int:
    char_map = {}
    left = 0
    max_len = 0
    
    for right, ch in enumerate(s):
        if ch in char_map and char_map[ch] >= left:
            left = char_map[ch] + 1
        char_map[ch] = right
        max_len = max(max_len, right - left + 1)
        
    return max_len
```

Time complexity is $O(n)$ since each character is visited at most twice; space complexity is $O(\min(n, m))$ where $m$ is alphabet size.
