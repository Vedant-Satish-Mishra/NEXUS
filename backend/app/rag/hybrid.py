"""
NEXUS Hybrid Search Engine (Milestone 3)
Step 3.C.3 — Vector + BM25 Fusion using Reciprocal Rank Fusion (RRF)
Strictly isolated by Principal; includes prompt-injection sanitization.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.rag.embeddings import get_embedder
from app.rag.vectorstore import VectorStore
from app.schemas.core import Principal

logger = logging.getLogger("nexus.rag.hybrid")

# Standard English stop words
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with", "i", "you", "we", "they"
}

# Prompt injection filters
INJECTION_PATTERNS = [
    r'^\s*system\s*:',
    r'^\s*assistant\s*:',
    r'^\s*user\s*:',
    r'ignore\s+(all\s+)?(previous|prior)\s+instructions',
    r'disregard\s+(all\s+)?(previous|prior|system)\s+(instructions|prompt)',
    r'system\s+override',
    r'new\s+system\s+prompt',
]


def sanitize_chunk_text(text: str) -> tuple[str, bool]:
    """
    Strips potential prompt-injection patterns from document chunks.
    Returns (sanitized_text, was_modified).
    """
    lines = text.splitlines()
    cleaned_lines = []
    modified = False

    for line in lines:
        is_suspicious = False
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                is_suspicious = True
                modified = True
                break
        if not is_suspicious:
            cleaned_lines.append(line)
        else:
            cleaned_lines.append("[sanitized instruction marker]")

    return "\n".join(cleaned_lines), modified


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokenizer with stop-word removal."""
    words = re.findall(r'\b[a-zA-Z0-9_]+\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]


def reciprocal_rank_fusion(rank_lists: List[List[str]], k: int = 60) -> List[str]:
    """
    Standard Reciprocal Rank Fusion (RRF) algorithm:
    RRF_score(d) = sum( 1 / (k + rank + 1) )
    """
    scores: Dict[str, float] = {}
    for ranks in rank_lists:
        for r, doc_id in enumerate(ranks):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + r + 1)
    return sorted(scores.keys(), key=lambda d: scores[d], reverse=True)


class HybridRetriever:
    def __init__(self, vectorstore: Optional[VectorStore] = None):
        self.vs = vectorstore or VectorStore()
        self.embedder = get_embedder()

    async def search_hybrid(
        self,
        principal: Principal,
        query: str,
        top_k: int = 6,
        min_score: float = 0.35,
        source_boosts: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search:
        1. Retrieves 3x candidate pool using semantic vector search.
        2. Computes BM25 keyword ranking over the candidate documents.
        3. Fuses both rankings via Reciprocal Rank Fusion (k=60).
        4. Returns normalized results with vector_score and bm25_score.
        """
        if not query.strip():
            return []

        # 1. Fetch 3x candidates from VectorStore
        pool_size = max(top_k * 3, 15)
        query_emb = await self.embedder.embed_query(query)
        candidates = self.vs.query_user_and_system(
            principal=principal,
            query_embedding=query_emb,
            n_results=pool_size,
            include_system=True
        )

        if not candidates:
            return []

        doc_ids = [c["id"] for c in candidates]
        cand_map = {c["id"]: c for c in candidates}

        # Vector ranking list
        vector_rank_list = doc_ids[:]

        # 2. BM25 keyword ranking over candidates
        corpus_tokens = [tokenize(c["text"]) for c in candidates]
        query_tokens = tokenize(query)

        bm25_rank_list = []
        bm25_scores_map = {}

        if query_tokens and any(corpus_tokens):
            bm25 = BM25Okapi(corpus_tokens)
            doc_scores = bm25.get_scores(query_tokens)
            ranked_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)
            bm25_rank_list = [doc_ids[i] for i in ranked_indices]
            max_bm25 = max(doc_scores) if max(doc_scores) > 0 else 1.0
            for idx, cid in enumerate(doc_ids):
                bm25_scores_map[cid] = round(float(doc_scores[idx] / max_bm25), 3)
        else:
            bm25_rank_list = vector_rank_list
            bm25_scores_map = {cid: 0.0 for cid in doc_ids}

        # 3. Fuse via Reciprocal Rank Fusion
        fused_ids = reciprocal_rank_fusion([vector_rank_list, bm25_rank_list], k=60)

        # 4. Format and apply threshold
        results: List[Dict[str, Any]] = []
        for r_idx, cid in enumerate(fused_ids):
            item = cand_map[cid]
            meta = item.get("metadata", {})
            v_score = round(float(item.get("score", 0.0)), 3)
            b_score = bm25_scores_map.get(cid, 0.0)
            
            # Blended score for threshold filtering
            blended_score = (v_score * 0.6) + (b_score * 0.4)
            if source_boosts:
                # Source boost bounded within +/- 10% (0.9 to 1.1)
                fid = str(meta.get("file_id", ""))
                src = str(meta.get("source", ""))
                raw_boost = source_boosts.get(fid, source_boosts.get(src, 1.0))
                boost = max(0.90, min(1.10, float(raw_boost)))
                blended_score *= boost
            blended_score = round(blended_score, 3)

            if blended_score < min_score:
                continue

            results.append({
                "id": cid,
                "text": item.get("text", ""),
                "source": meta.get("source", "knowledge_base"),
                "page": meta.get("page", 1),
                "score": blended_score,
                "vector_score": v_score,
                "bm25_score": b_score,
                "rrf_rank": r_idx + 1,
                "topic": meta.get("topic", "General"),
                "heading_path": meta.get("heading_path", "")
            })

            if len(results) >= top_k:
                break

        return results
