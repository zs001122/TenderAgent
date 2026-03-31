from scrapling.spiders import Spider, Response, Request  
from scrapling.fetchers import FetcherSession, AsyncStealthySession  
import json  
from datetime import datetime  
import pandas as pd  
  
class ChinaTelecomSpider(Spider):  
    name = "china_telecom_tenders"  
    start_urls = ["https://caigou.chinatelecom.com.cn"]  
    concurrent_requests = 5  
    crawled_ids = set()  
      
    def configure_sessions(self, manager):  
        """配置多个会话"""  
        # 快速HTTP会话用于API调用  
        manager.add("api", FetcherSession(  
            impersonate="chrome",  
            stealthy_headers=True  
        ))  
          
        # 隐秘浏览器会话用于详情页  
        manager.add("detail", AsyncStealthySession(  
            headless=True,  
            solve_cloudflare=True,  
            block_webrtc=True,  
            hide_canvas=True,  
            lazy=True  # 延迟启动  
        ))  
      
    async def parse(self, response: Response):  
        """入口页面解析"""  
        # 获取不同类型的公告  
        notice_types = ["e2no", "e2no"]  # 可以添加更多类型  
          
        for notice_type in notice_types:  
            # 生成API请求  
            yield Request(  
                f"https://caigou.chinatelecom.com.cn/portal/base/announcementJoin/queryListNew",  
                method="POST",  
                json={  
                    "pageNum": 1,  
                    "pageSize": 20,  
                    "type": notice_type,  
                    "provinceCode": "",  
                    "noticeSummary": ""  
                },  
                sid="api",  
                callback=self.parse_list,  
                meta={"notice_type": notice_type, "page_num": 1}  
            )  
      
    async def parse_list(self, response: Response):  
        """解析公告列表"""  
        try:  
            data = response.json()  
            if data.get('code') == 200:  
                page_info = data.get('data', {}).get('pageInfo', {})  
                records = page_info.get('list', [])  
                  
                if not records:  
                    return  
                  
                notice_type = response.meta.get("notice_type")  
                page_num = response.meta.get("page_num")  
                  
                print(f"第 {page_num} 页获取到 {len(records)} 条记录")  
                  
                for record in records:  
                    docId = record.get('docId')  
                    title = record.get('docTitle', '')  
                    publish_date = record.get('createDate', '')  
                    notice_type_name = record.get('docType', '')  
                    province = record.get('provinceName', '')  
                    security_code = record.get('securityViewCode', '')  
                      
                    unique_id = f"{docId}_{title}_{publish_date}"  
                      
                    if docId and unique_id not in self.crawled_ids:  
                        self.crawled_ids.add(unique_id)  
                          
                        # 请求详情页  
                        detail_url = f"https://caigou.chinatelecom.com.cn/DeclareDetails?id={docId}&type=1&docTypeCode=TenderAnnouncement&securityViewCode={security_code}"  
                          
                        yield Request(  
                            detail_url,  
                            sid="detail",  
                            callback=self.parse_detail,  
                            meta={  
                                "详情页ID": docId,  
                                "标题": title,  
                                "发布日期": publish_date,  
                                "公告类型": notice_type_name,  
                                "省份": province,  
                                "安全码": security_code,  
                                "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                            }  
                        )  
                  
                # 处理分页  
                total = page_info.get('total', 0)  
                if page_num * 20 < total:  
                    next_page = page_num + 1  
                    yield Request(  
                        response.url,  
                        method="POST",  
                        json={  
                            "pageNum": next_page,  
                            "pageSize": 20,  
                            "type": notice_type,  
                            "provinceCode": "",  
                            "noticeSummary": ""  
                        },  
                        sid="api",  
                        callback=self.parse_list,  
                        meta={"notice_type": notice_type, "page_num": next_page}  
                    )  
                      
        except Exception as e:  
            print(f"解析列表失败: {e}")  
      
    async def parse_detail(self, response: Response):  
        """解析详情页"""  
        try:  
            # 提取内容  
            content_element = response.css('.notice-content, .content, .detail-content, [class*="content"]')  
            content = content_element.get_all_text() if content_element else ''  
              
            # 获取附件  
            attachments = []  
            attachment_elements = response.css('[class*="attachment"], [class*="file"] a')  
            for element in attachment_elements:  
                file_name = element.get_text(strip=True)  
                file_path = element.attrib.get('href', '')  
                if file_name:  
                    attachments.append({  
                        'fileName': file_name,  
                        'filePath': file_path  
                    })  
              
            # 构建结果  
            result = response.meta.copy()  
            title = result.get("标题", "").replace('"', '""')  
            result.update({  
                "公告内容": f'=HYPERLINK("{response.url}", "{title}")',  
                "附件数量": len(attachments),  
                "附件列表": json.dumps(attachments, ensure_ascii=False),  
                "完整内容": len(content),  
                "详情页URL": response.url  
            })  
              
            yield result  
              
        except Exception as e:  
            print(f"解析详情失败: {e}")  
  
def main():  
    """运行Spider"""  
    # 创建Spider实例  
    spider = ChinaTelecomSpider(crawldir="./telecom_crawl_data")  
      
    # 运行并获取结果  
    result = spider.start()  
      
    # 保存为CSV  
    if result.items:  
        df = pd.DataFrame(list(result.items))  
        df.to_csv("中国电信采购公告_scrapling.csv", index=False, encoding="utf-8-sig")  
        print(f"成功保存 {len(result.items)} 条记录")  
      
    # 显示统计  
    print(f"总请求数: {result.stats.total_requests}")  
    print(f"抓取项目数: {result.stats.items_scraped}")  
  
if __name__ == "__main__":  
    main()