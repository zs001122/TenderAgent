import requests
import pandas as pd
from datetime import datetime
import time
import json
import re
from typing import List, Dict, Optional

class ChinaTelecomScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://caigou.chinatelecom.com.cn',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
        }
        self.base_url = 'https://caigou.chinatelecom.com.cn'
        self.save_path = "中国电信采购公告.csv"
        self.crawled_ids = set()
        
    def get_initial_cookies(self):
        """获取初始cookies"""
        try:
            # 先访问主页获取cookies
            response = self.session.get(self.base_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                print(f"[{datetime.now()}] 成功获取初始cookies")
                
                # 尝试访问公告列表页面以获取更多cookies
                list_response = self.session.post(
                    f'{self.base_url}/portal/base/announcementJoin/queryListNew',
                    headers=self.headers,
                    json={'pageNum': 1, 'pageSize': 1, 'type': 'e2no', 'provinceCode': '', 'noticeSummary': ''},
                    timeout=30
                )
                if list_response.status_code == 200:
                    print(f"[{datetime.now()}] 成功获取列表页面cookies")
                
                return True
            else:
                print(f"[{datetime.now()}] 获取cookies失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"[{datetime.now()}] 获取cookies异常: {e}")
            return False
    
    def fetch_notice_list(self, notice_type: str = "e2no", page_size: int = 20, max_pages: int = 5) -> List[Dict]:
        """
        获取公告列表
        notice_type: e2no=招标公告, e1no=资格预审公告, e3no=询比公告, etc.
        """
        all_notices = []
        page = 1
        
        while page <= max_pages:
            print(f"[{datetime.now()}] 正在获取第 {page} 页 {notice_type} 类型公告...")
            
            json_data = {
                'pageNum': page,
                'pageSize': page_size,
                'type': notice_type,
                'provinceCode': '',
                'noticeSummary': '',
            }

            try:
                response = self.session.post(
                    f'{self.base_url}/portal/base/announcementJoin/queryListNew',
                    headers=self.headers,
                    json=json_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data:
                        records = data['data']['pageInfo']['list']
                        
                        if not records:
                            print(f"第 {page} 页无数据，停止获取")
                            break
                        
                        print(f"第 {page} 页获取到 {len(records)} 条记录")
                        
                        for record in records:
                            try:
                                notice_id = record.get('id')
                                title = record.get('docTitle', '')
                                publish_date = record.get('createDate', '')
                                notice_type_name = record.get('docType', '')
                                province = record.get('provinceName', '')
                                security_code = record.get('securityViewCode', '')
                                
                                # 生成唯一ID
                                unique_id = f"{notice_id}_{title}_{publish_date}"
                                
                                if notice_id and unique_id not in self.crawled_ids:
                                    self.crawled_ids.add(unique_id)
                                    notice_info = {
                                        "公告ID": notice_id,
                                        "标题": title,
                                        "发布日期": publish_date,
                                        "公告类型": notice_type_name,
                                        "省份": province,
                                        "安全码": security_code,
                                        "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    }
                                    
                                    # 获取详细信息
                                    details = self.fetch_notice_details(notice_id, security_code)
                                    if details:
                                        notice_info.update(details)
                                    
                                    all_notices.append(notice_info)
                                    
                                    if len(all_notices) % 10 == 0:
                                        print(f"已处理 {len(all_notices)} 条公告")
                                        
                            except Exception as e:
                                print(f"解析单条记录失败：{e}")
                                continue
                        
                        page += 1
                        time.sleep(1)  # 添加延迟避免请求过快
                        
                    else:
                        print(f"响应数据格式异常: {data}")
                        break
                else:
                    print(f"请求失败，状态码: {response.status_code}")
                    print(f"响应内容: {response.text}")
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"网络请求失败：{e}")
                break
            except Exception as e:
                print(f"获取数据失败：{e}")
                break
        
        return all_notices
    
    def fetch_notice_details(self, notice_id: str, security_code: str) -> Optional[Dict]:
        """获取单个公告的详细信息"""
        try:
            # 使用正确的端点和参数格式
            json_data = {
                'type': 'TenderAnnouncement',
                'id': notice_id,
                'securityViewCode': security_code,
            }
            
            # 更新headers以包含必要的referer
            detail_headers = self.headers.copy()
            detail_headers['referer'] = f'{self.base_url}/DeclareDetails?id={notice_id}&type=1&docTypeCode=TenderAnnouncement&securityViewCode={security_code}'
            
            response = self.session.post(
                f'{self.base_url}/portal/base/tenderannouncement/view',
                headers=detail_headers,
                json=json_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200 and 'data' in result:
                    details = result['data']
                    
                    # 提取关键信息
                    content = details.get('noticeContent', '')
                    attachment_list = details.get('attachmentList', [])
                    
                    # 提取附件信息
                    attachments = []
                    for att in attachment_list:
                        if isinstance(att, dict):
                            att_info = {
                                "文件名": att.get('fileName', ''),
                                "文件大小": att.get('fileSize', ''),
                                "下载链接": att.get('filePath', '')
                            }
                            attachments.append(att_info)
                    
                    return {
                        "公告内容": content[:500] if content else '',  # 限制长度
                        "附件数量": len(attachments),
                        "附件列表": json.dumps(attachments, ensure_ascii=False),
                        "完整内容": len(content) if content else 0
                    }
                else:
                    print(f"获取详情失败: {result.get('msg', '未知错误')}")
            else:
                print(f"获取详情请求失败，状态码: {response.status_code}")
                    
        except Exception as e:
            print(f"获取公告详情失败 (ID: {notice_id}): {e}")
        
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
    
    def run(self, notice_types: List[str] = None, max_pages: int = 3):
        """运行爬虫
        notice_types: 公告类型列表，默认为 ['e2no'] (招标公告)
        """
        if notice_types is None:
            notice_types = ['e2no']  # 默认只获取招标公告
        
        print(f"[{datetime.now()}] 开始获取中国电信采购公告...")
        
        # 获取初始cookies
        if not self.get_initial_cookies():
            print("获取cookies失败，继续尝试...")
        
        all_notices = []
        
        # 获取不同类型的公告
        for notice_type in notice_types:
            print(f"\n[{datetime.now()}] 开始获取 {notice_type} 类型公告...")
            notices = self.fetch_notice_list(notice_type, max_pages=max_pages)
            all_notices.extend(notices)
            print(f"{notice_type} 类型获取完成，共 {len(notices)} 条")
        
        # 保存到CSV文件
        self.save_to_csv(all_notices)
        
        print(f"\n[{datetime.now()}] 任务完成！总共获取 {len(all_notices)} 条公告")

def main():
    """主函数"""
    scraper = ChinaTelecomScraper()
    
    # 可以指定多种公告类型
    notice_types = ['e2no']  # 招标公告
    # notice_types = ['e2no', 'e1no', 'e3no']  # 招标公告、资格预审公告、询比公告
    
    scraper.run(notice_types, max_pages=2)  # 限制页数避免请求过多

if __name__ == "__main__":
    main()