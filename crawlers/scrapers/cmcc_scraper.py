import json
import base64
import os
import re
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    print("WARNING: pymupdf not installed. PDF text extraction will fail.")

from .base_scraper import BaseScraper

class ChinaMobileScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://b2b.10086.cn"
        self.api_list = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryList"
        self.api_detail = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryDetail"
        self.api_files = "/api-b2b/api-file/file/listByAttrOnAuth"
        self.pdf_dir = "pdfs"
        self.crawled_urls = set()

    @property
    def name(self) -> str:
        return "中国移动"

    def run(self, max_pages: int = 3, last_publish_date: Optional[datetime] = None) -> Iterator[Dict[str, Any]]:
        print(f"[{datetime.now()}] 开始获取中国移动采购公告...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            # 初始化 session
            page.goto(f"{self.base_url}/#/biddingHall", wait_until="networkidle", timeout=30000)

            stop_crawling = False
            for pg in range(1, max_pages + 1):
                if stop_crawling:
                    break
                    
                print(f"       第 {pg} 页...")
                records = self._fetch_list(page, pg)
                if not records:
                    break
                    
                for record in records:
                    pub_date_str = record.get("publishDate", "")
                    try:
                        pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                    except:
                        pub_date = datetime.now()

                    if last_publish_date and pub_date < last_publish_date:
                        print(f"遇到旧数据 ({pub_date} < {last_publish_date})，停止抓取。")
                        stop_crawling = True
                        break

                    item_id = record["id"]
                    item_uuid = record["uuid"]
                    detail_url = self._build_detail_url(item_id, item_uuid)

                    if detail_url in self.crawled_urls:
                        continue
                        
                    self.crawled_urls.add(detail_url)

                    # 获取详情
                    meta = self._fetch_detail_meta(page, item_id, item_uuid)
                    
                    # 提取 PDF
                    content_text = ""
                    if meta.get("contentType") == "pdf" and fitz:
                        b64 = self._fetch_pdf_content(page, item_id, item_uuid)
                        if b64:
                            content_text = self._decode_pdf_base64(b64, item_id)
                            
                    tender_data = {
                        "source_url": detail_url,
                        "source_site": self.name,
                        "title": record.get("name", ""),
                        "publish_date": pub_date,
                        "notice_type": "招标公告", # 假设从 biddingHall 获取的都是招标公告
                        "region": record.get("companyTypeName", ""),
                        "content": content_text[:5000],
                    }
                    yield tender_data

            browser.close()

    def _browser_post(self, page, api_path: str, payload: dict):
        return page.evaluate(
            """async ([url, body]) => {
                const resp = await fetch(url, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(body)
                });
                return await resp.json();
            }""",
            [api_path, payload],
        )

    def _fetch_list(self, page, page_no: int) -> list:
        payload = {
            "size": 20,
            "current": page_no,
            "companyType": "",
            "name": "",
            "publishType": "PROCUREMENT",
            "publishOneType": "PROCUREMENT",
            "sfactApplColumn5": "PC",
        }
        data = self._browser_post(page, self.api_list, payload)
        return data.get("data", {}).get("content", [])

    def _fetch_detail_meta(self, page, item_id: str, item_uuid: str) -> dict:
        payload = {
            "publishId": item_id,
            "publishUuid": item_uuid,
            "publishType": "PROCUREMENT",
            "publishOneType": "PROCUREMENT",
        }
        data = self._browser_post(page, self.api_detail, payload)
        d = data.get("data", {})
        return {
            "projectName": d.get("projectName", ""),
            "tenderSaleDeadline": d.get("tenderSaleDeadline", ""),
            "contentType": d.get("contentType", ""),
        }

    def _fetch_pdf_content(self, page, item_id: str, item_uuid: str) -> str:
        payload = {
            "publishId": item_id,
            "publishUuid": item_uuid,
            "publishType": "PROCUREMENT",
            "publishOneType": "PROCUREMENT",
        }
        return page.evaluate(
            """async ([url, body]) => {
                const resp = await fetch(url, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(body)
                });
                const data = await resp.json();
                return (data.data || {}).noticeContent || "";
            }""",
            [self.api_detail, payload],
        )

    def _decode_pdf_base64(self, b64_str: str, file_id: str) -> str:
        os.makedirs(self.pdf_dir, exist_ok=True)
        pdf_path = os.path.join(self.pdf_dir, f"notice_{file_id}.pdf")
        try:
            pdf_bytes = base64.b64decode(b64_str)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            doc = fitz.open(pdf_path)
            texts = [p.get_text() for p in doc]
            doc.close()
            
            # 清理临时 pdf 文件
            os.remove(pdf_path)
            
            return "\n".join(texts).strip()
        except Exception as e:
            return f"[PDF解析错误: {e}]"

    def _build_detail_url(self, item_id: str, item_uuid: str) -> str:
        return (
            f"{self.base_url}/#/noticeDetail"
            f"?publishId={item_id}"
            f"&publishUuid={item_uuid}"
            f"&publishType=PROCUREMENT"
            f"&publishOneType=PROCUREMENT"
        )
