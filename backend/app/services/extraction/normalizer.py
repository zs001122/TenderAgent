from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from .models import BudgetInfo, DeadlineInfo, QualificationInfo, ContactInfo


class FieldNormalizer:
    """归一化阶段 - 标准化字段格式"""
    
    SOURCE_PRIORITY = {
        '正文': 3,
        '附件': 2,
        '表格': 1,
    }
    
    QUALIFICATION_ALIASES = {
        'ISO27001': ['ISO27001', 'ISO/IEC 27001', '信息安全管理体系认证', 'ISO 27001认证'],
        'ISO9001': ['ISO9001', 'ISO 9001', '质量管理体系认证', 'ISO 9001认证'],
        'CMMI3': ['CMMI3', 'CMMI三级', 'CMMI-ML3', 'CMMI L3', '能力成熟度模型集成三级'],
        'CMMI5': ['CMMI5', 'CMMI五级', 'CMMI-ML5', 'CMMI L5'],
        '等保三级': ['等保三级', '信息安全等级保护三级', '等保三级认证', '三级等保'],
        '等保二级': ['等保二级', '信息安全等级保护二级', '等保二级认证', '二级等保'],
        '高新技术企业': ['高新技术企业', '高新企业', '国家高新技术企业'],
        'ITSS': ['ITSS', '信息技术服务标准', 'ITSS认证'],
    }
    
    def normalize(self, rough_info: Dict[str, Any]) -> Dict[str, Any]:
        """执行归一化"""
        return {
            'budget': self._normalize_budget(rough_info.get('budget', [])),
            'deadline': self._normalize_deadline(rough_info.get('deadline', [])),
            'qualifications': self._normalize_qualifications(rough_info.get('qualifications', {})),
            'contact': self._normalize_contact(rough_info.get('contact', {})),
            'tags': rough_info.get('tags', []),
            'region': self._normalize_region(rough_info.get('region', '')),
            'project_type': rough_info.get('project_type', ''),
        }
    
    def _normalize_budget(self, budgets: List[Dict[str, Any]]) -> BudgetInfo:
        """预算归一化 - 选择最可能的值"""
        if not budgets:
            return BudgetInfo(value=None, confidence=0.0)
        
        valid_budgets = [b for b in budgets if b.get('value') and b['value'] > 0]
        
        if not valid_budgets:
            return BudgetInfo(value=None, confidence=0.0)
        
        sorted_budgets = sorted(
            valid_budgets,
            key=lambda x: self.SOURCE_PRIORITY.get(x.get('source', ''), 0),
            reverse=True
        )
        
        primary_budget = sorted_budgets[0]
        
        values = [b['value'] for b in valid_budgets]
        if len(values) > 1:
            max_val, min_val = max(values), min(values)
            if max_val > 0 and (max_val - min_val) / max_val < 0.1:
                confidence = 0.9
            else:
                confidence = 0.6
        else:
            confidence = 0.8
        
        return BudgetInfo(
            value=primary_budget['value'],
            unit=primary_budget.get('unit', '万元'),
            confidence=confidence,
            raw_values=valid_budgets,
            source=primary_budget.get('source', '')
        )
    
    def _normalize_deadline(self, deadlines: List[Dict[str, Any]]) -> DeadlineInfo:
        """截止日期归一化"""
        if not deadlines:
            return DeadlineInfo(value=None, confidence=0.0)
        
        valid_deadlines = [d for d in deadlines if d.get('value')]
        
        if not valid_deadlines:
            return DeadlineInfo(value=None, confidence=0.0)
        
        sorted_deadlines = sorted(
            valid_deadlines,
            key=lambda x: self.SOURCE_PRIORITY.get(x.get('source', ''), 0),
            reverse=True
        )
        
        primary = sorted_deadlines[0]
        
        future_deadlines = [d for d in valid_deadlines 
                          if d['value'] > datetime.now()]
        
        if future_deadlines:
            primary = min(future_deadlines, key=lambda x: x['value'])
            confidence = 0.9
        else:
            confidence = 0.5
        
        return DeadlineInfo(
            value=primary['value'],
            raw_text=primary.get('raw_text', ''),
            confidence=confidence
        )
    
    def _normalize_qualifications(self, quals: Dict[str, Any]) -> QualificationInfo:
        """资质归一化 - 标准化资质名称"""
        required_raw = quals.get('required', [])
        optional_raw = quals.get('optional', [])
        
        required_normalized = []
        for qual in required_raw:
            normalized = self._normalize_qualification_name(qual)
            if normalized and normalized not in required_normalized:
                required_normalized.append(normalized)
        
        optional_normalized = []
        for qual in optional_raw:
            normalized = self._normalize_qualification_name(qual)
            if normalized and normalized not in optional_normalized:
                optional_normalized.append(normalized)
        
        confidence = 0.8 if required_normalized else 0.3
        
        return QualificationInfo(
            required=required_normalized,
            optional=optional_normalized,
            confidence=confidence
        )
    
    def _normalize_qualification_name(self, qual: str) -> Optional[str]:
        """标准化单个资质名称"""
        qual = qual.strip()
        
        for standard, aliases in self.QUALIFICATION_ALIASES.items():
            for alias in aliases:
                if alias.lower() in qual.lower() or qual.lower() in alias.lower():
                    return standard
        
        qual = re.sub(r'[，。、；：]', '', qual)
        qual = re.sub(r'\s+', '', qual)
        
        if len(qual) < 2:
            return None
        
        return qual
    
    def _normalize_contact(self, contact: Dict[str, str]) -> ContactInfo:
        """联系人信息归一化"""
        person = contact.get('person', '').strip()
        phone = contact.get('phone', '').strip()
        email = contact.get('email', '').strip()
        
        if phone:
            phone = re.sub(r'[^\d-]', '', phone)
        
        confidence = 0.0
        if person:
            confidence += 0.3
        if phone:
            confidence += 0.4
        if email:
            confidence += 0.3
        
        return ContactInfo(
            person=person,
            phone=phone,
            email=email,
            confidence=confidence
        )
    
    def _normalize_region(self, region: str) -> str:
        """地区归一化"""
        if not region:
            return ""
        
        region = region.strip()
        
        region = re.sub(r'[，。、；：].*$', '', region)
        
        province_map = {
            '北京': '北京市',
            '上海': '上海市',
            '天津': '天津市',
            '重庆': '重庆市',
        }
        
        for short, full in province_map.items():
            if region.startswith(short):
                return full
        
        return region
