import asyncio
from datetime import datetime
import json
from typing import Iterator, Dict, Any, Optional, List
from playwright.async_api import async_playwright

from .base_scraper import BaseScraper

class ChinaTelecomScraper(BaseScraper):
    def __init__(self):
        self.base_url = 'https://caigou.chinatelecom.com.cn'
        self.crawled_ids = set()

    @property
    def name(self) -> str:
        return "中国电信"

    def run(self, max_pages: int = 3, last_publish_date: Optional[datetime] = None) -> Iterator[Dict[str, Any]]:
        """
        因为 playwright 是异步的，我们将异步执行包装在同步生成器中
        以匹配 BaseScraper 接口。
        """
        # 运行异步爬虫并 yield 结果
        # 为了避免复杂的异步生成器，我们可以收集它们或使用异步事件循环
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
        
        results = loop.run_until_complete(self._async_run(max_pages, last_publish_date))
        for item in results:
            yield item

    async def _async_run(self, max_pages: int, last_publish_date: Optional[datetime]) -> List[Dict[str, Any]]:
        print(f"[{datetime.now()}] 开始获取中国电信采购公告...")
        all_tenders = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            try:
                print("正在访问主页...")
                await page.goto(self.base_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # 获取公告列表
                all_tenders = await self._fetch_notices(page, max_pages, last_publish_date)
            except Exception as e:
                print(f"运行爬虫失败：{e}")
            finally:
                await browser.close()
                
        return all_tenders

    async def _fetch_notices(self, page, max_pages: int, last_publish_date: Optional[datetime]) -> List[Dict]:
        all_notices = []
        page_num = 1
        stop_crawling = False
        
        while page_num <= max_pages and not stop_crawling:
            print(f"[{datetime.now()}] 正在获取第 {page_num} 页公告...")
            
            try:
                list_url = f"{self.base_url}/#/biddingNotice"
                await page.goto(list_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                response = await page.evaluate(f"""
                    () => {{
                        const params = {{
                            pageNum: {page_num},
                            pageSize: 20,
                            type: 'e2no',
                            provinceCode: '',
                            noticeSummary: ''
                        }};
                        return fetch('{self.base_url}/portal/base/announcementJoin/queryListNew', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            }},
                            body: JSON.stringify(params)
                        }}).then(res => res.json()).catch(err => null);
                    }}
                """)
                
                if response and response.get('code') == 200:
                    records = response.get('data', {}).get('pageInfo', {}).get('list', [])
                    if not records:
                        break
                        
                    for record in records:
                        docId = record.get('docId')
                        title = record.get('docTitle', '')
                        pub_date_str = record.get('createDate', '')
                        
                        try:
                            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            try:
                                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                            except:
                                pub_date = datetime.now()
                                
                        # 检查增量条件
                        if last_publish_date and pub_date < last_publish_date:
                            print(f"遇到旧数据 ({pub_date} < {last_publish_date})，停止抓取。")
                            stop_crawling = True
                            break
                            
                        security_code = record.get('securityViewCode', '')
                        detail_url = f"{self.base_url}/DeclareDetails?id={docId}&type=1&docTypeCode=TenderAnnouncement&securityViewCode={security_code}"
                        
                        if detail_url not in self.crawled_ids:
                            self.crawled_ids.add(detail_url)
                            
                            # 获取详情
                            details = await self._fetch_details(page, detail_url)
                            
                            tender_data = {
                                "source_url": detail_url,
                                "source_site": self.name,
                                "title": title,
                                "publish_date": pub_date,
                                "notice_type": record.get('docType', ''),
                                "region": record.get('provinceName', ''),
                                "content": details.get("content", ""),
                            }
                            all_notices.append(tender_data)
                            
                    page_num += 1
                    await page.wait_for_timeout(2000)
                else:
                    break
            except Exception as e:
                print(f"获取第 {page_num} 页数据失败：{e}")
                break
                
        return all_notices

    async def _fetch_details(self, page, detail_url: str) -> Dict:
        try:
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            content = await page.evaluate("""
                () => {
                    const contentElement = document.querySelector('.notice-content, .content, .detail-content, [class*="content"]');
                    return contentElement ? contentElement.innerText : '';
                }
            """)
            return {"content": content[:5000] if content else ""}
        except Exception:
            return {"content": ""}
