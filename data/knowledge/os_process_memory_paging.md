topic: os_networking

# Operating Systems: Virtual Memory, Paging, and Page Faults

Virtual memory decouples the programmer's address space from physical RAM, providing hardware isolation between processes and enabling systems to execute programs larger than physical memory.

## Paging Mechanics
1. **Virtual Address Space:** Partitioned into fixed-size contiguous blocks called **pages** (commonly 4 KB).
2. **Physical Address Space:** Structured into physical hardware slots called **page frames**.
3. **Page Table:** An OS data structure mapping virtual page numbers (VPN) to physical frame numbers (PFN), along with protection bits (read, write, execute) and valid/present bits.
4. **Translation Lookaside Buffer (TLB):** A high-speed hardware cache inside the Memory Management Unit (MMU) that stores recent page translations to avoid multi-level memory bus penalties.

## Handling Page Faults
When a process references a virtual address whose valid bit in the page table is zero, the MMU raises a hardware interrupt known as a **Page Fault**:
- The OS trap handler traps into kernel mode and verifies whether the access was legal.
- An empty physical frame is located. If RAM is full, a page replacement algorithm (e.g. LRU or Clock) evicts a victim page to swap disk.
- The requested page is read from secondary storage via DMA into the physical frame.
- The page table and TLB are updated, and the interrupted CPU instruction restarts seamlessly.
