from sqlmodel import Session, select, func
from typing import List, Dict, Optional
from app.db.session import get_session
from app.models.tender import Tender
from datetime import datetime
import json

class TenderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_tenders(self, skip: int = 0, limit: int = 20) -> List[Dict]:
        statement = select(Tender).order_by(Tender.publish_date.desc()).offset(skip).limit(limit)
        results = self.session.exec(statement).all()
        return [self._to_dict(t) for t in results]

    def get_tender_by_id(self, tender_id: str) -> Optional[Dict]:
        try:
            tid = int(tender_id)
            tender = self.session.get(Tender, tid)
            return self._to_dict(tender) if tender else None
        except ValueError:
            return None

    def count_tenders(self) -> int:
        statement = select(func.count(Tender.id))
        return self.session.exec(statement).one()

    # Analysis results are currently stored in JSON (not DB yet), keeping simple for now
    # Ideally, AnalysisResult should be a separate table
    # For this refactor, we will read analysis from file but link to DB tenders
    # NOTE: This is a hybrid approach during migration
    def get_analysis_result(self, tender_id: str) -> Optional[Dict]:
        # Placeholder: In a full DB migration, we'd query an Analysis table
        # For now, we rely on the file-based cache logic from the previous version
        # But since we are refactoring, let's assume we load from file for now
        # TODO: Migrate analysis results to DB
        return None

    def save_analysis_result(self, tender_id: str, result: Dict):
        # Placeholder
        pass

    def get_all_analysis_results(self) -> List[Dict]:
        # Placeholder
        return []

    def get_stats(self) -> Dict:
        total_tenders = self.count_tenders()
        # Mock stats for DB-based implementation
        return {
            "total_tenders": total_tenders,
            "analyzed_count": 0,
            "high_value_count": 0,
            "total_budget_wanyuan": 0,
            "top_tags": []
        }

    def _to_dict(self, tender: Tender) -> Dict:
        return {
            "id": str(tender.id),
            "title": tender.title,
            "clean_title": tender.title, # Assuming title is clean
            "publish_date": tender.publish_date.strftime("%Y-%m-%d"),
            "url": tender.source_url,
            "content": tender.content,
            "deadline": "详见公告" # Not parsed in basic schema yet
        }

# Helper to get repository with a new session
def get_repository():
    session = next(get_session())
    return TenderRepository(session)
