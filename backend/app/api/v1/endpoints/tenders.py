from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any, Dict
from app.schemas import tender as schemas
from app.db.repository import get_repository, TenderRepository

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
def read_tenders(
    skip: int = 0,
    limit: int = 20,
    repo: TenderRepository = Depends(get_repository)
):
    """
    Retrieve tenders.
    """
    tenders = repo.get_tenders(skip=skip, limit=limit)
    total = repo.count_tenders()
    return {
        "total": total,
        "items": tenders
    }

@router.get("/{tender_id}", response_model=schemas.TenderDetail)
def read_tender(
    tender_id: str,
    repo: TenderRepository = Depends(get_repository)
):
    """
    Get tender by ID.
    """
    tender = repo.get_tender_by_id(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender
