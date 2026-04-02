from sqlmodel import Session, select, func, or_
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

from app.models.tender import Tender, CrawlLog
from app.models.analysis import AnalysisResult
from app.models.company import CompanyProfile


class TenderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_tenders(self, skip: int = 0, limit: int = 20) -> List[Dict]:
        statement = select(Tender).order_by(Tender.publish_date.desc()).offset(skip).limit(limit)
        results = self.session.exec(statement).all()
        return [self._to_dict(t) for t in results]

    def get_tender_by_id(self, tender_id: int) -> Optional[Tender]:
        return self.session.get(Tender, tender_id)

    def get_tender_dict_by_id(self, tender_id: int) -> Optional[Dict]:
        tender = self.get_tender_by_id(tender_id)
        return self._to_dict(tender) if tender else None

    def count_tenders(self) -> int:
        statement = select(func.count(Tender.id))
        return self.session.exec(statement).one()

    def get_unanalyzed_tenders(self, limit: int = 100) -> List[Tender]:
        subquery = select(AnalysisResult.tender_id).distinct()
        statement = (
            select(Tender)
            .where(or_(Tender.extraction_status == None, Tender.extraction_status == ""))
            .order_by(Tender.publish_date.desc())
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def get_tenders_without_analysis(self, limit: int = 100) -> List[Tender]:
        subquery = select(AnalysisResult.tender_id).distinct()
        statement = (
            select(Tender)
            .where(Tender.id.not_in(subquery))
            .order_by(Tender.publish_date.desc())
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def update_extraction_result(self, tender_id: int, extraction: Dict[str, Any]) -> None:
        tender = self.session.get(Tender, tender_id)
        if tender:
            if extraction.get("budget"):
                tender.budget_amount = extraction["budget"].get("value")
                tender.budget_confidence = extraction["budget"].get("confidence", 0.0)
            if extraction.get("deadline"):
                tender.deadline = extraction["deadline"].get("value")
            if extraction.get("qualifications"):
                tender.qualifications = json.dumps(
                    extraction["qualifications"].get("required", []), 
                    ensure_ascii=False
                )
            if extraction.get("contact"):
                tender.contact_person = extraction["contact"].get("person")
                tender.contact_phone = extraction["contact"].get("phone")
                tender.contact_email = extraction["contact"].get("email")
            if extraction.get("tags"):
                tender.tags = json.dumps(extraction["tags"], ensure_ascii=False)
            if extraction.get("project_type"):
                tender.project_type = extraction["project_type"]
            if extraction.get("region"):
                tender.region = extraction["region"]
            
            tender.extraction_status = "completed"
            tender.extraction_time = datetime.utcnow()
            tender.updated_at = datetime.utcnow()
            self.session.add(tender)
            self.session.commit()

    def save_analysis_result(self, result: AnalysisResult) -> AnalysisResult:
        result.updated_at = datetime.utcnow()
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result

    def get_analysis_by_tender_id(self, tender_id: int) -> Optional[AnalysisResult]:
        statement = select(AnalysisResult).where(AnalysisResult.tender_id == tender_id)
        return self.session.exec(statement).first()

    def get_analysis_result(self, tender_id: int) -> Optional[Dict]:
        analysis = self.get_analysis_by_tender_id(tender_id)
        return self._analysis_to_dict(analysis) if analysis else None

    def get_all_analysis_results(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        statement = (
            select(AnalysisResult)
            .order_by(AnalysisResult.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [self._analysis_to_dict(a) for a in results]

    def get_recommended_tenders(self, min_score: float = 60.0, limit: int = 20) -> List[Dict]:
        statement = (
            select(Tender, AnalysisResult)
            .join(AnalysisResult, Tender.id == AnalysisResult.tender_id)
            .where(AnalysisResult.pass_gate == True)
            .where(AnalysisResult.match_score >= min_score)
            .order_by(AnalysisResult.match_score.desc())
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [
            {
                "tender": self._to_dict(t),
                "analysis": self._analysis_to_dict(a)
            }
            for t, a in results
        ]

    def get_stats(self) -> Dict:
        total_tenders = self.count_tenders()
        analyzed_count = self.session.exec(
            select(func.count(AnalysisResult.id))
        ).one()
        high_value_count = self.session.exec(
            select(func.count(AnalysisResult.id)).where(AnalysisResult.match_grade == "A")
        ).one()
        
        total_budget = self.session.exec(
            select(func.sum(Tender.budget_amount)).where(Tender.budget_amount != None)
        ).one() or 0
        
        return {
            "total_tenders": total_tenders,
            "analyzed_count": analyzed_count,
            "high_value_count": high_value_count,
            "total_budget_wanyuan": total_budget,
            "top_tags": []
        }

    def _to_dict(self, tender: Tender) -> Dict:
        return {
            "id": tender.id,
            "title": tender.title,
            "source_url": tender.source_url,
            "source_site": tender.source_site,
            "publish_date": tender.publish_date.strftime("%Y-%m-%d") if tender.publish_date else None,
            "notice_type": tender.notice_type,
            "content": tender.content,
            "region": tender.region,
            "budget_amount": tender.budget_amount,
            "budget_confidence": tender.budget_confidence,
            "deadline": tender.deadline.strftime("%Y-%m-%d %H:%M") if tender.deadline else None,
            "qualifications": json.loads(tender.qualifications) if tender.qualifications else [],
            "contact_person": tender.contact_person,
            "contact_phone": tender.contact_phone,
            "contact_email": tender.contact_email,
            "tags": json.loads(tender.tags) if tender.tags else [],
            "project_type": tender.project_type,
            "extraction_status": tender.extraction_status,
        }

    def _analysis_to_dict(self, analysis: AnalysisResult) -> Dict:
        return {
            "id": analysis.id,
            "tender_id": analysis.tender_id,
            "pass_gate": analysis.pass_gate,
            "gate_checks": json.loads(analysis.gate_checks) if analysis.gate_checks else [],
            "match_score": analysis.match_score,
            "match_grade": analysis.match_grade,
            "recommendation": analysis.recommendation,
            "decision_action": analysis.decision_action,
            "decision_reason": analysis.decision_reason,
            "decision_confidence": analysis.decision_confidence,
            "risks": json.loads(analysis.risks) if analysis.risks else [],
            "key_findings": json.loads(analysis.key_findings) if analysis.key_findings else [],
            "created_at": analysis.created_at.strftime("%Y-%m-%d %H:%M:%S") if analysis.created_at else None,
        }


class CompanyRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_profile(self) -> Optional[CompanyProfile]:
        statement = select(CompanyProfile).where(CompanyProfile.is_active == True).limit(1)
        return self.session.exec(statement).first()

    def get_profile_dict(self) -> Dict:
        profile = self.get_active_profile()
        if not profile:
            return self._default_profile()
        return {
            "name": profile.name,
            "target_domains": json.loads(profile.target_domains) if profile.target_domains else [],
            "budget_range": [profile.budget_range_min or 50, profile.budget_range_max or 1000],
            "qualifications": json.loads(profile.qualifications) if profile.qualifications else [],
            "service_regions": json.loads(profile.service_regions) if profile.service_regions else [],
            "bid_history": json.loads(profile.bid_history) if profile.bid_history else [],
        }

    def save_profile(self, profile_data: Dict) -> CompanyProfile:
        profile = self.get_active_profile()
        if not profile:
            profile = CompanyProfile()
        
        profile.name = profile_data.get("name", "默认公司")
        profile.target_domains = json.dumps(profile_data.get("target_domains", []), ensure_ascii=False)
        profile.budget_range_min = profile_data.get("budget_range", [50, 1000])[0]
        profile.budget_range_max = profile_data.get("budget_range", [50, 1000])[1]
        profile.qualifications = json.dumps(profile_data.get("qualifications", []), ensure_ascii=False)
        profile.service_regions = json.dumps(profile_data.get("service_regions", []), ensure_ascii=False)
        profile.bid_history = json.dumps(profile_data.get("bid_history", []), ensure_ascii=False)
        profile.updated_at = datetime.utcnow()
        
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def _default_profile(self) -> Dict:
        return {
            "name": "默认公司",
            "target_domains": ["软件开发", "大数据", "AI/人工智能"],
            "budget_range": [50, 1000],
            "qualifications": ["CMMI3", "ISO27001", "高新技术企业"],
            "service_regions": ["广东省", "北京市", "上海市"],
            "bid_history": [],
        }


def get_repository():
    from app.db.session import get_session
    session = next(get_session())
    return TenderRepository(session)


def get_company_repository():
    from app.db.session import get_session
    session = next(get_session())
    return CompanyRepository(session)
