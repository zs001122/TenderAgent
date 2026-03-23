from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from app.schemas import analysis as schemas
from app.db.repository import get_repository, TenderRepository
from app.services.analysis_service import get_analysis_service, AnalysisService

router = APIRouter()

@router.post("/{tender_id}", response_model=schemas.AnalysisResult)
def analyze_tender(
    tender_id: str,
    repo: TenderRepository = Depends(get_repository),
    service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analyze a tender by ID.
    """
    # Check cache first
    cached_result = repo.get_analysis_result(tender_id)
    if cached_result:
        return cached_result

    # Get tender data
    tender = repo.get_tender_by_id(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    try:
        # Perform analysis
        result = service.analyze_tender(tender)
        
        # Save to cache/db
        repo.save_analysis_result(tender_id, result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.AnalysisResult])
def read_analysis_results(
    repo: TenderRepository = Depends(get_repository)
):
    """
    Get all analysis results.
    """
    return repo.get_all_analysis_results()
