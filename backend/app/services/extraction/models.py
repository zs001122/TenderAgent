from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class BudgetInfo:
    value: Optional[float] = None
    unit: str = "万元"
    confidence: float = 0.0
    raw_values: List[Dict[str, Any]] = field(default_factory=list)
    source: str = ""


@dataclass
class DeadlineInfo:
    value: Optional[datetime] = None
    raw_text: str = ""
    confidence: float = 0.0


@dataclass
class QualificationInfo:
    required: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ContactInfo:
    person: str = ""
    phone: str = ""
    email: str = ""
    confidence: float = 0.0


@dataclass
class ExtractedInfo:
    budget: BudgetInfo = field(default_factory=BudgetInfo)
    deadline: DeadlineInfo = field(default_factory=DeadlineInfo)
    qualifications: QualificationInfo = field(default_factory=QualificationInfo)
    contact: ContactInfo = field(default_factory=ContactInfo)
    tags: List[str] = field(default_factory=list)
    region: str = ""
    project_type: str = ""
    validation_issues: List[str] = field(default_factory=list)
    is_reliable: bool = True
    extraction_time: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractionResult:
    success: bool
    info: ExtractedInfo
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
