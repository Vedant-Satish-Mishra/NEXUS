topic: knowledge_conventions

# NEXUS Preloaded Knowledge Base Conventions

This directory contains pre-curated, high-quality technical notes that are preloaded into ChromaDB (`kb_system` collection, `scope="system"`) for grounding student questions in placements and engineering fundamentals.

## 1. File Conventions
- **Header:** The very first line of each file MUST be formatted as: `topic: <topic_name>`.
- **Word Count:** 300 to 600 words per file to optimize for 250–350 word chunk windows.
- **Headings:** Use clear Markdown `#` and `##` headings. Chunks preserve the heading breadcrumb prefix.
- **Code:** Code blocks must be fenced (e.g. ````java ... ````) and syntax-valid. Never split mid-block.
- **Licensing & Originality:** All summaries must be written in your own words. Do not copy copyrighted text.

## 2. Topic Directory & Scope
1. **Java Core:** JVM architecture, Garbage Collection, OOP, Java 8 Streams, Concurrency.
2. **DSA:** Arrays, Strings, Trees, Graphs, Dynamic Programming patterns.
3. **DBMS & SQL:** Normalization, ACID transactions, B-Tree vs Hash indexes, Query execution.
4. **Python:** AsyncIO, memory management, GIL, decorators, generator pipelines.
5. **Operating Systems & Networking:** Paging, virtual memory, TCP vs UDP, HTTP/2 vs HTTP/3.
6. **Software Engineering & System Design:** SOLID principles, CAP theorem, caching, message queues.
7. **Interview Preparation:** Technical problem-solving strategy, behavioral STAR methodology.
