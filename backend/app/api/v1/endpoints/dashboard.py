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
