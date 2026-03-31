from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from datetime import datetime


class GateResult(Enum):
    """门槛检查结果"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class GateCheck:
    """门槛检查项"""
    name: str
    result: GateResult
    reason: str
    is_mandatory: bool
    detail: str = ""


class GateFilter:
    """硬性过滤层 - Gate
    
    检查必须满足的硬性条件：
    1. 资质门槛 - 必须具备要求的资质
    2. 地域门槛 - 是否在服务区域内
    3. 时间门槛 - 是否在投标有效期内
    """
    
    def __init__(self, company_profile: Dict[str, Any]):
        self.company = company_profile
        self._build_qualification_index()
    
    def _build_qualification_index(self):
        """构建资质索引，支持模糊匹配"""
        company_quals = self.company.get('qualifications', [])
        self.qual_index: Set[str] = set()
        
        for qual in company_quals:
            self.qual_index.add(qual.lower())
            self.qual_index.add(qual.upper())
            self.qual_index.add(qual)
        
        self.qual_aliases = {
            '等保三级': ['信息安全等级保护三级', '等保三级认证', '三级等保'],
            'CMMI3': ['CMMI三级', 'CMMI-ML3', 'CMMI L3'],
            'ISO27001': ['ISO/IEC 27001', '信息安全管理体系认证'],
            'ISO9001': ['ISO 9001', '质量管理体系认证'],
            '高新技术企业': ['高新企业', '国家高新技术企业'],
        }
    
    def check(self, tender_info: Dict[str, Any]) -> List[GateCheck]:
        """执行所有门槛检查
        
        Args:
            tender_info: 招标信息，包含资质要求、地区、截止日期等
        
        Returns:
            检查结果列表
        """
        checks = []
        
        checks.extend(self._check_qualifications(tender_info))
        
        checks.append(self._check_region(tender_info))
        
        checks.append(self._check_deadline(tender_info))
        
        checks.append(self._check_budget_range(tender_info))
        
        return checks
    
    def _check_qualifications(self, tender_info: Dict[str, Any]) -> List[GateCheck]:
        """检查资质门槛"""
        checks = []
        
        required_quals = tender_info.get('qualifications', [])
        if not required_quals:
            if hasattr(tender_info, 'qualifications'):
                required_quals = tender_info.qualifications.required if hasattr(tender_info.qualifications, 'required') else []
            elif isinstance(tender_info, dict):
                qual_info = tender_info.get('qualifications')
                if qual_info:
                    if hasattr(qual_info, 'required'):
                        required_quals = qual_info.required
                    elif isinstance(qual_info, dict):
                        required_quals = qual_info.get('required', [])
        
        if not required_quals:
            return [GateCheck(
                name="资质要求",
                result=GateResult.PASS,
                reason="无特殊资质要求",
                is_mandatory=False
            )]
        
        for req_qual in required_quals:
            has_qual = self._has_qualification(req_qual)
            
            checks.append(GateCheck(
                name=f"资质: {req_qual}",
                result=GateResult.PASS if has_qual else GateResult.FAIL,
                reason="已具备" if has_qual else "缺少此资质",
                is_mandatory=True,
                detail=req_qual
            ))
        
        return checks
    
    def _has_qualification(self, required_qual: str) -> bool:
        """检查是否具备某资质"""
        required_lower = required_qual.lower()
        required_upper = required_qual.upper()
        
        if required_qual in self.qual_index:
            return True
        if required_lower in self.qual_index:
            return True
        if required_upper in self.qual_index:
            return True
        
        for standard, aliases in self.qual_aliases.items():
            if standard in self.qual_index or standard.lower() in self.qual_index:
                if required_qual == standard:
                    return True
                if required_qual in aliases:
                    return True
                for alias in aliases:
                    if required_qual in alias or alias in required_qual:
                        return True
        
        company_quals = self.company.get('qualifications', [])
        for qual in company_quals:
            if required_qual in qual or qual in required_qual:
                return True
        
        return False
    
    def _check_region(self, tender_info: Dict[str, Any]) -> GateCheck:
        """检查地域门槛"""
        tender_region = tender_info.get('region', '')
        
        if hasattr(tender_info, 'region'):
            tender_region = tender_info.region
        
        if not tender_region:
            return GateCheck(
                name="地域要求",
                result=GateResult.PASS,
                reason="无地域限制",
                is_mandatory=False
            )
        
        company_regions = self.company.get('service_regions', [])
        
        if not company_regions:
            return GateCheck(
                name="地域要求",
                result=GateResult.WARNING,
                reason=f"未配置服务区域，项目地区: {tender_region}",
                is_mandatory=False
            )
        
        for region in company_regions:
            if region in tender_region or tender_region in region:
                return GateCheck(
                    name="地域要求",
                    result=GateResult.PASS,
                    reason=f"符合服务区域: {region}",
                    is_mandatory=False
                )
        
        return GateCheck(
            name="地域要求",
            result=GateResult.WARNING,
            reason=f"不在服务区域: {tender_region}",
            is_mandatory=False
        )
    
    def _check_deadline(self, tender_info: Dict[str, Any]) -> GateCheck:
        """检查时间门槛"""
        deadline = tender_info.get('deadline')
        
        if hasattr(tender_info, 'deadline'):
            deadline = tender_info.deadline
            if hasattr(deadline, 'value'):
                deadline = deadline.value
        
        if not deadline:
            return GateCheck(
                name="投标截止时间",
                result=GateResult.WARNING,
                reason="无法获取截止时间",
                is_mandatory=False
            )
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.strptime(deadline, '%Y-%m-%d')
            except ValueError:
                return GateCheck(
                    name="投标截止时间",
                    result=GateResult.WARNING,
                    reason=f"截止时间格式异常: {deadline}",
                    is_mandatory=False
                )
        
        now = datetime.now()
        
        if deadline > now:
            days_left = (deadline - now).days
            return GateCheck(
                name="投标截止时间",
                result=GateResult.PASS,
                reason=f"仍在有效期内，剩余{days_left}天",
                is_mandatory=True,
                detail=f"截止日期: {deadline.strftime('%Y-%m-%d')}"
            )
        
        return GateCheck(
            name="投标截止时间",
            result=GateResult.FAIL,
            reason=f"已过截止时间: {deadline.strftime('%Y-%m-%d')}",
            is_mandatory=True
        )
    
    def _check_budget_range(self, tender_info: Dict[str, Any]) -> GateCheck:
        """检查预算范围"""
        budget = tender_info.get('budget')
        
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        
        if not budget:
            return GateCheck(
                name="预算范围",
                result=GateResult.WARNING,
                reason="无法获取预算信息",
                is_mandatory=False
            )
        
        budget_range = self.company.get('budget_range', [0, float('inf')])
        min_budget, max_budget = budget_range[0], budget_range[1]
        
        if min_budget <= budget <= max_budget:
            return GateCheck(
                name="预算范围",
                result=GateResult.PASS,
                reason=f"预算符合范围: {budget}万元",
                is_mandatory=False
            )
        elif budget > max_budget:
            return GateCheck(
                name="预算范围",
                result=GateResult.WARNING,
                reason=f"预算超标: {budget}万元 (上限{max_budget}万元)",
                is_mandatory=False
            )
        else:
            return GateCheck(
                name="预算范围",
                result=GateResult.WARNING,
                reason=f"预算偏低: {budget}万元 (下限{min_budget}万元)",
                is_mandatory=False
            )
    
    def pass_gate(self, checks: List[GateCheck]) -> bool:
        """判断是否通过硬性门槛
        
        Args:
            checks: 检查结果列表
        
        Returns:
            True 如果所有强制性检查都通过
        """
        for check in checks:
            if check.is_mandatory and check.result == GateResult.FAIL:
                return False
        return True
    
    def get_failed_checks(self, checks: List[GateCheck]) -> List[GateCheck]:
        """获取未通过的检查项"""
        return [c for c in checks if c.result == GateResult.FAIL]
    
    def get_warnings(self, checks: List[GateCheck]) -> List[GateCheck]:
        """获取警告项"""
        return [c for c in checks if c.result == GateResult.WARNING]
