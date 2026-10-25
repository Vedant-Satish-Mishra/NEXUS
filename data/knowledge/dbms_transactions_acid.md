topic: dbms

# Relational Transactions and ACID Guarantees

A database transaction represents a single logical unit of work that accesses and modifies data.

## The ACID Principles
1. **Atomicity:** All operations within a transaction succeed completely, or the database rolls back to its pre-transaction state ("All or Nothing"). Implemented via write-ahead logging (WAL) and undo logs.
2. **Consistency:** A transaction transforms the database from one valid state to another, preserving all declared schema constraints, cascades, and business rules.
3. **Isolation:** Concurrent transactions execute without interfering with one another.
4. **Durability:** Once a transaction commits, its modifications persist permanently across system failures and power outages via redo logs.

## Transaction Isolation Levels (SQL Standard)
- **Read Uncommitted:** Allows Dirty Reads (reading uncommitted changes from concurrent transactions).
- **Read Committed:** Prevents Dirty Reads; permits Non-Repeatable Reads.
- **Repeatable Read:** Prevents Non-Repeatable Reads; permits Phantom Reads (mitigated in PostgreSQL via MVCC).
- **Serializable:** Highest isolation level; prevents all concurrency anomalies through two-phase locking (2PL) or serializable snapshot isolation (SSI).
