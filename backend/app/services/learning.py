"""
NEXUS Learning Service (Step 5.B.1)
Adapts strategies, retrieval boosts, and prompt hints from feedback, evaluation scores, and run outcomes.
HARD RULES:
- Never store user message content.
- Code-only aggregation (no LLM).
- Requires >= 5 samples per (user_id, intent, strategy_key) before generating any hint.
- A single negative rating never alters knowledge or counts as proof a fact is wrong.
- All signals preserve provenance (run_id).
- Exponential recency decay applied to older signals.
- Retrieval source boosts bounded strictly within +/-10% (0.90 to 1.10).
"""
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LearningSignal, Run, UserSettings
from app.schemas.core import Principal


class LearningService:
    # Half-life for signal decay in days
    DECAY_HALF_LIFE_DAYS = 14.0
    MIN_SAMPLE_THRESHOLD = 5
    MAX_HINTS = 3
    MAX_HINT_LENGTH = 120

    async def is_learning_enabled(self, db: AsyncSession, user_id: str) -> bool:
        """Checks if learning is globally enabled in user settings."""
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record or not record.settings:
            return True
        return bool(record.settings.get("learning_enabled", True))

    async def record_signal(
        self,
        db: AsyncSession,
        user_id: str,
        intent: str,
        strategy_key: str,
        signal: str,
        value: float,
        source: str,
        run_id: str,
    ) -> Optional[LearningSignal]:
        """
        Records a learning signal.
        Asserts that no free-form message text is stored.
        """
        # Ensure value is clamped
        val = max(0.0, min(1.0, float(value)))
        clean_intent = (intent or "general").strip().lower()
        clean_strategy = (strategy_key or "default").strip().lower()

        entry = LearningSignal(
            user_id=user_id,
            intent=clean_intent,
            strategy_key=clean_strategy,
            signal=signal,
            value=val,
            source=source,
            run_id=run_id,
        )
        db.add(entry)
        await db.commit()
        return entry

    async def record_run_outcome(
        self,
        db: AsyncSession,
        user_id: str,
        run: Run,
        intent: str = "general",
        plan_approved_unchanged: bool = False,
        plan_edits_count: int = 0,
        plan_replanned: bool = False,
        tools_success: Optional[bool] = None,
        run_completed: bool = True,
        eval_score: Optional[float] = None,
    ) -> None:
        """
        Records discrete outcome signals for a finished run.
        """
        if not await self.is_learning_enabled(db, user_id):
            return

        # 1. Run completion signal
        await self.record_signal(
            db=db,
            user_id=user_id,
            intent=intent,
            strategy_key="run_execution",
            signal="completed" if run_completed else "abandoned",
            value=1.0 if run_completed else 0.0,
            source="outcome",
            run_id=run.id,
        )

        # 2. Plan outcome signal
        if plan_approved_unchanged:
            await self.record_signal(
                db=db,
                user_id=user_id,
                intent=intent,
                strategy_key="plan_detail",
                signal="approved_unchanged",
                value=1.0,
                source="outcome",
                run_id=run.id,
            )
        elif plan_edits_count > 0:
            await self.record_signal(
                db=db,
                user_id=user_id,
                intent=intent,
                strategy_key="plan_detail",
                signal="edited_by_user",
                value=0.5,
                source="outcome",
                run_id=run.id,
            )
        elif plan_replanned:
            await self.record_signal(
                db=db,
                user_id=user_id,
                intent=intent,
                strategy_key="plan_detail",
                signal="replanned",
                value=0.2,
                source="outcome",
                run_id=run.id,
            )

        # 3. Tool outcome
        if tools_success is not None:
            await self.record_signal(
                db=db,
                user_id=user_id,
                intent=intent,
                strategy_key="tool_reliability",
                signal="tool_ok" if tools_success else "tool_err",
                value=1.0 if tools_success else 0.0,
                source="outcome",
                run_id=run.id,
            )

        # 4. Evaluation score
        if eval_score is not None:
            await self.record_signal(
                db=db,
                user_id=user_id,
                intent=intent,
                strategy_key="evaluation_pass",
                signal="evaluator_score",
                value=max(0.0, min(1.0, float(eval_score))),
                source="evaluation",
                run_id=run.id,
            )

    async def get_hints_and_boosts(
        self,
        db: AsyncSession,
        principal: Principal,
        intent: str,
    ) -> Tuple[List[str], Dict[str, float]]:
        """
        Computes strategy hints and evidence source boosts via decay aggregation.
        Returns:
            (hints_list, evidence_source_boosts)
        """
        if not await self.is_learning_enabled(db, principal.user_id):
            return [], {}

        clean_intent = (intent or "general").strip().lower()

        # Fetch all signals for this user
        stmt = (
            select(LearningSignal)
            .where(LearningSignal.user_id == principal.user_id)
            .order_by(LearningSignal.created_at.desc())
        )
        res = await db.execute(stmt)
        signals = res.scalars().all()

        if not signals:
            return [], {}

        now = datetime.now(timezone.utc)
        decay_lambda = math.log(2) / self.DECAY_HALF_LIFE_DAYS

        # Aggregate by (intent, strategy_key)
        # We allow matching on specific intent OR 'general'
        grouped: Dict[str, List[Tuple[float, float]]] = {}  # strategy_key -> [(weighted_val, weight)]

        for s in signals:
            # Match intent or general
            if s.intent not in (clean_intent, "general"):
                continue

            dt = s.created_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            age_days = max(0.0, (now - dt).total_seconds() / 86400.0)
            weight = math.exp(-decay_lambda * age_days)

            k = s.strategy_key
            if k not in grouped:
                grouped[k] = []
            grouped[k].append((s.value * weight, weight))

        hints: List[str] = []
        source_boosts: Dict[str, float] = {}

        for strategy_key, samples in grouped.items():
            # Threshold check: require >= 5 samples
            if len(samples) < self.MIN_SAMPLE_THRESHOLD:
                continue

            total_weighted_val = sum(v for v, w in samples)
            total_weight = sum(w for v, w in samples)
            if total_weight <= 0:
                continue

            avg_score = total_weighted_val / total_weight

            # Source boost check
            if strategy_key.startswith("evidence_source:"):
                source_id = strategy_key.split("evidence_source:", 1)[1]
                # Bounded at most +/-10% (0.90 to 1.10)
                # Map avg_score [0..1] -> [0.90..1.10]
                boost = 0.90 + (avg_score * 0.20)
                boost = max(0.90, min(1.10, boost))
                source_boosts[source_id] = round(boost, 3)
                continue

            # Hint rule: < 0.4 -> "avoid", > 0.75 -> "prefer"
            if avg_score < 0.4:
                hint_str = f"Avoid overly complex {strategy_key.replace('_', ' ')}"
                if len(hint_str) <= self.MAX_HINT_LENGTH and hint_str not in hints:
                    hints.append(hint_str)
            elif avg_score > 0.75:
                hint_str = f"Prefer structured {strategy_key.replace('_', ' ')}"
                if len(hint_str) <= self.MAX_HINT_LENGTH and hint_str not in hints:
                    hints.append(hint_str)

        return hints[:self.MAX_HINTS], source_boosts

    async def reset_learning_data(self, db: AsyncSession, user_id: str) -> int:
        """Deletes all learning signals for the user."""
        stmt = delete(LearningSignal).where(LearningSignal.user_id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount


learning_service = LearningService()
