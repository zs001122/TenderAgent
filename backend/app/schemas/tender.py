from pydantic import BaseModel
from typing import List, Optional

class TenderBase(BaseModel):
    id: str
    title: str
    publish_date: str
    url: str
    content: Optional[str] = None

class TenderResponse(BaseModel):
    id: str
    title: str
    publish_date: str
    url: str
    clean_title: str

class TenderDetail(TenderResponse):
    content: Optional[str] = None
    deadline: Optional[str] = None
