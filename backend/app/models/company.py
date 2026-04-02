from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class CompanyProfile(SQLModel, table=True):
    __tablename__ = "company_profiles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="默认公司")
    target_domains: Optional[str] = None
    budget_range_min: Optional[float] = Field(default=50.0)
    budget_range_max: Optional[float] = Field(default=1000.0)
    qualifications: Optional[str] = None
    service_regions: Optional[str] = None
    bid_history: Optional[str] = None
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
