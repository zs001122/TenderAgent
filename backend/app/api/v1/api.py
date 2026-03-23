from fastapi import APIRouter
from app.api.v1.endpoints import tenders, analysis, dashboard

api_router = APIRouter()
api_router.include_router(tenders.router, prefix="/tenders", tags=["tenders"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
