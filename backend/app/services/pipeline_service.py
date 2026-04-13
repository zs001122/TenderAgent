from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlmodel import Session
import json
import time

from app.models.tender import Tender
from app.models.analysis import AnalysisResult
from app.models.analysis_trace import AnalysisTrace
from app.models.company import CompanyProfile
from app.core.config import settings
from app.db.repository import TenderRepository, CompanyRepository
from app.services.extraction.pipeline import InformationFusionPipeline
from app.services.extraction.models import ExtractionResult
from app.services.extraction.agent_extractor import AgentExtractionService
from app.services.matching.matching_engine import MatchingEngine
from app.agents.orchestrator import OrchestratorAgent


class PipelineService:
    """数据流转主服务：抓取 → 提取 → 匹配 → 推荐"""

    def __init__(self, session: Session, company_profile: Dict[str, Any] = None):
        self.session = session
        self.tender_repo = TenderRepository(session)
        self.company_repo = CompanyRepository(session)
        
        if company_profile:
            self.company_profile = company_profile
        else:
            self.company_profile = self.company_repo.get_profile_dict()
        
        self.extraction_pipeline = InformationFusionPipeline()
        self.agent_extractor = AgentExtractionService()
        self.extraction_mode = str(settings.EXTRACTION_MODE or "hybrid").strip().lower()
        self.matching_engine = MatchingEngine(self.company_profile)
        self.orchestrator = OrchestratorAgent()

    def process_tender(self, tender_id: int) -> Optional[AnalysisResult]:
        """处理单个招标：提取 → 匹配 → 推荐"""
        started = time.perf_counter()
        tender = self.tender_repo.get_tender_by_id(tender_id)
        if not tender:
            return None
        
        if not tender.content:
            return self._create_empty_analysis(tender_id, "招标内容为空")
        
        extraction_result, mode_meta = self._extract_with_mode(tender.content, tender.title)
        
        extraction_dict = self._extraction_to_dict(extraction_result.info)
        self.tender_repo.update_extraction_result(tender_id, extraction_dict)
        
        tender_info = self._build_tender_info(tender, extraction_result.info)
        
        match_result = self.matching_engine.match(tender_info)
        
        orchestrator_result = self.orchestrator.analyze(tender_info, self.company_profile)
        
        analysis = self._create_analysis_result(
            tender_id=tender_id,
            match_result=match_result,
            orchestrator_result=orchestrator_result
        )
        
        saved = self.tender_repo.save_analysis_result(analysis)
        duration_ms = int((time.perf_counter() - started) * 1000)
        self.tender_repo.save_analysis_trace(
            AnalysisTrace(
                tender_id=tender_id,
                configured_mode=self.extraction_mode,
                selected_mode=str(mode_meta.get("selected_mode", "rule")),
                fallback_used=bool(mode_meta.get("fallback_used", False)),
                success=bool(extraction_result.success),
                error_count=len(extraction_result.errors or []),
                duration_ms=duration_ms,
                created_at=datetime.utcnow(),
            )
        )
        return saved

    def debug_extraction(self, tender_id: int) -> Optional[Dict[str, Any]]:
        """返回当前招标在配置模式下的抽取调试信息。"""
        tender = self.tender_repo.get_tender_by_id(tender_id)
        if not tender:
            return None
        if not tender.content:
            return {
                "tender_id": tender_id,
                "configured_mode": self.extraction_mode,
                "selected_mode": "none",
                "fallback_used": False,
                "success": False,
                "errors": ["招标内容为空"],
                "warnings": [],
                "extraction": {},
            }

        configured_mode = self.extraction_mode
        selected_mode = "rule"
        fallback_used = False

        if configured_mode == "rule":
            result = self.extraction_pipeline.extract(tender.content)
            selected_mode = "rule"
        elif configured_mode == "agent":
            agent_result = self.agent_extractor.extract(tender.content, title=tender.title)
            if agent_result.success:
                result = agent_result
                selected_mode = "agent"
            else:
                result = self.extraction_pipeline.extract(tender.content)
                selected_mode = "rule_fallback"
                fallback_used = True
                result.warnings.append("agent_extract_failed_fallback_rule")
                result.errors.extend(agent_result.errors)
        else:
            agent_result = self.agent_extractor.extract(tender.content, title=tender.title)
            if agent_result.success:
                result = agent_result
                selected_mode = "agent"
            else:
                result = self.extraction_pipeline.extract(tender.content)
                selected_mode = "rule_fallback"
                fallback_used = True
                result.warnings.append("agent_extract_failed_fallback_rule")
                result.errors.extend(agent_result.errors)

        return {
            "tender_id": tender_id,
            "configured_mode": configured_mode,
            "selected_mode": selected_mode,
            "fallback_used": fallback_used,
            "success": result.success,
            "errors": result.errors,
            "warnings": result.warnings,
            "extraction": self._extraction_to_dict(result.info),
        }

    def _extract_with_mode(self, content: str, title: str) -> tuple[ExtractionResult, Dict[str, Any]]:
        mode = self.extraction_mode
        if mode == "rule":
            return self.extraction_pipeline.extract(content), {
                "selected_mode": "rule",
                "fallback_used": False,
            }

        if mode == "agent":
            agent_result = self.agent_extractor.extract(content, title=title)
            if agent_result.success:
                return agent_result, {
                    "selected_mode": "agent",
                    "fallback_used": False,
                }
            # agent-only 模式失败时兜底，避免主流程中断
            fallback = self.extraction_pipeline.extract(content)
            fallback.warnings.append("agent_extract_failed_fallback_rule")
            fallback.errors.extend(agent_result.errors or [])
            return fallback, {
                "selected_mode": "rule_fallback",
                "fallback_used": True,
            }

        # hybrid: 优先 Agent，失败回退 Rule
        agent_result = self.agent_extractor.extract(content, title=title)
        if agent_result.success:
            return agent_result, {
                "selected_mode": "agent",
                "fallback_used": False,
            }
        fallback = self.extraction_pipeline.extract(content)
        fallback.warnings.append("agent_extract_failed_fallback_rule")
        fallback.errors.extend(agent_result.errors or [])
        return fallback, {
            "selected_mode": "rule_fallback",
            "fallback_used": True,
        }

    def process_batch(self, tender_ids: List[int]) -> List[AnalysisResult]:
        """批量处理招标"""
        results = []
        for tender_id in tender_ids:
            try:
                result = self.process_tender(tender_id)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"处理招标 {tender_id} 失败: {e}")
        return results

    def process_batch_detailed(self, tender_ids: List[int]) -> Dict[str, Any]:
        """批量处理招标（返回成功/失败明细）"""
        success_ids: List[int] = []
        failed_items: List[Dict[str, Any]] = []

        for tender_id in tender_ids:
            try:
                result = self.process_tender(tender_id)
                if result:
                    success_ids.append(tender_id)
                    continue
                failed_items.append({"tender_id": tender_id, "reason": "招标不存在或分析失败"})
            except Exception as exc:
                failed_items.append({"tender_id": tender_id, "reason": str(exc)})

        return {
            "total": len(tender_ids),
            "success": len(success_ids),
            "failed": len(failed_items),
            "success_ids": success_ids,
            "failed_items": failed_items,
        }

    def process_unanalyzed(self, limit: int = 100) -> Dict[str, Any]:
        """处理未分析的招标"""
        tenders = self.tender_repo.get_tenders_without_analysis(limit)
        tender_ids = [t.id for t in tenders]
        
        results = self.process_batch(tender_ids)
        
        return {
            "total": len(tenders),
            "processed": len(results),
            "tender_ids": tender_ids,
        }

    def get_full_analysis(self, tender_id: int) -> Optional[Dict]:
        """获取完整的分析结果（包含招标信息）"""
        tender_dict = self.tender_repo.get_tender_dict_by_id(tender_id)
        if not tender_dict:
            return None
        
        analysis_dict = self.tender_repo.get_analysis_result(tender_id)
        
        return {
            "tender_id": tender_id,
            "title": tender_dict.get("title"),
            "source_url": tender_dict.get("source_url"),
            "publish_date": tender_dict.get("publish_date"),
            "extraction": {
                "budget": {
                    "value": tender_dict.get("budget_amount"),
                    "confidence": tender_dict.get("budget_confidence"),
                },
                "deadline": tender_dict.get("deadline"),
                "qualifications": tender_dict.get("qualifications", []),
                "tags": tender_dict.get("tags", []),
                "region": tender_dict.get("region"),
                "contact": {
                    "person": tender_dict.get("contact_person"),
                    "phone": tender_dict.get("contact_phone"),
                    "email": tender_dict.get("contact_email"),
                },
            },
            "matching": {
                "pass_gate": analysis_dict.get("pass_gate", False) if analysis_dict else False,
                "score": analysis_dict.get("match_score", 0) if analysis_dict else 0,
                "grade": analysis_dict.get("match_grade", "D") if analysis_dict else "D",
                "recommendation": analysis_dict.get("recommendation", "") if analysis_dict else "",
                "gate_checks": analysis_dict.get("gate_checks", []) if analysis_dict else [],
            },
            "decision": {
                "action": analysis_dict.get("decision_action", "评估后决定") if analysis_dict else "评估后决定",
                "confidence": analysis_dict.get("decision_confidence", 0) if analysis_dict else 0,
                "reason": analysis_dict.get("decision_reason", "") if analysis_dict else "",
                "risks": analysis_dict.get("risks", []) if analysis_dict else [],
            } if analysis_dict else None,
        }

    def _extraction_to_dict(self, info) -> Dict:
        """将 ExtractedInfo 转换为字典"""
        result = {}
        
        if hasattr(info, 'budget') and info.budget:
            result['budget'] = {
                'value': info.budget.value,
                'confidence': getattr(info.budget, 'confidence', 0.9),
            }
        
        if hasattr(info, 'deadline') and info.deadline:
            result['deadline'] = {
                'value': info.deadline.value,
            }
        
        if hasattr(info, 'qualifications') and info.qualifications:
            result['qualifications'] = {
                'required': info.qualifications.required or [],
            }
        
        if hasattr(info, 'contact') and info.contact:
            result['contact'] = {
                'person': getattr(info.contact, 'person', None),
                'phone': getattr(info.contact, 'phone', None),
                'email': getattr(info.contact, 'email', None),
            }
        
        if hasattr(info, 'tags'):
            result['tags'] = info.tags or []
        
        if hasattr(info, 'region'):
            result['region'] = info.region
        
        if hasattr(info, 'project_type'):
            result['project_type'] = info.project_type
        
        return result

    def _build_tender_info(self, tender: Tender, extracted_info) -> Dict:
        """构建匹配引擎需要的招标信息"""
        tender_info = {
            'title': tender.title,
            'budget': extracted_info.budget.value if extracted_info.budget else None,
            'deadline': extracted_info.deadline.value.strftime('%Y-%m-%d') if extracted_info.deadline and extracted_info.deadline.value else None,
            'region': extracted_info.region or tender.region,
            'qualifications': extracted_info.qualifications.required if extracted_info.qualifications else [],
            'tags': extracted_info.tags or [],
            'content': tender.content,
        }
        return tender_info

    def _create_analysis_result(
        self, 
        tender_id: int, 
        match_result, 
        orchestrator_result
    ) -> AnalysisResult:
        """创建分析结果记录"""
        analysis = AnalysisResult(
            tender_id=tender_id,
            pass_gate=match_result.pass_gate,
            gate_checks=json.dumps(match_result.gate_checks, ensure_ascii=False) if match_result.gate_checks else None,
            match_score=match_result.score,
            match_grade=match_result.grade,
            recommendation=match_result.recommendation,
            decision_action=orchestrator_result.decision.action if orchestrator_result else "评估后决定",
            decision_reason=orchestrator_result.decision.reason if orchestrator_result else None,
            decision_confidence=orchestrator_result.decision.confidence if orchestrator_result else 0.0,
            risks=json.dumps(orchestrator_result.decision.risks, ensure_ascii=False) if orchestrator_result and orchestrator_result.decision.risks else None,
            key_findings=json.dumps(orchestrator_result.key_findings, ensure_ascii=False) if orchestrator_result and hasattr(orchestrator_result, 'key_findings') else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return analysis

    def _create_empty_analysis(self, tender_id: int, reason: str) -> AnalysisResult:
        """创建空的分析结果"""
        return AnalysisResult(
            tender_id=tender_id,
            pass_gate=False,
            match_score=0,
            match_grade="D",
            recommendation="不推荐",
            decision_action="不投标",
            decision_reason=reason,
            decision_confidence=1.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


def get_pipeline_service(session: Session = None, company_profile: Dict = None) -> PipelineService:
    """获取 PipelineService 实例"""
    if session is None:
        from app.db.session import get_session
        session = next(get_session())
    return PipelineService(session, company_profile)
