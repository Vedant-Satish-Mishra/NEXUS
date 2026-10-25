from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class RunsPerDayPoint(BaseModel):
    date: str
    count: int
    tier1: int = 0
    tier2: int = 0
    tier3: int = 0

class EvalScorePoint(BaseModel):
    date: str
    avg_score: float

class FeedbackRatio(BaseModel):
    up: int = 0
    down: int = 0
    ratio: float = 0.0

class RecentTask(BaseModel):
    run_id: str
    conversation_id: str
    prompt: str
    tier: int
    status: str
    duration_ms: Optional[int] = None
    created_at: str

class ServicesHealth(BaseModel):
    ollama: bool = True
    db: bool = True
    chroma: bool = True
    sandbox: bool = True

class DashboardData(BaseModel):
    runs_per_day: List[RunsPerDayPoint] = Field(default_factory=list)
    avg_latency_by_tier: Dict[str, float] = Field(default_factory=dict)
    evaluation_score_trend: List[EvalScorePoint] = Field(default_factory=list)
    feedback_ratio: FeedbackRatio = Field(default_factory=FeedbackRatio)
    files_count: int = 0
    chunks_count: int = 0
    memories_count: int = 0
    recent_tasks: List[RecentTask] = Field(default_factory=list)
    services_health: ServicesHealth = Field(default_factory=ServicesHealth)
