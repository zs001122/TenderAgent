import asyncio
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
import time

class ChinaTelecomPlaywrightScraper:
    def __init__(self):
        self.base_url = 'https://caigou.chinatelecom.com.cn'
        self.save_path = "../../data/中国电信采购公告.csv"
        self.crawled_ids = set()
        
    async def fetch_notice_list(self, page, notice_type: str = "e2no", max_pages: int = 3) -> List[Dict]:
        """获取公告列表"""
        all_notices = []
        page_num = 1
        
        while page_num <= max_pages:
            print(f"[{datetime.now()}] 正在获取第 {page_num} 页公告...")
            
            try:
                # 访问公告列表页面
                list_url = f"{self.base_url}/#/biddingNotice"
                await page.goto(list_url, wait_until="networkidle", timeout=30000)
                
                # 等待页面加载完成
                await page.wait_for_timeout(3000)
                
                # 获取页面数据
                response = await page.evaluate(f"""
                    () => {{
                        // 构造API请求参数
                        const params = {{
                            pageNum: {page_num},
                            pageSize: 20,
                            type: '{notice_type}',
                            provinceCode: '',
                            noticeSummary: ''
                        }};
                        
                        // 使用fetch API获取数据
                        return fetch('{self.base_url}/portal/base/announcementJoin/queryListNew', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            }},
                            body: JSON.stringify(params)
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            console.log('API Response:', data);
                            return data;
                        }})
                        .catch(error => {{
                            console.error('API Error:', error);
                            return null;
                        }});
                    }}
                """)
                
                if response and response.get('code') == 200:
                    data = response.get('data', {})
                    page_info = data.get('pageInfo', {})
                    records = page_info.get('list', [])
                    
                    if not records:
                        print(f"第 {page_num} 页无数据，停止获取")
                        break
                    
                    print(f"第 {page_num} 页获取到 {len(records)} 条记录")
                    
                    for record in records:
                        try:
                            docId = record.get('docId')
                            title = record.get('docTitle', '')
                            publish_date = record.get('createDate', '')
                            notice_type_name = record.get('docType', '')
                            province = record.get('provinceName', '')
                            security_code = record.get('securityViewCode', '')
                            
                            # 生成唯一ID
                            unique_id = f"{docId}_{title}_{publish_date}"
                            
                            if docId and unique_id not in self.crawled_ids:
                                self.crawled_ids.add(unique_id)
                                detail_url = f"{self.base_url}/DeclareDetails?id={docId}&type=1&docTypeCode=TenderAnnouncement&securityViewCode={security_code}"
                                notice_info = {
                                    "详情页ID": docId,
                                    "标题": f'=HYPERLINK("{detail_url}", "{title}")',
                                    "发布日期": publish_date,
                                    "公告类型": notice_type_name,
                                    "省份": province,
                                    "安全码": security_code,
                                    "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                # 获取详细信息
                                details = await self.fetch_notice_details(page, docId, detail_url)
                                if details:
                                    notice_info.update(details)
                                
                                all_notices.append(notice_info)
                                
                                if len(all_notices) % 10 == 0:
                                    print(f"已处理 {len(all_notices)} 条公告")
                                    
                        except Exception as e:
                            print(f"解析单条记录失败：{e}")
                            continue
                    
                    page_num += 1
                    await page.wait_for_timeout(2000)  # 添加延迟避免请求过快
                    
                else:
                    print(f"API响应异常: {response}")
                    break
                    
            except Exception as e:
                print(f"获取第 {page_num} 页数据失败：{e}")
                break
        
        return all_notices
    
    async def fetch_notice_details(self, page, docId: str, detail_url: str) -> Optional[Dict]:
        """获取单个公告的详细信息"""
        try:
            # 访问详情页面
            await page.goto(detail_url, wait_until="networkidle", timeout=30000)
            
            # 等待页面加载
            await page.wait_for_timeout(3000)
            
            # 获取页面内容
            content = await page.evaluate("""
                () => {
                    // 尝试获取公告内容
                    const contentElement = document.querySelector('.notice-content, .content, .detail-content, [class*="content"]');
                    const content = contentElement ? contentElement.innerText : '';
                    
                    // 获取附件信息
                    const attachments = [];
                    const attachmentElements = document.querySelectorAll('[class*="attachment"], [class*="file"]');
                    attachmentElements.forEach(element => {
                        const link = element.querySelector('a');
                        if (link) {
                            attachments.push({
                                fileName: link.innerText.trim(),
                                filePath: link.href
                            });
                        }
                    });
                    
                    return {
                        noticeContent: content,
                        attachmentList: attachments
                    };
                }
            """)
            
            if content:
                attachments = content.get('attachmentList', [])
                return {
                    "公告内容": content.get('noticeContent', ''),
                    "附件数量": len(attachments),
                    "附件列表": json.dumps(attachments, ensure_ascii=False),
                    "完整内容": len(content.get('noticeContent', ''))
                }
            
        except Exception as e:
            print(f"获取公告详情失败 (ID: {docId}): {e}")
        
        return None
    
    def save_to_csv(self, notices: List[Dict]):
        """保存数据到CSV文件"""
        if not notices:
            print(f"[{datetime.now()}] 无新公告")
            return
        
        try:
            df = pd.DataFrame(notices)
            
            # 如果文件已存在，先读取现有数据
            try:
                existing_df = pd.read_csv(self.save_path)
                df = pd.concat([existing_df, df], ignore_index=True)
                # 去重（基于公告ID）
                df = df.drop_duplicates(subset=["公告ID"], keep="first")
            except FileNotFoundError:
                pass
            
            # 保存到CSV文件
            df.to_csv(self.save_path, index=False, encoding="utf-8-sig")
            print(f"[{datetime.now()}] 成功抓取 {len(notices)} 条新公告，已保存到 {self.save_path}")
            
            # 显示统计信息
            print(f"\n统计信息:")
            print(f"总记录数: {len(df)}")
            if '公告类型' in df.columns:
                print(f"公告类型分布:")
                print(df['公告类型'].value_counts().head(10))
            if '省份' in df.columns:
                print(f"省份数量: {df['省份'].nunique()}")
                print(f"省份分布:")
                print(df['省份'].value_counts().head(10))
            
            # 显示前几条数据
            print(f"\n前几条数据预览:")
            display_cols = ['标题', '发布日期', '公告类型', '省份']
            available_cols = [col for col in display_cols if col in df.columns]
            if available_cols:
                print(df[available_cols].head())
            
        except Exception as e:
            print(f"保存CSV文件失败：{e}")
            import traceback
            traceback.print_exc()
    
    async def run(self, max_pages: int = 3):
        """运行爬虫"""
        print(f"[{datetime.now()}] 开始获取中国电信采购公告...")
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=True,  # 设置为True为无界面模式
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # 设置页面超时
            page.set_default_timeout(30000)
            
            try:
                # 首先访问主页获取cookies
                print("正在访问主页...")
                await page.goto(self.base_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # 获取公告列表
                notices = await self.fetch_notice_list(page, max_pages=max_pages)
                
                # 保存数据
                self.save_to_csv(notices)
                
                print(f"\n[{datetime.now()}] 任务完成！总共获取 {len(notices)} 条公告")
                
            except Exception as e:
                print(f"运行爬虫失败：{e}")
                import traceback
                traceback.print_exc()
            
            finally:
                await browser.close()

async def main():
    """主函数"""
    scraper = ChinaTelecomPlaywrightScraper()
    await scraper.run(max_pages=2)  # 限制页数避免请求过多

if __name__ == "__main__":
    asyncio.run(main())