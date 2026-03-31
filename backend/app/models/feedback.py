from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class BidRecord(SQLModel, table=True):
    """投标记录表
    
    记录投标行为和结果，用于反馈学习
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    tender_id: int = Field(foreign_key="tender.id", index=True)
    
    bid_date: datetime = Field(default_factory=datetime.now)
    bid_price: float = Field(default=0.0)
    
    is_won: bool = Field(default=False)
    win_date: Optional[datetime] = Field(default=None)
    
    lose_reason: Optional[str] = Field(default=None)
    feedback_notes: Optional[str] = Field(default=None)
    
    predicted_score: float = Field(default=0.0)
    predicted_recommendation: str = Field(default="")
    predicted_grade: str = Field(default="D")
    
    actual_result: str = Field(default="待定")
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FeedbackAnalysis(SQLModel, table=True):
    """反馈分析表
    
    存储模型优化分析结果
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    analysis_date: datetime = Field(default_factory=datetime.now)
    total_records: int = Field(default=0)
    correct_predictions: int = Field(default=0)
    accuracy: float = Field(default=0.0)
    
    high_score_won: int = Field(default=0)
    high_score_lost: int = Field(default=0)
    low_score_won: int = Field(default=0)
    low_score_lost: int = Field(default=0)
    
    recommendations: str = Field(default="")
    
    created_at: datetime = Field(default_factory=datetime.now)
