from fastapi import APIRouter
from app.api.v1.endpoints import tenders, analysis, dashboard, company, feedback

api_router = APIRouter()
api_router.include_router(tenders.router, prefix="/tenders", tags=["tenders"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
