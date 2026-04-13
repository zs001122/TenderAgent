from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any, Dict, Optional
from pydantic import BaseModel, Field

from app.db.repository import get_repository, TenderRepository, get_company_repository, CompanyRepository
from app.db.session import get_session
from app.services.pipeline_service import PipelineService, get_pipeline_service


router = APIRouter()


class AnalyzeRequest(BaseModel):
    tender_ids: List[int] = Field(default_factory=list, alias="tenderIds")

    class Config:
        allow_population_by_field_name = True


class BatchAnalyzeResponse(BaseModel):
    total: int
    success: int
    failed: int
    success_ids: List[int]
    failed_items: List[Dict[str, Any]]
    retryable_ids: List[int]


class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = None
    target_domains: Optional[List[str]] = None
    budget_range: Optional[List[float]] = None
    qualifications: Optional[List[str]] = None
    service_regions: Optional[List[str]] = None


@router.get("/", response_model=Dict[str, Any])
def read_tenders(
    skip: int = 0,
    limit: int = 20,
    repo: TenderRepository = Depends(get_repository)
):
    """获取招标列表"""
    tenders = repo.get_tenders(skip=skip, limit=limit)
    total = repo.count_tenders()
    return {
        "total": total,
        "items": tenders,
        "summary": repo.get_tender_overview(),
    }


@router.get("/{tender_id}", response_model=Dict[str, Any])
def read_tender(
    tender_id: int,
    repo: TenderRepository = Depends(get_repository)
):
    """获取招标详情"""
    tender = repo.get_tender_dict_by_id(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="招标不存在")
    return tender


@router.post("/{tender_id}/analyze", response_model=Dict[str, Any])
def analyze_tender(
    tender_id: int,
    session = Depends(get_session)
):
    """触发单个招标分析"""
    service = PipelineService(session)
    result = service.process_tender(tender_id)
    if not result:
        raise HTTPException(status_code=404, detail="招标不存在或分析失败")
    return service.get_full_analysis(tender_id)


@router.post("/analyze-batch", response_model=BatchAnalyzeResponse)
def analyze_batch(
    request: AnalyzeRequest,
    session = Depends(get_session)
):
    """批量分析招标"""
    if not request.tender_ids:
        raise HTTPException(status_code=400, detail="tender_ids 不能为空")
    service = PipelineService(session)
    details = service.process_batch_detailed(request.tender_ids)
    return BatchAnalyzeResponse(
        total=details["total"],
        success=details["success"],
        failed=details["failed"],
        success_ids=details["success_ids"],
        failed_items=details["failed_items"],
        retryable_ids=[item["tender_id"] for item in details["failed_items"]],
    )


@router.post("/analyze-unanalyzed")
def analyze_unanalyzed(
    limit: int = 100,
    session = Depends(get_session)
):
    """分析未处理的招标"""
    service = PipelineService(session)
    result = service.process_unanalyzed(limit)
    return result


@router.get("/{tender_id}/analysis", response_model=Dict[str, Any])
def get_tender_analysis(
    tender_id: int,
    session = Depends(get_session)
):
    """获取招标分析结果"""
    service = PipelineService(session)
    result = service.get_full_analysis(tender_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    return result


@router.get("/recommended/list")
def get_recommended_tenders(
    min_score: float = 60.0,
    limit: int = 20,
    repo: TenderRepository = Depends(get_repository)
):
    """获取推荐招标列表"""
    results = repo.get_recommended_tenders(min_score=min_score, limit=limit)
    return {
        "total": len(results),
        "items": results
    }
