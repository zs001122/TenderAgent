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


class CompanyAsset(SQLModel, table=True):
    """Structured company evidence imported from the qualification workbook."""

    __tablename__ = "company_assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str = Field(default="")
    asset_type: str = Field(index=True)
    source_sheet: str = Field(index=True)
    name: str = Field(default="", index=True)
    category: Optional[str] = None
    certificate_no: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None
    amount_wanyuan: Optional[float] = None
    keywords: Optional[str] = None
    data_json: Optional[str] = None
    import_batch_id: Optional[str] = Field(default=None, index=True)
    source_type: str = Field(default="excel_import", index=True)
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: Optional[datetime] = None
    deleted_reason: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
