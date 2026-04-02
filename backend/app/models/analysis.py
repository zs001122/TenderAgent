from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tender_id: int = Field(foreign_key="tender.id", index=True)
    
    pass_gate: bool = Field(default=False)
    gate_checks: Optional[str] = None
    match_score: float = Field(default=0.0)
    match_grade: str = Field(default="D")
    recommendation: str = Field(default="")
    
    decision_action: str = Field(default="评估后决定")
    decision_reason: Optional[str] = None
    decision_confidence: float = Field(default=0.0)
    risks: Optional[str] = None
    key_findings: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
