from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.db.repository import get_repository, TenderRepository

router = APIRouter()

@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(
    repo: TenderRepository = Depends(get_repository)
):
    """
    Get dashboard statistics.
    """
    return repo.get_stats()


@router.get("/crawler-health", response_model=Dict[str, Any])
def get_crawler_health(
    hours: int = 24,
    repo: TenderRepository = Depends(get_repository),
):
    """获取抓取链路健康指标。"""
    return repo.get_crawler_health_stats(hours=hours)


@router.get("/analysis-mode-metrics", response_model=Dict[str, Any])
def get_analysis_mode_metrics(
    hours: int = 24,
    repo: TenderRepository = Depends(get_repository),
):
    """获取分析模式统计（agent 命中率 / fallback 比例 / 平均耗时）。"""
    return repo.get_analysis_mode_stats(hours=hours)
