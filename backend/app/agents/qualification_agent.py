from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult


class QualificationAgent(BaseAgent):
    """资质分析 Agent
    
    分析招标项目的资质要求与公司资质的匹配情况
    """
    
    @property
    def name(self) -> str:
        return "资质分析"
    
    @property
    def description(self) -> str:
        return "分析招标项目的资质要求与公司资质的匹配情况"
    
    def analyze(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> AgentResult:
        required_quals = self._get_required_qualifications(tender_info)
        required_quals = [str(qual).strip() for qual in required_quals if qual and str(qual).strip()]
        company_quals = set(company_profile.get('qualifications', []))
        company_quals.update(
            asset.get("name", "")
            for asset in company_profile.get("assets", [])
            if asset.get("asset_type") == "qualification" and asset.get("status") == "有效" and not asset.get("is_deleted")
        )
        company_quals = {str(qual).strip() for qual in company_quals if qual and str(qual).strip()}
        
        matched = []
        missing = []
        partial_matched = []
        
        for req_qual in required_quals:
            status = self._check_qualification(req_qual, company_quals)
            if status == 'matched':
                matched.append(req_qual)
            elif status == 'partial':
                partial_matched.append(req_qual)
            else:
                missing.append(req_qual)
        
        key_findings = []
        risks = []
        recommendations = []
        
        if matched:
            key_findings.append(f"已具备资质: {', '.join(matched)}")
        
        if partial_matched:
            key_findings.append(f"部分匹配资质: {', '.join(partial_matched)}")
            recommendations.append("建议核实部分匹配资质是否满足要求")
        
        if missing:
            key_findings.append(f"缺少资质: {', '.join(missing)}")
            risks.append(f"缺少{len(missing)}项必要资质")
            recommendations.append(f"建议评估获取以下资质的可行性: {', '.join(missing)}")
        
        confidence = self._calculate_confidence(len(matched), len(partial_matched), len(required_quals))
        
        return AgentResult(
            agent_name=self.name,
            analysis={
                'required_qualifications': required_quals,
                'company_qualifications': list(company_quals),
                'matched': matched,
                'partial_matched': partial_matched,
                'missing': missing,
                'pass': len(missing) == 0
            },
            confidence=confidence,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks
        )
    
    def _get_required_qualifications(self, tender_info: Dict[str, Any]) -> List[str]:
        """获取资质要求列表"""
        quals = tender_info.get('qualifications', [])
        
        if hasattr(tender_info, 'qualifications'):
            qual_obj = tender_info.qualifications
            if hasattr(qual_obj, 'required'):
                quals = qual_obj.required
            elif isinstance(qual_obj, dict):
                quals = qual_obj.get('required', [])
        
        return quals if isinstance(quals, list) else []
    
    def _check_qualification(self, required: str, owned: set) -> str:
        """检查资质匹配状态"""
        required_lower = required.lower()
        
        for qual in owned:
            qual_lower = qual.lower()
            if required_lower == qual_lower:
                return 'matched'
            if required_lower in qual_lower or qual_lower in required_lower:
                return 'matched'
        
        aliases = {
            '等保三级': ['信息安全等级保护三级', '三级等保'],
            'CMMI3': ['CMMI三级', 'CMMI-ML3', 'CMMI L3'],
            'ISO27001': ['ISO/IEC 27001', '信息安全管理体系认证'],
            'ISO9001': ['ISO 9001', '质量管理体系认证'],
        }
        
        for standard, alias_list in aliases.items():
            all_names = [standard] + alias_list
            required_in_group = any(n.lower() in required_lower for n in all_names)
            
            if required_in_group:
                for qual in owned:
                    if any(n.lower() in qual.lower() for n in all_names):
                        return 'matched'
        
        return 'missing'
    
    def _calculate_confidence(self, matched: int, partial: int, total: int) -> float:
        """计算置信度"""
        if total == 0:
            return 1.0
        
        score = (matched + partial * 0.5) / total
        return round(score, 2)
