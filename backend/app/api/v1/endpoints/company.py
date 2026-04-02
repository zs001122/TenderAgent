from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.db.repository import get_company_repository, CompanyRepository


router = APIRouter()


class CompanyProfileInput(BaseModel):
    name: Optional[str] = None
    target_domains: Optional[List[str]] = None
    budget_range: Optional[List[float]] = None
    qualifications: Optional[List[str]] = None
    service_regions: Optional[List[str]] = None
    bid_history: Optional[List[Dict[str, Any]]] = None


@router.get("/", response_model=Dict[str, Any])
def get_company_profile(
    repo: CompanyRepository = Depends(get_company_repository)
):
    """获取公司画像配置"""
    return repo.get_profile_dict()


@router.put("/", response_model=Dict[str, Any])
def update_company_profile(
    profile_data: CompanyProfileInput,
    repo: CompanyRepository = Depends(get_company_repository)
):
    """更新公司画像配置"""
    update_dict = profile_data.dict(exclude_unset=True)
    profile = repo.save_profile(update_dict)
    return repo.get_profile_dict()


@router.post("/reset")
def reset_company_profile(
    repo: CompanyRepository = Depends(get_company_repository)
):
    """重置为默认公司画像"""
    default_profile = {
        "name": "默认公司",
        "target_domains": ["软件开发", "大数据", "AI/人工智能"],
        "budget_range": [50, 1000],
        "qualifications": ["CMMI3", "ISO27001", "高新技术企业"],
        "service_regions": ["广东省", "北京市", "上海市"],
        "bid_history": [],
    }
    repo.save_profile(default_profile)
    return {"message": "已重置为默认配置", "profile": default_profile}
