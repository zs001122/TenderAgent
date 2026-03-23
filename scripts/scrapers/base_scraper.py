from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional
from datetime import datetime

class BaseScraper(ABC):
    """
    所有招标爬虫的抽象基类。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """爬虫的名称 (例如：'中国电信', '中国移动')"""
        pass

    @abstractmethod
    def run(self, max_pages: int = 3, last_publish_date: Optional[datetime] = None) -> Iterator[Dict[str, Any]]:
        """
        爬虫的主入口。
        应该 yield 表示招标数据的字典，与数据库模式匹配。
        
        Args:
            max_pages: 要抓取的最大页数。
            last_publish_date: 如果提供，爬虫在遇到较旧的招标公告时应停止抓取。
            
        Yields:
            包含招标数据的字典:
            {
                "source_url": str,
                "source_site": str, # 通常是 self.name
                "title": str,
                "publish_date": datetime,
                "notice_type": str (可选),
                "content": str (可选),
                "region": str (可选)
            }
        """
        pass
