from sqlmodel import Session, select, func, or_
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from app.models.tender import Tender, CrawlLog
from app.models.analysis import AnalysisResult
from app.models.analysis_trace import AnalysisTrace
from app.models.company import CompanyProfile


class TenderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_tenders(self, skip: int = 0, limit: int = 20) -> List[Dict]:
        statement = select(Tender).order_by(Tender.publish_date.desc()).offset(skip).limit(limit)
        results = self.session.exec(statement).all()
        tender_ids = [item.id for item in results if item.id is not None]
        latest_analysis_map = self._get_latest_analysis_map(tender_ids)
        items: List[Dict[str, Any]] = []
        for tender in results:
            tender_dict = self._to_dict(tender)
            analysis_dict = latest_analysis_map.get(tender.id) if tender.id else None
            if analysis_dict:
                tender_dict["match_score"] = analysis_dict.get("match_score")
                tender_dict["match_grade"] = analysis_dict.get("match_grade")
                tender_dict["recommendation"] = analysis_dict.get("recommendation")
            else:
                tender_dict["match_score"] = None
                tender_dict["match_grade"] = None
                tender_dict["recommendation"] = None
            items.append(tender_dict)
        return items

    def get_tender_overview(self) -> Dict[str, int]:
        """看板总览（全量统计，不受分页影响）"""
        total = int(self.count_tenders() or 0)
        analyzed_count = int(
            self.session.exec(
                select(func.count(func.distinct(AnalysisResult.tender_id)))
            ).one()
            or 0
        )
        pending_count = max(total - analyzed_count, 0)

        latest_subquery = (
            select(
                AnalysisResult.tender_id.label("tender_id"),
                func.max(AnalysisResult.id).label("latest_id"),
            )
            .group_by(AnalysisResult.tender_id)
            .subquery()
        )
        strong_recommended_count = int(
            self.session.exec(
                select(func.count(AnalysisResult.id))
                .join(latest_subquery, AnalysisResult.id == latest_subquery.c.latest_id)
                .where(AnalysisResult.recommendation == "强烈推荐")
            ).one()
            or 0
        )

        return {
            "total": total,
            "analyzed": analyzed_count,
            "pending": pending_count,
            "strong_recommended": strong_recommended_count,
        }

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

    def save_analysis_trace(self, trace: AnalysisTrace) -> AnalysisTrace:
        self.session.add(trace)
        self.session.commit()
        self.session.refresh(trace)
        return trace

    def get_analysis_by_tender_id(self, tender_id: int) -> Optional[AnalysisResult]:
        statement = (
            select(AnalysisResult)
            .where(AnalysisResult.tender_id == tender_id)
            .order_by(AnalysisResult.created_at.desc())
        )
        return self.session.exec(statement).first()

    def get_analysis_result(self, tender_id: int) -> Optional[Dict]:
        analysis = self.get_analysis_by_tender_id(tender_id)
        return self._analysis_to_dict(analysis) if analysis else None

    def _get_latest_analysis_map(self, tender_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        if not tender_ids:
            return {}
        latest_subquery = (
            select(
                AnalysisResult.tender_id.label("tender_id"),
                func.max(AnalysisResult.id).label("latest_id"),
            )
            .where(AnalysisResult.tender_id.in_(tender_ids))
            .group_by(AnalysisResult.tender_id)
            .subquery()
        )
        latest_analyses = self.session.exec(
            select(AnalysisResult).join(latest_subquery, AnalysisResult.id == latest_subquery.c.latest_id)
        ).all()
        return {
            int(item.tender_id): self._analysis_to_dict(item)
            for item in latest_analyses
            if item.tender_id is not None
        }

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

    def get_crawler_health_stats(self, hours: int = 24) -> Dict[str, Any]:
        """抓取链路健康指标（默认近 24 小时）"""
        since = datetime.utcnow() - timedelta(hours=max(hours, 1))

        recent_logs_stmt = select(CrawlLog).where(CrawlLog.start_time >= since)
        recent_logs = self.session.exec(recent_logs_stmt).all()
        total_runs = len(recent_logs)
        success_runs = sum(1 for item in recent_logs if str(item.status).upper() == "SUCCESS")
        failed_runs = sum(1 for item in recent_logs if str(item.status).upper() == "FAILED")
        total_new_count = sum(int(item.new_count or 0) for item in recent_logs)

        durations = [
            (item.end_time - item.start_time).total_seconds()
            for item in recent_logs
            if item.end_time and item.start_time
        ]
        avg_duration_seconds = round(sum(durations) / len(durations), 2) if durations else 0.0
        success_rate = round((success_runs / total_runs), 4) if total_runs > 0 else 0.0

        pending_analysis_stmt = (
            select(func.count(Tender.id))
            .where(Tender.id.not_in(select(AnalysisResult.tender_id).distinct()))
        )
        pending_analysis_count = self.session.exec(pending_analysis_stmt).one()

        latest_log = self.session.exec(
            select(CrawlLog).order_by(CrawlLog.start_time.desc()).limit(1)
        ).first()

        return {
            "window_hours": max(hours, 1),
            "since": since.isoformat(),
            "runs": {
                "total": total_runs,
                "success": success_runs,
                "failed": failed_runs,
                "success_rate": success_rate,
                "avg_duration_seconds": avg_duration_seconds,
            },
            "ingest": {
                "new_tenders": total_new_count,
            },
            "analysis": {
                "pending_count": int(pending_analysis_count or 0),
            },
            "latest_run": {
                "source_site": latest_log.source_site if latest_log else None,
                "status": latest_log.status if latest_log else None,
                "start_time": latest_log.start_time.isoformat() if latest_log and latest_log.start_time else None,
                "end_time": latest_log.end_time.isoformat() if latest_log and latest_log.end_time else None,
                "new_count": int(latest_log.new_count or 0) if latest_log else 0,
            },
        }

    def get_analysis_mode_stats(self, hours: int = 24) -> Dict[str, Any]:
        """分析执行模式统计（Agent/Fallback 命中率）"""
        since = datetime.utcnow() - timedelta(hours=max(hours, 1))
        traces = self.session.exec(
            select(AnalysisTrace).where(AnalysisTrace.created_at >= since)
        ).all()

        total = len(traces)
        agent_count = sum(1 for t in traces if t.selected_mode == "agent")
        fallback_count = sum(1 for t in traces if t.fallback_used)
        rule_count = sum(1 for t in traces if t.selected_mode == "rule")
        success_count = sum(1 for t in traces if t.success)
        error_total = sum(int(t.error_count or 0) for t in traces)
        avg_duration_ms = round(
            sum(int(t.duration_ms or 0) for t in traces) / total, 2
        ) if total else 0.0

        def _ratio(v: int) -> float:
            return round(v / total, 4) if total else 0.0

        return {
            "window_hours": max(hours, 1),
            "since": since.isoformat(),
            "counts": {
                "total": total,
                "success": success_count,
                "agent": agent_count,
                "rule": rule_count,
                "fallback": fallback_count,
                "error_total": error_total,
            },
            "rates": {
                "success_rate": _ratio(success_count),
                "agent_rate": _ratio(agent_count),
                "fallback_rate": _ratio(fallback_count),
            },
            "performance": {
                "avg_duration_ms": avg_duration_ms,
            },
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
    session_gen = get_session()
    session = next(session_gen)
    try:
        yield TenderRepository(session)
    finally:
        session.close()
        session_gen.close()


def get_company_repository():
    from app.db.session import get_session
    session_gen = get_session()
    session = next(session_gen)
    try:
        yield CompanyRepository(session)
    finally:
        session.close()
        session_gen.close()
