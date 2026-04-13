from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class AnalysisTrace(SQLModel, table=True):
    __tablename__ = "analysis_traces"

    id: Optional[int] = Field(default=None, primary_key=True)
    tender_id: int = Field(index=True)
    configured_mode: str = Field(default="hybrid")
    selected_mode: str = Field(default="rule")
    fallback_used: bool = Field(default=False)
    success: bool = Field(default=True)
    error_count: int = Field(default=0)
    duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
