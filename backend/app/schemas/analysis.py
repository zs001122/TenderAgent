from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ExtractedInfo(BaseModel):
    budget_wanyuan: float
    deadline: str
    tags: List[str]

class MatchResult(BaseModel):
    total_score: float
    recommendation: str
    match_details: List[str]

class AIAnalysis(BaseModel):
    risk_assessment: str
    competitor_analysis: str
    technical_difficulty: str
    summary: str

class AnalysisResult(BaseModel):
    id: str
    title: str
    extracted_info: ExtractedInfo
    ai_analysis: AIAnalysis
    match_result: MatchResult
