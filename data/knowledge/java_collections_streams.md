topic: java_core

# Java Collections Framework and Streams API

The Collections Framework provides unified architectures for representing and manipulating collections of objects in Java.

## Core Hierarchy
- **List Interface:** Ordered collections allowing duplicate elements.
  - `ArrayList`: Resizable array. Offers $O(1)$ amortized insertion and $O(1)$ random access by index.
  - `LinkedList`: Doubly-linked list. Provides $O(1)$ node insertion/deletion once the pointer is reached.
- **Set Interface:** Collection containing no duplicate elements.
  - `HashSet`: Backed by a `HashMap`. Provides average $O(1)$ lookups.
  - `TreeSet`: Implemented via Red-Black Tree. Guarantees $O(\log n)$ ordered operations.
- **Map Interface:** Key-value mappings without duplicate keys.
  - `HashMap`: Array of buckets (linked lists transitioning to balanced trees at threshold 8).

## Declarative Processing with Streams
Introduced in Java 8, streams enable functional pipelines:
```java
import java.util.*;
import java.util.stream.Collectors;

public class StreamDemo {
    public static void main(String[] args) {
        List<String> candidates = List.of("Arjun", "Rohan", "Priya", "Ananya", "Rahul");

        // Filter names starting with 'A', map to uppercase, and collect to list
        List<String> filtered = candidates.stream()
            .filter(name -> name.startsWith("A"))
            .map(String::toUpperCase)
            .sorted()
            .collect(Collectors.toList());

        System.out.println(filtered); // [ANANYA, ARJUN]
    }
}
```
Intermediate operations (like `filter`, `map`) are evaluated lazily until a terminal operation (like `collect`, `forEach`) executes.
