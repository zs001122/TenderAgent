import requests
import pandas as pd
from datetime import datetime
import time
import json

# 全局变量：存储已抓取的公告ID（避免重复）
crawled_ids = set()
# 保存文件路径
SAVE_PATH = "中国移动采购公告.csv"

def fetch_bidding_notices():
    """使用API获取采购公告列表"""
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://b2b.10086.cn',
        'Pragma': 'no-cache',
        'Referer': 'https://b2b.10086.cn/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
        'processInstId': '-1',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'userLoginName': '-1',
    }

    all_notices = []
    page = 1
    max_pages = 5  # 限制页数避免请求过多
    
    while page <= max_pages:
        print(f"[{datetime.now()}] 正在获取第 {page} 页数据...")
        
        json_data = {
            'name': '',
            'publishType': 'PROCUREMENT',
            'publishOneType': 'PROCUREMENT',
            'purchaseType': '',
            'companyType': '',
            'size': 20,
            'current': page,
            'sfactApplColumn5': 'PC',
        }

        try:
            response = requests.post(
                'https://b2b.10086.cn/api-b2b/api-sync-es/white_list_api/b2b/publish/queryList',
                headers=headers,
                json=json_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 解析响应数据
                if 'data' in data and 'records' in data['data']:
                    records = data['data']['records']
                    
                    if not records:
                        print(f"第 {page} 页无数据，停止获取")
                        break
                    
                    print(f"第 {page} 页获取到 {len(records)} 条记录")
                    
                    for record in records:
                        try:
                            # 提取关键信息
                            title = record.get('name', '')
                            publish_date = record.get('publishTime', '')
                            notice_type = record.get('publishOneTypeName', '')
                            company = record.get('companyName', '')
                            
                            # 生成唯一ID（避免重复）
                            notice_id = f"{title}_{publish_date}"
                            
                            # 仅添加未抓取过的公告
                            if title and notice_id not in crawled_ids:
                                crawled_ids.add(notice_id)
                                all_notices.append({
                                    "标题": title,
                                    "发布日期": publish_date,
                                    "公告类型": notice_type,
                                    "采购单位": company,
                                    "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                        except Exception as e:
                            print(f"解析单条记录失败：{e}")
                            continue
                    
                    page += 1
                    
                    # 添加延迟避免请求过快
                    time.sleep(1)
                    
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
        except json.JSONDecodeError as e:
            print(f"JSON解析失败：{e}")
            print(f"响应内容: {response.text}")
            break
        except Exception as e:
            print(f"获取数据失败：{e}")
            break
    
    return all_notices

def save_to_csv(notices):
    """保存数据到CSV文件"""
    if not notices:
        print("[{datetime.now()}] 无新公告")
        return
    
    try:
        df = pd.DataFrame(notices)
        
        # 如果文件已存在，先读取现有数据
        try:
            existing_df = pd.read_csv(SAVE_PATH)
            df = pd.concat([existing_df, df], ignore_index=True)
            # 去重（防止手动修改文件导致的重复）
            df = df.drop_duplicates(subset=["标题", "发布日期"], keep="first")
        except FileNotFoundError:
            pass
        
        # 保存到CSV文件
        df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
        print(f"[{datetime.now()}] 成功抓取 {len(notices)} 条新公告，已保存到 {SAVE_PATH}")
        
        # 显示前几条数据
        print("前几条数据预览:")
        print(df.head())
        
        # 显示统计信息
        print(f"\n统计信息:")
        print(f"总记录数: {len(df)}")
        if '公告类型' in df.columns:
            print(f"公告类型分布:")
            print(df['公告类型'].value_counts())
        if '采购单位' in df.columns:
            print(f"采购单位数量: {df['采购单位'].nunique()}")
        
    except Exception as e:
        print(f"保存CSV文件失败：{e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print(f"[{datetime.now()}] 开始获取中国移动采购公告...")
    
    # 获取公告数据
    notices = fetch_bidding_notices()
    
    # 保存到CSV文件
    save_to_csv(notices)
    
    print(f"[{datetime.now()}] 任务完成！")

if __name__ == "__main__":
    main()