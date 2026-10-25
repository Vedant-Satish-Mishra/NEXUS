topic: java_core

# Java Virtual Machine (JVM) Architecture & Memory Management

The Java Virtual Machine (JVM) provides an execution environment for compiled Java bytecode, enabling the "Write Once, Run Anywhere" philosophy.

## JVM Runtime Data Areas
The memory managed by the JVM is structured into distinct functional regions:
1. **Classloader Subsystem:** Responsible for loading, linking, and initializing `.class` files into memory.
2. **Method Area:** Stores class-level structures, runtime constant pools, field/method metadata, and static variables.
3. **Heap Space:** The runtime data area where all class instances and arrays are allocated. Divided into:
   - *Young Generation:* Comprising Eden space and Survivor spaces (S0, S1). Minor Garbage Collection occurs here.
   - *Old (Tenured) Generation:* Stores long-lived objects that survived multiple Minor GC cycles.
4. **JVM Stacks:** Each thread possesses a private stack that holds frames containing local variables, operand stacks, and partial results.
5. **Program Counter (PC) Register:** Stores the address of the currently executing JVM instruction per thread.
6. **Native Method Stack:** Supports execution of native C/C++ code via JNI.

## Garbage Collection Mechanisms
Automated memory recovery prevents leaks:
- **Mark-and-Sweep:** Objects reachable from GC roots (thread stacks, static references) are marked; unreferenced memory is swept.
- **Generational Collection:** Because most objects die young (Weak Generational Hypothesis), young generation collections run rapidly using parallel copying collectors (e.g. G1GC, ZGC).

```java
// Example demonstrating heap allocation vs stack reference
public class MemoryExample {
    private static final String APP_NAME = "NEXUS"; // Method area

    public static void main(String[] args) {
        int localCount = 10; // Stored in thread stack frame
        StringBuilder sb = new StringBuilder("Heap Allocated"); // Reference in stack, object in Heap
        System.out.println(sb.append(" - ").append(localCount));
    }
}
```
