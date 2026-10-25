topic: dbms

# Database Normalization and Normal Forms

Database normalization is the systematic technique of organizing relational database schemas to minimize insertion, update, and deletion anomalies while eliminating data redundancy.

## Normal Forms Comparison Table

| Normal Form | Primary Rule Requirement | Eliminates | Example Violation Resolved |
|---|---|---|---|
| **1NF** (First Normal Form) | All column attributes must hold atomic (indivisible) values; each record is unique. | Multi-valued attributes, nested repeating groups | Comma-separated phone numbers stored in a single column |
| **2NF** (Second Normal Form) | Table is in 1NF, and every non-prime attribute is fully functionally dependent on the entire primary key. | Partial dependencies on composite keys | Course teacher name depending only on `CourseID` in a `(StudentID, CourseID)` table |
| **3NF** (Third Normal Form) | Table is in 2NF, and no non-prime attribute depends transitively on the primary key ($X \to Y \to Z$). | Transitive dependencies | `City` and `State` depending on `ZipCode` which depends on `CustomerID` |
| **BCNF** (Boyce-Codd) | For every non-trivial functional dependency $X \to Y$, $X$ must be a super key. | Anomalies where a prime attribute depends on a non-super key | Overlapping candidate keys where determinant is not a super key |

## Normalization Trade-Offs
While higher normal forms prevent data inconsistencies, excessive normalization introduces query latency due to complex multi-table SQL joins (`JOIN`). In read-heavy OLAP workloads, denormalization is often deliberately applied for performance.
