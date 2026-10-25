"""
NEXUS GraphStore Interface and Optional Neo4j Relationship Memory (Step 5.B.3)
Maintains concept relationship graphs behind an abstract interface.
When Neo4j is disabled (default), NullGraphStore operates as a clean no-op.
"""
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import re
import logging

logger = logging.getLogger("nexus.graph_store")


@runtime_checkable
class GraphStore(Protocol):
    def is_available(self) -> bool:
        ...

    async def upsert_concept(
        self, user_id: str, concept: str, source_type: str, source_id: str
    ) -> None:
        ...

    async def link_concepts(
        self, user_id: str, concept_a: str, concept_b: str, relation: str
    ) -> None:
        ...

    async def get_related_concepts(
        self, user_id: str, concepts: List[str], limit: int = 5
    ) -> List[str]:
        ...

    async def get_user_graph(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        ...

    async def delete_by_source(self, user_id: str, source_id: str) -> None:
        ...

    async def delete_user_graph(self, user_id: str) -> None:
        ...


class NullGraphStore:
    """Safe no-op graph store when Neo4j profile is inactive."""

    def is_available(self) -> bool:
        return False

    async def upsert_concept(
        self, user_id: str, concept: str, source_type: str, source_id: str
    ) -> None:
        pass

    async def link_concepts(
        self, user_id: str, concept_a: str, concept_b: str, relation: str
    ) -> None:
        pass

    async def get_related_concepts(
        self, user_id: str, concepts: List[str], limit: int = 5
    ) -> List[str]:
        return []

    async def get_user_graph(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        return {"nodes": [], "edges": []}

    async def delete_by_source(self, user_id: str, source_id: str) -> None:
        pass

    async def delete_user_graph(self, user_id: str) -> None:
        pass


class InMemoryGraphStore:
    """
    Lightweight graph store for unit tests and local graph exploration
    without requiring a running Neo4j instance.
    Enforces user isolation on all nodes and edges.
    """

    def __init__(self):
        # user_id -> concept -> set of (source_type, source_id)
        self.concepts: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
        # user_id -> list of {from, to, relation}
        self.edges: Dict[str, List[Dict[str, str]]] = {}

    def is_available(self) -> bool:
        return True

    async def upsert_concept(
        self, user_id: str, concept: str, source_type: str, source_id: str
    ) -> None:
        c = concept.strip().lower()
        if not c:
            return
        if user_id not in self.concepts:
            self.concepts[user_id] = {}
        if c not in self.concepts[user_id]:
            self.concepts[user_id][c] = []
        self.concepts[user_id][c].append({"type": source_type, "id": source_id})

    async def link_concepts(
        self, user_id: str, concept_a: str, concept_b: str, relation: str
    ) -> None:
        ca = concept_a.strip().lower()
        cb = concept_b.strip().lower()
        if not ca or not cb or ca == cb:
            return
        if user_id not in self.edges:
            self.edges[user_id] = []
        # Check duplicate
        for e in self.edges[user_id]:
            if e["from"] == ca and e["to"] == cb and e["relation"] == relation:
                return
        self.edges[user_id].append({"from": ca, "to": cb, "relation": relation})

    async def get_related_concepts(
        self, user_id: str, concepts: List[str], limit: int = 5
    ) -> List[str]:
        if user_id not in self.edges:
            return []
        query_set = {c.strip().lower() for c in concepts}
        related = set()
        for e in self.edges[user_id]:
            if e["from"] in query_set and e["to"] not in query_set:
                related.add(e["to"])
            elif e["to"] in query_set and e["from"] not in query_set:
                related.add(e["from"])
            if len(related) >= limit:
                break
        return list(related)[:limit]

    async def get_user_graph(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        user_c = self.concepts.get(user_id, {})
        user_e = self.edges.get(user_id, [])

        nodes = [
            {"id": c, "label": c.title(), "sources": src}
            for c, src in user_c.items()
        ]
        edges = [
            {"id": f"{e['from']}->{e['to']}", "source": e["from"], "target": e["to"], "label": e["relation"]}
            for e in user_e
        ]
        return {"nodes": nodes, "edges": edges}

    async def delete_by_source(self, user_id: str, source_id: str) -> None:
        if user_id in self.concepts:
            for c, sources in list(self.concepts[user_id].items()):
                self.concepts[user_id][c] = [s for s in sources if s["id"] != source_id]
                if not self.concepts[user_id][c]:
                    del self.concepts[user_id][c]
                    # Also prune orphan edges
                    if user_id in self.edges:
                        self.edges[user_id] = [
                            e for e in self.edges[user_id]
                            if e["from"] != c and e["to"] != c
                        ]

    async def delete_user_graph(self, user_id: str) -> None:
        self.concepts.pop(user_id, None)
        self.edges.pop(user_id, None)


def extract_concepts_from_text(text: str) -> List[str]:
    """
    Rule-based extraction of technical concepts from text (no LLM).
    Extracts Markdown headings, bolded technical terms, and standard keywords.
    """
    found = set()
    # Markdown headings: # Heading
    for match in re.finditer(r'^#{1,4}\s+([A-Za-z0-9_ -]+)', text, re.MULTILINE):
        h = match.group(1).strip()
        if len(h) < 40 and not any(skip in h.lower() for skip in ["introduction", "summary", "overview"]):
            found.add(h.lower())

    # Bolded terms: **Term**
    for match in re.finditer(r'\*\*([A-Za-z0-9_ -]{3,30})\*\*', text):
        found.add(match.group(1).strip().lower())

    # Pre-defined programming and CS concepts
    CS_CONCEPTS = [
        "hashmap", "array", "binary tree", "dynamic programming", "graph",
        "sorting", "recursion", "stack", "queue", "linked list", "acid",
        "indexing", "normalization", "concurrency", "garbage collection",
        "jvm", "paging", "threads", "deadlock", "asyncio"
    ]
    lower_text = text.lower()
    for c in CS_CONCEPTS:
        if c in lower_text:
            found.add(c)

    return sorted(list(found))[:10]


# Global singleton instance - defaults to InMemoryGraphStore for rich UI exploration
graph_store: GraphStore = InMemoryGraphStore()
