from sqlmodel import Session, select, func, or_
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from app.models.tender import Tender, CrawlLog
from app.models.analysis import AnalysisResult
from app.models.analysis_trace import AnalysisTrace
from app.models.company import CompanyProfile, CompanyAsset


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
            "matching_details": json.loads(analysis.matching_details) if analysis.matching_details else {},
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
            result = self._default_profile()
            result["asset_summary"] = self.get_asset_summary()
            result["assets"] = self.get_assets(limit=500)
            return result
        result = {
            "name": profile.name,
            "target_domains": json.loads(profile.target_domains) if profile.target_domains else [],
            "budget_range": [profile.budget_range_min or 50, profile.budget_range_max or 1000],
            "qualifications": json.loads(profile.qualifications) if profile.qualifications else [],
            "service_regions": json.loads(profile.service_regions) if profile.service_regions else [],
            "bid_history": json.loads(profile.bid_history) if profile.bid_history else [],
        }
        result["asset_summary"] = self.get_asset_summary()
        result["assets"] = self.get_assets(limit=500)
        return result

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

    def replace_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        existing = self.session.exec(select(CompanyAsset).where(CompanyAsset.is_deleted == False)).all()
        for item in existing:
            self.session.delete(item)

        for item in assets:
            asset = CompanyAsset(
                company_name=item.get("company_name", ""),
                asset_type=item.get("asset_type", ""),
                source_sheet=item.get("source_sheet", ""),
                name=item.get("name", ""),
                category=item.get("category"),
                certificate_no=item.get("certificate_no"),
                issuer=item.get("issuer"),
                issue_date=item.get("issue_date"),
                expiry_date=item.get("expiry_date"),
                status=item.get("status"),
                amount_wanyuan=item.get("amount_wanyuan"),
                keywords=item.get("keywords"),
                data_json=json.dumps(item.get("data", {}), ensure_ascii=False),
                import_batch_id=item.get("import_batch_id"),
                source_type=item.get("source_type", "excel_import"),
                updated_at=datetime.utcnow(),
            )
            self.session.add(asset)
        self.session.commit()
        return self.get_asset_summary()

    def create_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        asset = CompanyAsset()
        self._apply_asset_data(asset, asset_data, default_source_type="manual")
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return self._asset_to_dict(asset)

    def update_asset(self, asset_id: int, asset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        asset = self.session.get(CompanyAsset, asset_id)
        if not asset:
            return None
        self._apply_asset_data(asset, asset_data, default_source_type="manual_edit")
        if asset.source_type == "excel_import":
            asset.source_type = "manual_edit"
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return self._asset_to_dict(asset)

    def soft_delete_asset(self, asset_id: int, reason: str = "") -> Optional[Dict[str, Any]]:
        asset = self.session.get(CompanyAsset, asset_id)
        if not asset:
            return None
        asset.is_deleted = True
        asset.deleted_at = datetime.utcnow()
        asset.deleted_reason = reason or None
        asset.updated_at = datetime.utcnow()
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return self._asset_to_dict(asset)

    def restore_asset(self, asset_id: int) -> Optional[Dict[str, Any]]:
        asset = self.session.get(CompanyAsset, asset_id)
        if not asset:
            return None
        asset.is_deleted = False
        asset.deleted_at = None
        asset.deleted_reason = None
        asset.updated_at = datetime.utcnow()
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return self._asset_to_dict(asset)

    def get_assets(
        self,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        source_sheet: Optional[str] = None,
        keyword: Optional[str] = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        statement = select(CompanyAsset)
        if not include_deleted:
            statement = statement.where(CompanyAsset.is_deleted == False)
        if asset_type:
            statement = statement.where(CompanyAsset.asset_type == asset_type)
        if status:
            statement = statement.where(CompanyAsset.status == status)
        if source_sheet:
            statement = statement.where(CompanyAsset.source_sheet == source_sheet)
        if keyword:
            like_value = f"%{keyword}%"
            statement = statement.where(
                or_(
                    CompanyAsset.name.like(like_value),
                    CompanyAsset.category.like(like_value),
                    CompanyAsset.certificate_no.like(like_value),
                    CompanyAsset.issuer.like(like_value),
                    CompanyAsset.keywords.like(like_value),
                    CompanyAsset.data_json.like(like_value),
                )
            )
        statement = statement.order_by(CompanyAsset.asset_type, CompanyAsset.id).offset(skip).limit(limit)
        return [self._asset_to_dict(item) for item in self.session.exec(statement).all()]

    def count_assets(
        self,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        source_sheet: Optional[str] = None,
        keyword: Optional[str] = None,
        include_deleted: bool = False,
    ) -> int:
        statement = select(func.count(CompanyAsset.id))
        if not include_deleted:
            statement = statement.where(CompanyAsset.is_deleted == False)
        if asset_type:
            statement = statement.where(CompanyAsset.asset_type == asset_type)
        if status:
            statement = statement.where(CompanyAsset.status == status)
        if source_sheet:
            statement = statement.where(CompanyAsset.source_sheet == source_sheet)
        if keyword:
            like_value = f"%{keyword}%"
            statement = statement.where(
                or_(
                    CompanyAsset.name.like(like_value),
                    CompanyAsset.category.like(like_value),
                    CompanyAsset.certificate_no.like(like_value),
                    CompanyAsset.issuer.like(like_value),
                    CompanyAsset.keywords.like(like_value),
                    CompanyAsset.data_json.like(like_value),
                )
            )
        return int(self.session.exec(statement).one() or 0)

    def get_asset_summary(self) -> Dict[str, Any]:
        assets = self.session.exec(select(CompanyAsset).where(CompanyAsset.is_deleted == False)).all()
        by_type: Dict[str, int] = {}
        by_sheet: Dict[str, int] = {}
        expired_count = 0
        expiring_soon_count = 0
        top_qualifications: List[str] = []
        now = datetime.utcnow()
        soon = now + timedelta(days=180)

        for asset in assets:
            by_type[asset.asset_type] = by_type.get(asset.asset_type, 0) + 1
            by_sheet[asset.source_sheet] = by_sheet.get(asset.source_sheet, 0) + 1
            if asset.status == "过期":
                expired_count += 1
            if asset.status == "有效" and asset.expiry_date and asset.expiry_date <= soon:
                expiring_soon_count += 1
            if asset.asset_type == "qualification" and asset.status == "有效" and len(top_qualifications) < 20:
                top_qualifications.append(asset.name)

        return {
            "total_assets": len(assets),
            "by_type": by_type,
            "by_sheet": by_sheet,
            "by_status": self._count_by_status(assets),
            "valid_qualification_count": len([
                a for a in assets if a.asset_type == "qualification" and a.status == "有效"
            ]),
            "expired_count": expired_count,
            "expiring_soon_count": expiring_soon_count,
            "top_qualifications": top_qualifications,
        }

    def _count_by_status(self, assets: List[CompanyAsset]) -> Dict[str, int]:
        result: Dict[str, int] = {}
        for asset in assets:
            key = asset.status or "未知"
            result[key] = result.get(key, 0) + 1
        return result

    def sync_profile_from_assets(self, company_name: str = "") -> CompanyProfile:
        profile = self.get_active_profile()
        current = self.get_profile_dict() if profile else self._default_profile()
        assets = self.get_assets(limit=1000)
        qualification_names = [
            asset["name"] for asset in assets
            if asset["asset_type"] == "qualification" and asset.get("status") == "有效"
        ]
        domains = set(current.get("target_domains") or [])
        for asset in assets:
            for keyword in asset.get("keywords", []):
                if keyword == "安全/信创":
                    domains.add("安全/等保")
                elif keyword in {"AI/人工智能", "大数据", "软件开发", "通信/网络", "运维/服务"}:
                    domains.add(keyword)
        merged = {
            **current,
            "name": company_name or current.get("name") or "默认公司",
            "target_domains": sorted(domains),
            "qualifications": sorted(set(current.get("qualifications", []) + qualification_names)),
        }
        return self.save_profile(merged)

    def _asset_to_dict(self, asset: CompanyAsset) -> Dict[str, Any]:
        return {
            "id": asset.id,
            "company_name": asset.company_name,
            "asset_type": asset.asset_type,
            "source_sheet": asset.source_sheet,
            "name": asset.name,
            "category": asset.category,
            "certificate_no": asset.certificate_no,
            "issuer": asset.issuer,
            "issue_date": asset.issue_date.strftime("%Y-%m-%d") if asset.issue_date else None,
            "expiry_date": asset.expiry_date.strftime("%Y-%m-%d") if asset.expiry_date else None,
            "status": asset.status,
            "amount_wanyuan": asset.amount_wanyuan,
            "keywords": json.loads(asset.keywords) if asset.keywords else [],
            "data": json.loads(asset.data_json) if asset.data_json else {},
            "import_batch_id": asset.import_batch_id,
            "source_type": asset.source_type,
            "is_deleted": asset.is_deleted,
            "deleted_at": asset.deleted_at.strftime("%Y-%m-%d %H:%M:%S") if asset.deleted_at else None,
            "deleted_reason": asset.deleted_reason,
        }

    def _apply_asset_data(self, asset: CompanyAsset, data: Dict[str, Any], default_source_type: str) -> None:
        now = datetime.utcnow()
        asset.company_name = str(data.get("company_name", asset.company_name or "") or "")
        asset.asset_type = str(data.get("asset_type", asset.asset_type or "") or "")
        asset.source_sheet = str(data.get("source_sheet", asset.source_sheet or "手工维护") or "手工维护")
        asset.name = str(data.get("name", asset.name or "") or "")
        asset.category = data.get("category", asset.category)
        asset.certificate_no = data.get("certificate_no", asset.certificate_no)
        asset.issuer = data.get("issuer", asset.issuer)
        asset.issue_date = self._coerce_datetime(data.get("issue_date", asset.issue_date))
        asset.expiry_date = self._coerce_datetime(data.get("expiry_date", asset.expiry_date))
        asset.status = data.get("status", asset.status or "有效")
        asset.amount_wanyuan = self._coerce_float(data.get("amount_wanyuan", asset.amount_wanyuan))
        asset.keywords = self._encode_keywords(data.get("keywords", asset.keywords))
        raw_data = data.get("data", None)
        if raw_data is not None:
            asset.data_json = json.dumps(raw_data if isinstance(raw_data, dict) else {}, ensure_ascii=False)
        elif not asset.data_json:
            asset.data_json = "{}"
        asset.import_batch_id = data.get("import_batch_id", asset.import_batch_id)
        if data.get("source_type"):
            asset.source_type = data["source_type"]
        elif asset.id is None:
            asset.source_type = default_source_type
        elif not asset.source_type:
            asset.source_type = default_source_type
        asset.updated_at = now
        if asset.created_at is None:
            asset.created_at = now

    def _coerce_datetime(self, value) -> Optional[datetime]:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None

    def _coerce_float(self, value) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _encode_keywords(self, value) -> str:
        if value is None:
            return "[]"
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return json.dumps([str(item) for item in parsed], ensure_ascii=False)
            except Exception:
                return json.dumps([item.strip() for item in value.split(",") if item.strip()], ensure_ascii=False)
        if isinstance(value, list):
            return json.dumps([str(item).strip() for item in value if str(item).strip()], ensure_ascii=False)
        return "[]"

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
