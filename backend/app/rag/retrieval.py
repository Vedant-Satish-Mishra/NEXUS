"""
NEXUS Retrieval Service
Step 2.C.2 — Multi-query hybrid vector search with de-duplication and isolation
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.rag.embeddings import get_embedder
from app.rag.vectorstore import VectorStore
from app.schemas.core import Principal

logger = logging.getLogger("nexus.rag.retrieval")


class RetrievalService:
    def __init__(self, vectorstore: Optional[VectorStore] = None):
        self.vs = vectorstore or VectorStore()
        self.embedder = get_embedder()

    async def search(
        self,
        principal: Principal,
        queries: List[str],
        top_k_per_query: int = 3,
        min_score: Optional[float] = None,
        max_chunks: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes multi-query search with:
        1. Tenant-isolated VectorStore lookup
        2. Chunk ID de-duplication preserving highest score
        3. Strict score cutoff (min_score)
        4. Global max_chunks capping
        """
        threshold = min_score if min_score is not None else settings.RAG_MIN_SCORE
        limit = max_chunks if max_chunks is not None else settings.RAG_MAX_CHUNKS

        if not queries:
            return []

        # Deduplicate and cap query count to 5
        clean_queries = [q.strip() for q in queries if q.strip()][:5]
        chunk_map: Dict[str, Dict[str, Any]] = {}

        for query in clean_queries:
            query_emb = await self.embedder.embed_query(query)
            results = self.vs.query_user_and_system(
                principal=principal,
                query_embedding=query_emb,
                n_results=top_k_per_query,
                include_system=True
            )

            for item in results:
                cid = item["id"]
                score = item.get("score", 0.0)
                if score < threshold:
                    continue

                meta = item.get("metadata", {})
                formatted_chunk = {
                    "id": cid,
                    "text": item.get("text", ""),
                    "source": meta.get("source", "knowledge_base"),
                    "page": meta.get("page", 1),
                    "score": round(score, 3),
                    "topic": meta.get("topic", "General"),
                    "heading_path": meta.get("heading_path", "")
                }

                if cid not in chunk_map or score > chunk_map[cid]["score"]:
                    chunk_map[cid] = formatted_chunk

        merged = list(chunk_map.values())
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged[:limit]


_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
