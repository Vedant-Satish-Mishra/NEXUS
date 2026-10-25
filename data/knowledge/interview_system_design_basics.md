topic: interview_prep

# System Design Fundamentals: Scaling, Caching, and CAP Theorem

Modern software engineering interviews evaluate the ability to design resilient, distributed systems under real-world scale.

## 1. Vertical vs Horizontal Scaling
- **Vertical Scaling (Scale-Up):** Adding more CPU, RAM, or storage to a single server. Limited by hardware caps and introduces a Single Point of Failure (SPOF).
- **Horizontal Scaling (Scale-Out):** Adding more commodity machines connected behind a load balancer (e.g. Nginx, AWS ALB). Provides elasticity and high fault tolerance.

## 2. Distributed Caching Strategies
Caching stores expensive query results or computed data in fast memory (e.g. Redis, Memcached):
- **Cache-Aside (Lazy Loading):** Application queries the cache; on miss, reads from database, updates cache, and returns.
- **Write-Through:** Application writes to cache, which synchronously writes to database before returning.
- **Write-Back (Write-Behind):** Application writes to cache immediately; cache asynchronously writes batches to the database.

## 3. The CAP Theorem
In an asynchronous distributed data store with network partitioning ($P$), the system can guarantee at most one of:
- **Consistency ($C$):** Every read receives the most recent write or an error.
- **Availability ($A$):** Every request receives a non-error response without guarantee of recent write data.
Systems must choose either **CP** (e.g. HBase, MongoDB) or **AP** (e.g. Cassandra, DynamoDB) during network partitions.
