import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class RoughExtractor:
    """粗抽阶段 - Recall优先，允许脏数据"""
    
    def __init__(self):
        self.keywords_map = {
            "大数据": ["大数据", "数据清洗", "Hadoop", "Spark", "数据仓库", "数据治理"],
            "AI/人工智能": ["AI", "人工智能", "机器学习", "NLP", "图像识别", "大模型", "深度学习"],
            "软件开发": ["软件开发", "系统建设", "APP", "小程序", "平台开发", "信息化建设"],
            "硬件/设备": ["服务器", "电脑", "硬件", "存储", "网络设备", "机房建设"],
            "工程/施工": ["装修", "施工", "改造", "土建", "安装工程", "机电工程"],
            "通信/网络": ["通信", "基站", "光缆", "宽带", "5G", "网络优化", "传输网"],
            "运维/服务": ["运维", "维护", "驻场", "巡检", "技术支持", "运营服务"],
            "安全/等保": ["等保", "安全", "网络安全", "信息安全", "数据安全"],
        }
        
        self.qualification_patterns = [
            r'资质要求[：:]\s*(.+?)(?=\n|。|$)',
            r'投标人须具备[：:]\s*(.+?)(?=\n|。|$)',
            r'具有(.+?)资质',
            r'持有(.+?)证书',
            r'具备(.+?)认证',
            r'资质条件[：:]\s*(.+?)(?=\n|。|$)',
        ]
        
        self.region_patterns = [
            r'项目地点[：:]\s*(.+?)(?=\n|。|$)',
            r'实施地点[：:]\s*(.+?)(?=\n|。|$)',
            r'项目所在地[：:]\s*(.+?)(?=\n|。|$)',
            r'采购人地址[：:]\s*(.+?)(?=\n|。|$)',
        ]
    
    def extract(self, content: str, attachments: List[str] = None) -> Dict[str, Any]:
        """执行粗抽"""
        if not content:
            content = ""
        
        results = {
            'budget': self._extract_budget(content),
            'deadline': self._extract_deadline(content),
            'qualifications': self._extract_qualifications(content),
            'contact': self._extract_contact(content),
            'tags': self._extract_keywords(content),
            'region': self._extract_region(content),
            'project_type': self._extract_project_type(content),
        }
        
        if attachments:
            for attachment in attachments:
                attachment_info = self._extract_from_attachment(attachment)
                results = self._merge_results(results, attachment_info)
        
        return results
    
    def _extract_budget(self, content: str) -> List[Dict[str, Any]]:
        """提取预算 - 返回所有可能的值"""
        budgets = []
        
        patterns_wan = [
            r'(\d+(?:\.\d+)?)\s*万元',
            r'(\d+(?:\.\d+)?)\s*万',
            r'预算[：:]\s*(\d+(?:\.\d+)?)\s*万',
            r'采购预算[：:]\s*(\d+(?:\.\d+)?)\s*万',
            r'项目金额[：:]\s*(\d+(?:\.\d+)?)\s*万',
        ]
        
        for pattern in patterns_wan:
            for match in re.finditer(pattern, content):
                value = float(match.group(1))
                budgets.append({
                    'value': value,
                    'unit': '万元',
                    'source': '正文',
                    'context': match.group(0)
                })
        
        patterns_yuan = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*元(?!(?:万|亿))',
            r'人民币[：:]?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*元',
        ]
        
        for pattern in patterns_yuan:
            for match in re.finditer(pattern, content):
                value_str = match.group(1).replace(',', '')
                value = float(value_str) / 10000.0
                budgets.append({
                    'value': round(value, 2),
                    'unit': '万元',
                    'source': '正文',
                    'context': match.group(0)
                })
        
        patterns_yi = [
            r'(\d+(?:\.\d+)?)\s*亿元',
            r'(\d+(?:\.\d+)?)\s*亿',
        ]
        
        for pattern in patterns_yi:
            for match in re.finditer(pattern, content):
                value = float(match.group(1)) * 10000
                budgets.append({
                    'value': value,
                    'unit': '万元',
                    'source': '正文',
                    'context': match.group(0)
                })
        
        return budgets
    
    def _extract_deadline(self, content: str) -> List[Dict[str, Any]]:
        """提取截止日期"""
        deadlines = []
        
        patterns = [
            (r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日号]?\s*(\d{1,2})[时:：](\d{1,2})', 'datetime'),
            (r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日号]?', 'date'),
            (r'截止时间[：:]\s*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', 'date'),
            (r'投标截止[：:]\s*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', 'date'),
            (r'开标时间[：:]\s*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', 'date'),
        ]
        
        for pattern, dtype in patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                try:
                    if dtype == 'datetime' and len(groups) >= 5:
                        dt = datetime(
                            int(groups[0]), int(groups[1]), int(groups[2]),
                            int(groups[3]), int(groups[4])
                        )
                    elif dtype == 'date' and len(groups) >= 3:
                        dt = datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                    else:
                        continue
                    
                    deadlines.append({
                        'value': dt,
                        'raw_text': match.group(0),
                        'source': '正文'
                    })
                except ValueError:
                    continue
        
        return deadlines
    
    def _extract_qualifications(self, content: str) -> Dict[str, Any]:
        """提取资质要求"""
        required = []
        optional = []
        
        for pattern in self.qualification_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                qual_text = match.group(1) if match.lastindex else match.group(0)
                qual_text = qual_text.strip()
                
                if qual_text and len(qual_text) > 2:
                    if '或' in qual_text or '及' in qual_text:
                        parts = re.split(r'[或及，,；;]', qual_text)
                        for part in parts:
                            part = part.strip()
                            if part and len(part) > 2:
                                required.append(part)
                    else:
                        required.append(qual_text)
        
        required = list(set(required))
        
        return {
            'required': required,
            'optional': optional,
            'raw_text': content
        }
    
    def _extract_contact(self, content: str) -> Dict[str, Any]:
        """提取联系人信息"""
        contact = {
            'person': '',
            'phone': '',
            'email': '',
        }
        
        person_patterns = [
            r'联系人[：:]\s*(.+?)(?=\n|。|电话|$)',
            r'联系人员[：:]\s*(.+?)(?=\n|。|电话|$)',
            r'项目负责人[：:]\s*(.+?)(?=\n|。|电话|$)',
        ]
        
        for pattern in person_patterns:
            match = re.search(pattern, content)
            if match:
                contact['person'] = match.group(1).strip()
                break
        
        phone_patterns = [
            r'(?:电话|联系电话|手机)[：:]\s*(\d{3,4}[-\s]?\d{7,8}|\d{11})',
            r'(?:电话|联系电话|手机)[：:]\s*(1[3-9]\d{9})',
            r'(\d{3,4}[-\s]?\d{7,8})',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, content)
            if match:
                contact['phone'] = match.group(1).strip()
                break
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, content)
        if match:
            contact['email'] = match.group(0)
        
        return contact
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词标签"""
        tags = set()
        
        for category, keywords in self.keywords_map.items():
            for kw in keywords:
                if kw.lower() in content.lower():
                    tags.add(category)
                    break
        
        return list(tags)
    
    def _extract_region(self, content: str) -> str:
        """提取项目地区"""
        for pattern in self.region_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        province_patterns = [
            r'([\u4e00-\u9fa5]{2,4}省)',
            r'([\u4e00-\u9fa5]{2,4}市)',
            r'([\u4e00-\u9fa5]{2,4}自治区)',
        ]
        
        for pattern in province_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_project_type(self, content: str) -> str:
        """提取项目类型"""
        type_patterns = [
            (r'招标公告', '招标'),
            (r'询比公告', '询比'),
            (r'竞争性谈判', '竞争性谈判'),
            (r'单一来源', '单一来源'),
            (r'竞争性磋商', '竞争性磋商'),
            (r'采购公告', '采购'),
        ]
        
        for pattern, ptype in type_patterns:
            if re.search(pattern, content):
                return ptype
        
        return ""
    
    def _extract_from_attachment(self, attachment_path: str) -> Dict[str, Any]:
        """从附件中提取信息"""
        results = {
            'budget': [],
            'deadline': [],
            'qualifications': {'required': [], 'optional': []},
            'contact': {'person': '', 'phone': '', 'email': ''},
        }
        
        return results
    
    def _merge_results(self, main: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
        """合并提取结果"""
        merged = main.copy()
        
        if extra.get('budget'):
            merged['budget'].extend(extra['budget'])
        
        if extra.get('deadline'):
            merged['deadline'].extend(extra['deadline'])
        
        if extra.get('qualifications', {}).get('required'):
            merged['qualifications']['required'].extend(extra['qualifications']['required'])
        
        if extra.get('contact', {}).get('person') and not merged['contact']['person']:
            merged['contact']['person'] = extra['contact']['person']
        if extra.get('contact', {}).get('phone') and not merged['contact']['phone']:
            merged['contact']['phone'] = extra['contact']['phone']
        
        return merged
