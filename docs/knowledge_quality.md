# NEXUS Knowledge Quality Standards & Checklist

This document defines the strict quality guidelines for all curated technical documentation included in the NEXUS system knowledge base (`data/knowledge/`).

---

## 1. Quality Checklist

Every knowledge file must satisfy all of the following rules:

1. **Front-Matter Metadata**:
   - Must begin with YAML front-matter containing `topic`, `title`, and `tags`.
   - Topics must be canonical: `Java`, `DSA`, `DBMS`, `Python`, `Operating Systems`, `Software Engineering`, or `System Design`.

2. **Word Count Budget**:
   - Each markdown document must be between **300 and 650 words**.
   - Ensures tight semantic cohesion and avoids chunk dilution.

3. **No Unresolved Markers**:
   - Zero occurrences of `TODO`, `TODO-VERIFY`, `FIXME`, or placeholder text (`Lorem Ipsum`).
   - All code snippets and algorithmic complexity claims must be verified.

4. **Structured Heading Hierarchy**:
   - Must feature a single `# Level 1 Title`.
   - Must contain at least two `## Level 2 Section` headings.
   - Subheadings `### Level 3` are optional but must be nested properly.

5. **Fenced Code Blocks**:
   - All code examples must use markdown fenced blocks with explicit language tags (e.g., ````python```, ````java```, ````sql```).
   - Code blocks must contain runnable, syntactically valid code (no empty blocks).

6. **Original & Accurate Content**:
   - Content must be original, concisely written in reference style.
   - No duplicate paragraphs across different markdown files.

---

## 2. Automated Validation

Run the validator script before committing or indexing any new knowledge files:

```bash
python scripts/validate_knowledge.py
```
