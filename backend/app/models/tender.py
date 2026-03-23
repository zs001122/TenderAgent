from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class Tender(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_url: str = Field(unique=True, index=True)
    source_site: str
    title: str
    publish_date: datetime
    notice_type: Optional[str] = None
    content: Optional[str] = None
    budget_amount: Optional[float] = None
    region: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CrawlLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_site: str
    start_time: datetime
    end_time: Optional[datetime] = None
    new_count: int = 0
    update_count: int = 0
    status: str = "RUNNING"
