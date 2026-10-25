"""
NEXUS VectorStore Implementation over ChromaDB (Step 1.C.1)
Provides strict isolation by construction:
- All retrieval and mutation methods accept a Principal(user_id, conversation_id)
- Where filters are built internally; raw where clauses are never accepted from callers
- Collections: kb_system, kb_user, memory (all with cosine similarity metric)
- Explicit embeddings only (no implicit embedding functions inside Chroma)
"""

import os
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from app.core.config import settings
from app.schemas.core import Principal


def scope_filter(p: Principal, include_system: bool = True) -> Dict[str, Any]:
    """
    Builds ChromaDB where-filter enforcing user/conversation isolation.
    - Personal scope: user_id must match p.user_id.
    - Chat scope: user_id must match p.user_id AND conversation_id must match p.conversation_id.
    - System scope: readable by any user if include_system is True.
    """
    clauses: List[Dict[str, Any]] = [
        {"$and": [{"user_id": p.user_id}, {"scope": "personal"}]}
    ]

    if p.conversation_id:
        clauses.append({
            "$and": [
                {"user_id": p.user_id},
                {"scope": "chat"},
                {"conversation_id": p.conversation_id}
            ]
        })

    if include_system:
        clauses.append({"scope": "system"})

    if len(clauses) == 1:
        return clauses[0]
    return {"$or": clauses}


class VectorStore:
    def __init__(self, client: Optional[ClientAPI] = None, path: Optional[str] = None):
        if client is not None:
            self.client = client
        else:
            chroma_dir = path or settings.CHROMA_PATH
            os.makedirs(chroma_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(path=chroma_dir)

        # Initialize standard collections with cosine distance
        self.kb_system: Collection = self.client.get_or_create_collection(
            name="kb_system",
            metadata={"hnsw:space": "cosine"}
        )
        self.kb_user: Collection = self.client.get_or_create_collection(
            name="kb_user",
            metadata={"hnsw:space": "cosine"}
        )
        self.memory: Collection = self.client.get_or_create_collection(
            name="memory",
            metadata={"hnsw:space": "cosine"}
        )

    # -------------------------------------------------------------------------
    # System Knowledge Base (read-only for normal users)
    # -------------------------------------------------------------------------
    def upsert_system_chunks(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> int:
        """Upsert system-wide curated knowledge chunks."""
        if not ids:
            return 0
        enriched_metas = []
        for m in metadatas:
            meta = dict(m)
            meta["scope"] = "system"
            enriched_metas.append(meta)

        self.kb_system.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=enriched_metas,
        )
        return len(ids)

    # -------------------------------------------------------------------------
    # User Knowledge Base (strict isolation by construction)
    # -------------------------------------------------------------------------
    def upsert_user_chunks(
        self,
        principal: Principal,
        file_id: str,
        scope: str,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> int:
        """
        Upsert user document chunks, enforcing user ownership and scope parameters.
        Scope must be either 'personal' or 'chat'.
        """
        if scope not in ("personal", "chat"):
            raise ValueError("scope must be either 'personal' or 'chat'")
        if scope == "chat" and not principal.conversation_id:
            raise ValueError("conversation_id required for chat-scoped chunks")

        if not ids:
            return 0

        enriched_metas = []
        for m in metadatas:
            meta = dict(m)
            meta["user_id"] = principal.user_id
            meta["file_id"] = file_id
            meta["scope"] = scope
            if scope == "chat":
                meta["conversation_id"] = principal.conversation_id
            enriched_metas.append(meta)

        self.kb_user.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=enriched_metas,
        )
        return len(ids)

    def query_user_kb(
        self,
        principal: Principal,
        query_embedding: List[float],
        n_results: int = 5,
        include_system: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Query knowledge base with automatic principal-based isolation.
        Searches user collection with scope filter, and merges system chunks if include_system=True.
        """
        results: List[Dict[str, Any]] = []

        # 1. Query kb_user with isolation filter
        user_filter = scope_filter(principal, include_system=False)
        try:
            user_res = self.kb_user.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=user_filter,
                include=["documents", "metadatas", "distances"]
            )
            if user_res["ids"] and user_res["ids"][0]:
                for doc_id, text, meta, dist in zip(
                    user_res["ids"][0],
                    user_res["documents"][0],
                    user_res["metadatas"][0],
                    user_res["distances"][0],
                ):
                    results.append({
                        "id": doc_id,
                        "text": text,
                        "metadata": meta,
                        "score": 1.0 - dist if dist is not None else 0.0,
                        "collection": "kb_user"
                    })
        except Exception:
            # Handle empty collection or no match
            pass

        # 2. Query kb_system if requested
        if include_system:
            try:
                sys_res = self.kb_system.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"]
                )
                if sys_res["ids"] and sys_res["ids"][0]:
                    for doc_id, text, meta, dist in zip(
                        sys_res["ids"][0],
                        sys_res["documents"][0],
                        sys_res["metadatas"][0],
                        sys_res["distances"][0],
                    ):
                        results.append({
                            "id": doc_id,
                            "text": text,
                            "metadata": meta,
                            "score": 1.0 - dist if dist is not None else 0.0,
                            "collection": "kb_system"
                        })
            except Exception:
                pass

        # Sort combined results descending by score and cap to n_results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]

    query_user_and_system = query_user_kb

    def delete_file(self, principal: Principal, file_id: str) -> int:
        """
        Remove all vectors associated with file_id owned by principal.
        Guarantees users can never delete files of other users.
        """
        del_filter = {
            "$and": [
                {"user_id": principal.user_id},
                {"file_id": file_id}
            ]
        }
        # Get count before deletion
        existing = self.kb_user.get(where=del_filter)
        count = len(existing["ids"]) if existing and existing["ids"] else 0
        if count > 0:
            self.kb_user.delete(where=del_filter)
        return count

    # -------------------------------------------------------------------------
    # User Memories
    # -------------------------------------------------------------------------
    def upsert_memory(
        self,
        principal: Principal,
        memory_id: str,
        kind: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a confirmed user memory chunk."""
        meta = dict(metadata or {})
        meta["user_id"] = principal.user_id
        meta["memory_id"] = memory_id
        meta["kind"] = kind

        self.memory.upsert(
            ids=[memory_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[meta],
        )

    def query_memory(
        self,
        principal: Principal,
        query_embedding: List[float],
        n_results: int = 5,
        kind: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query user's confirmed memories."""
        if kind:
            where_clause = {
                "$and": [
                    {"user_id": principal.user_id},
                    {"kind": kind}
                ]
            }
        else:
            where_clause = {"user_id": principal.user_id}

        try:
            res = self.memory.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            return []

        out = []
        if res["ids"] and res["ids"][0]:
            for doc_id, text, meta, dist in zip(
                res["ids"][0],
                res["documents"][0],
                res["metadatas"][0],
                res["distances"][0],
            ):
                out.append({
                    "id": doc_id,
                    "text": text,
                    "metadata": meta,
                    "score": 1.0 - dist if dist is not None else 0.0,
                })
        return out

    def delete_memory(self, principal: Principal, memory_id: str) -> None:
        """Delete a single memory belonging to principal."""
        self.memory.delete(
            where={
                "$and": [
                    {"user_id": principal.user_id},
                    {"memory_id": memory_id}
                ]
            }
        )

    def delete_all_memories(self, principal: Principal) -> None:
        """Delete all memories belonging to principal."""
        self.memory.delete(where={"user_id": principal.user_id})
