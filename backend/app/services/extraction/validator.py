from typing import Dict, Any, List
from datetime import datetime

from .models import ExtractedInfo, ExtractionResult


class ConsistencyValidator:
    """交叉验证阶段 - 检查数据一致性"""
    
    def validate(self, normalized_info: Dict[str, Any]) -> ExtractionResult:
        """执行交叉验证"""
        issues = []
        warnings = []
        
        budget_issues = self._validate_budget(normalized_info.get('budget'))
        issues.extend(budget_issues)
        
        deadline_issues = self._validate_deadline(normalized_info.get('deadline'))
        issues.extend(deadline_issues)
        
        qual_issues = self._validate_qualifications(normalized_info.get('qualifications'))
        issues.extend(qual_issues)
        
        contact_warnings = self._validate_contact(normalized_info.get('contact'))
        warnings.extend(contact_warnings)
        
        is_reliable = len(issues) == 0
        
        extracted_info = ExtractedInfo(
            budget=normalized_info.get('budget'),
            deadline=normalized_info.get('deadline'),
            qualifications=normalized_info.get('qualifications'),
            contact=normalized_info.get('contact'),
            tags=normalized_info.get('tags', []),
            region=normalized_info.get('region', ''),
            project_type=normalized_info.get('project_type', ''),
            validation_issues=issues,
            is_reliable=is_reliable
        )
        
        return ExtractionResult(
            success=True,
            info=extracted_info,
            errors=issues,
            warnings=warnings
        )
    
    def _validate_budget(self, budget_info) -> List[str]:
        """验证预算一致性"""
        issues = []
        
        if not budget_info:
            issues.append("未能提取预算信息")
            return issues
        
        if not budget_info.value or budget_info.value <= 0:
            issues.append("预算金额无效或为零")
            return issues
        
        raw_values = budget_info.raw_values if hasattr(budget_info, 'raw_values') else []
        
        if len(raw_values) > 1:
            values = [v['value'] for v in raw_values if v.get('value')]
            if values:
                max_val, min_val = max(values), min(values)
                if max_val > 0:
                    diff_ratio = (max_val - min_val) / max_val
                    if diff_ratio > 0.2:
                        issues.append(
                            f"预算在不同来源差异较大: {min_val:.2f}万 - {max_val:.2f}万 "
                            f"(差异{diff_ratio*100:.1f}%)"
                        )
        
        if budget_info.value > 100000:
            issues.append(f"预算金额异常大: {budget_info.value:.2f}万元，请人工核实")
        
        return issues
    
    def _validate_deadline(self, deadline_info) -> List[str]:
        """验证截止日期一致性"""
        issues = []
        
        if not deadline_info:
            issues.append("未能提取截止日期")
            return issues
        
        if not deadline_info.value:
            issues.append("截止日期格式无法解析")
            return issues
        
        if deadline_info.value < datetime.now():
            issues.append(f"截止日期已过: {deadline_info.value.strftime('%Y-%m-%d')}")
        
        return issues
    
    def _validate_qualifications(self, qual_info) -> List[str]:
        """验证资质要求"""
        issues = []
        
        if not qual_info:
            return issues
        
        required = qual_info.required if hasattr(qual_info, 'required') else []
        
        if not required:
            return issues
        
        for qual in required:
            if len(qual) < 2:
                issues.append(f"资质要求描述不清晰: '{qual}'")
        
        return issues
    
    def _validate_contact(self, contact_info) -> List[str]:
        """验证联系人信息"""
        warnings = []
        
        if not contact_info:
            warnings.append("未提取到联系人信息")
            return warnings
        
        if not contact_info.person and not contact_info.phone:
            warnings.append("联系人和联系电话均未找到")
        
        if contact_info.phone:
            phone = contact_info.phone
            if len(phone) < 7:
                warnings.append(f"电话号码长度异常: {phone}")
        
        return warnings
    
    def cross_validate_sources(
        self, 
        main_content_info: Dict[str, Any], 
        attachment_info: Dict[str, Any]
    ) -> List[str]:
        """正文与附件交叉验证"""
        issues = []
        
        main_budget = main_content_info.get('budget', {})
        attach_budget = attachment_info.get('budget', {})
        
        if main_budget and attach_budget:
            main_val = main_budget.get('value')
            attach_val = attach_budget.get('value')
            
            if main_val and attach_val and main_val != attach_val:
                diff = abs(main_val - attach_val) / max(main_val, attach_val)
                if diff > 0.1:
                    issues.append(
                        f"正文预算({main_val}万)与附件预算({attach_val}万)不一致"
                    )
        
        return issues
