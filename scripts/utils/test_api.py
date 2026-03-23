import requests
import json
from datetime import datetime

# 简单的测试代码
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://caigou.chinatelecom.com.cn',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://caigou.chinatelecom.com.cn/search',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
}

json_data = {
    'pageNum': 1,
    'pageSize': 5,
    'type': 'e2no',
    'provinceCode': '',
    'noticeSummary': '',
}

print(f"[{datetime.now()}] 正在测试中国电信API...")

try:
    response = requests.post(
        'https://caigou.chinatelecom.com.cn/portal/base/announcementJoin/queryListNew',
        headers=headers,
        json=json_data,
        timeout=30
    )
    
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"响应数据结构: {list(data.keys())}")
            
            if 'data' in data:
                data_content = data['data']
                print(f"data内容类型: {type(data_content)}")
                
                if isinstance(data_content, dict) and 'list' in data_content:
                    records = data_content['list']
                    print(f"获取到 {len(records)} 条记录")
                    
                    if records:
                        print("\n前3条记录预览:")
                        for i, record in enumerate(records[:3]):
                            print(f"\n记录 {i+1}:")
                            print(f"  标题: {record.get('docTitle', 'N/A')}")
                            print(f"  省份: {record.get('provinceName', 'N/A')}")
                            print(f"  类型: {record.get('docType', 'N/A')}")
                            print(f"  发布时间: {record.get('createDate', 'N/A')}")
                            print(f"  ID: {record.get('id', 'N/A')}")
                            print(f"  安全码: {record.get('securityViewCode', 'N/A')}")
                            
                else:
                    print(f"data内容: {data_content}")
            else:
                print(f"完整响应: {data}")
                
        except json.JSONDecodeError as e:
            print(f"JSON解析失败：{e}")
            print(f"响应文本: {response.text[:500]}")
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        
except Exception as e:
    print(f"请求异常: {e}")

print(f"\n[{datetime.now()}] 测试完成！")