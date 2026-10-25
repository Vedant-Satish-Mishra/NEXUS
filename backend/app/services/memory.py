"""
NEXUS Memory Service (Milestone 3)
Step 3.B.1 & Step 3.D.2 — Semantic memory recall with recency weighting,
rule-based proposals, and user-confirmed persistence.
"""

from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.models import Memory, MemoryProposalRecord
from app.rag.embeddings import get_embedder
from app.rag.vectorstore import VectorStore
from app.schemas.core import Principal

SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',
    r'ghp_[a-zA-Z0-9]{20,}',
    r'password\s*[:=]\s*\S+',
    r'secret\s*[:=]\s*\S+',
    r'api[_-]?key\s*[:=]\s*\S+',
    r'bearer\s+[a-zA-Z0-9_\-\.]+',
]

TRIVIA_PATTERNS = [
    r'^what is \d+[\+\-\*\/]\d+',
    r'^what time is it',
    r'^hello',
    r'^hi',
]


def contains_secret(text: str) -> bool:
    for pat in SECRET_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def is_trivia(text: str) -> bool:
    t_clean = text.strip().lower()
    for pat in TRIVIA_PATTERNS:
        if re.search(pat, t_clean):
            return True
    return False


def calculate_recency_factor(timestamp_str: Optional[str], half_life_days: float = 60.0) -> float:
    """Calculates exponential decay factor: e^(-lambda * dt) where lambda = ln(2) / half_life."""
    if not timestamp_str:
        return 1.0
    try:
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta_days = (now - dt).total_seconds() / 86400.0
        decay = math.exp(- (math.log(2) / half_life_days) * max(delta_days, 0.0))
        return round(decay, 3)
    except Exception:
        return 1.0


class MemoryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.vectorstore = VectorStore()
        self.embedder = get_embedder()

    async def recall_memories(
        self,
        principal: Principal,
        query: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recalls confirmed user memories:
        Semantic search over the user's memories, ranked by:
        score = similarity * (0.7 + 0.3 * importance) * recency_factor(half_life=60 days)
        """
        if not query.strip():
            return []

        query_emb = await self.embedder.embed_query(query)
        try:
            res = self.vectorstore.memory.query(
                query_embeddings=[query_emb],
                n_results=k * 2,
                where={"user_id": principal.user_id},
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            return []

        if not res["ids"] or not res["ids"][0]:
            return []

        ranked_items = []
        for mid, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            sim = 1.0 - dist if dist is not None else 0.5
            importance = float(meta.get("importance", 0.5))
            recency = calculate_recency_factor(meta.get("confirmed_at"))
            final_score = sim * (0.7 + 0.3 * importance) * recency
            ranked_items.append({
                "id": mid,
                "content": doc,
                "kind": meta.get("kind", "long_term"),
                "importance": importance,
                "score": round(final_score, 3)
            })

        ranked_items.sort(key=lambda x: x["score"], reverse=True)
        return ranked_items[:k]

    async def extract_and_propose(
        self,
        user_id: str,
        run_id: str,
        user_input: str,
        plan: Optional[Dict[str, Any]] = None,
        tier: int = 1
    ) -> List[Dict[str, str]]:
        """
        Extracts candidate memories from message using heuristic rules.
        Rejects credentials and trivia. Persists ONLY to memory_proposals table.
        """
        if contains_secret(user_input) or is_trivia(user_input):
            return []

        proposals: List[Dict[str, str]] = []

        # Rule 1: Explicit "remember that ..." / "remember ..."
        match_rem = re.search(r'\bremember\s+(?:that\s+)?(.+)', user_input, re.IGNORECASE)
        if match_rem:
            candidate = match_rem.group(1).strip()
            if candidate and not contains_secret(candidate):
                proposals.append({"kind": "long_term", "content": candidate})

        # Rule 2: Goals / Preparation
        match_goal = re.search(r'\b(i am preparing for|my goal is to|i want to become)\s+(.+)', user_input, re.IGNORECASE)
        if match_goal:
            proposals.append({"kind": "long_term", "content": f"{match_goal.group(1)} {match_goal.group(2).strip()}"})

        # Rule 3: Preferences
        match_pref = re.search(r'\b(i prefer|i like to use|my preferred stack is)\s+(.+)', user_input, re.IGNORECASE)
        if match_pref:
            proposals.append({"kind": "long_term", "content": f"{match_pref.group(1)} {match_pref.group(2).strip()}"})

        # Rule 4: Episodic memory for completed complex plans
        if tier == 3 and plan and plan.get("goal"):
            proposals.append({
                "kind": "episodic",
                "content": f"Completed structured plan for: {plan.get('goal')}"
            })

        # Save to DB memory_proposals table (pending)
        saved_proposals = []
        if proposals:
            async with self.session_factory() as db:
                for p in proposals:
                    rec = MemoryProposalRecord(
                        user_id=user_id,
                        run_id=run_id,
                        kind=p["kind"],
                        content=p["content"],
                        status="pending"
                    )
                    db.add(rec)
                    saved_proposals.append({"id": rec.id, "kind": rec.kind, "content": rec.content})
                await db.commit()

        return saved_proposals

    async def decide_proposal(
        self,
        user_id: str,
        proposal_id: str,
        action: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Human decision endpoint for memory proposals:
        - accept/edit: creates verified Memory row & upserts into ChromaDB memory collection
        - reject: marks proposal rejected
        """
        async with self.session_factory() as db:
            stmt = select(MemoryProposalRecord).where(
                MemoryProposalRecord.id == proposal_id,
                MemoryProposalRecord.user_id == user_id
            )
            prop = (await db.execute(stmt)).scalar_one_or_none()
            if not prop:
                return {"status": "not_found"}

            if action in ["accept", "edit"]:
                final_content = (content or prop.content).strip()
                now = datetime.now(timezone.utc)
                
                # Create confirmed Memory row
                mem = Memory(
                    user_id=user_id,
                    kind=prop.kind,
                    content=final_content,
                    source_run_id=prop.run_id,
                    confirmed_at=now,
                    active=True,
                    chroma_id=f"mem_{prop.id}"
                )
                db.add(mem)
                prop.status = "accepted" if action == "accept" else "edited"
                await db.commit()
                await db.refresh(mem)

                # Upsert into ChromaDB memory collection
                emb = await self.embedder.embed_query(final_content)
                self.vectorstore.memory.upsert(
                    ids=[mem.chroma_id],
                    documents=[final_content],
                    embeddings=[emb],
                    metadatas=[{
                        "user_id": user_id,
                        "kind": prop.kind,
                        "importance": 0.8,
                        "confirmed_at": now.isoformat()
                    }]
                )
                return {"status": "saved", "memory_id": mem.id}

            elif action == "reject":
                prop.status = "rejected"
                await db.commit()
                return {"status": "rejected"}

            return {"status": "unknown_action"}

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Deletes confirmed memory row and vector record."""
        async with self.session_factory() as db:
            stmt = select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
            mem = (await db.execute(stmt)).scalar_one_or_none()
            if not mem:
                return False

            chroma_id = mem.chroma_id
            await db.delete(mem)
            await db.commit()

        if chroma_id:
            try:
                self.vectorstore.memory.delete(ids=[chroma_id])
            except Exception:
                pass
        return True

    async def wipe_all_memories(self, user_id: str) -> int:
        """Wipes all memories and vector records for the given user."""
        async with self.session_factory() as db:
            stmt = select(Memory).where(Memory.user_id == user_id)
            memories = (await db.execute(stmt)).scalars().all()
            count = len(memories)
            for m in memories:
                if m.chroma_id:
                    try:
                        self.vectorstore.memory.delete(ids=[m.chroma_id])
                    except Exception:
                        pass
                await db.delete(m)
            await db.commit()
            return count
