import time
import schedule
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

# 全局变量：存储已抓取的公告ID（避免重复）
crawled_ids = set()
# 保存文件路径
SAVE_PATH = "中国移动采购公告.csv"

def crawl_bidding_notices():
    """核心爬取函数：抓取采购公告列表"""
    try:
        with sync_playwright() as p:
            # 启动浏览器（headless=True 为无界面模式，False 可看到浏览器窗口）
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 访问目标网站，等待页面加载完成
            print(f"[{datetime.now()}] 开始访问网站...")
            page.goto("https://b2b.10086.cn/#/biddingProcurementBulletin", wait_until="networkidle")
            
            # 等待公告列表加载（根据网页结构调整等待时间/条件）
            page.wait_for_selector(".el-table__body", timeout=10000)
            print(f"[{datetime.now()}] 页面加载完成，开始提取数据...")

            # 提取公告数据
            notices = []
            # 定位表格行（根据网页实际DOM结构调整选择器）
            rows = page.locator(".el-table__body tr").all()
            
            for row in rows:
                # 提取每一行的关键信息（需根据网页实际元素调整选择器）
                try:
                    # 公告标题
                    title = row.locator("td:nth-child(2)").inner_text().strip()
                    # 发布日期
                    publish_date = row.locator("td:nth-child(3)").inner_text().strip()
                    # 公告链接（动态链接需提取属性）
                    link_elem = row.locator("td:nth-child(2) a")
                    link = link_elem.get_attribute("href") if link_elem else ""
                    # 生成唯一ID（避免重复）
                    notice_id = f"{title}_{publish_date}"

                    # 仅添加未抓取过的公告
                    if notice_id not in crawled_ids:
                        crawled_ids.add(notice_id)
                        notices.append({
                            "标题": title,
                            "发布日期": publish_date,
                            "链接": f"https://b2b.10086.cn{link}" if link else "",
                            "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                except Exception as e:
                    print(f"提取单条公告失败：{e}")
                    continue

            # 关闭浏览器
            browser.close()

            # 保存数据
            if notices:
                # 追加模式写入CSV
                df = pd.DataFrame(notices)
                # 如果文件不存在则创建，存在则追加（不重复写表头）
                try:
                    existing_df = pd.read_csv(SAVE_PATH)
                    df = pd.concat([existing_df, df], ignore_index=True)
                    # 去重（防止手动修改文件导致的重复）
                    df = df.drop_duplicates(subset=["标题", "发布日期"], keep="first")
                except FileNotFoundError:
                    pass
                df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
                print(f"[{datetime.now()}] 成功抓取 {len(notices)} 条新公告，已保存到 {SAVE_PATH}")
            else:
                print(f"[{datetime.now()}] 无新公告")

    except Exception as e:
        print(f"爬取失败：{e}")

if __name__ == "__main__":
    # 直接执行爬取（去掉定时任务部分）
    crawl_bidding_notices()