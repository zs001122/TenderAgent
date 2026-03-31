import time
import schedule
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

# 全局变量：存储已抓取的公告ID（避免重复）
crawled_ids = set()
# 保存文件路径
SAVE_PATH = "中国移动采购公告.csv"

def take_screenshot(page, filename):
    """截图保存用于调试"""
    try:
        page.screenshot(path=filename)
        print(f"截图已保存: {filename}")
    except Exception as e:
        print(f"截图失败: {e}")

def debug_page_content(page):
    """调试页面内容"""
    try:
        # 获取页面标题
        title = page.title()
        print(f"页面标题: {title}")
        
        # 获取页面源码前500字符
        content = page.content()[:500]
        print(f"页面内容前500字符: {content}")
        
        # 检查是否有表格相关的元素
        table_elements = page.locator("table, .table, .el-table, .el-table__body").count()
        print(f"找到的表格元素数量: {table_elements}")
        
        # 列出页面上所有的表格类名
        table_classes = page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table, .table, [class*="table"]');
                return Array.from(tables).map(table => ({
                    tag: table.tagName,
                    className: table.className,
                    id: table.id
                }));
            }
        """)
        print(f"页面中的表格元素: {table_classes}")
        
    except Exception as e:
        print(f"调试页面内容失败: {e}")

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
            page.goto("https://b2b.10086.cn/#/biddingProcurementBulletin", wait_until="networkidle", timeout=30000)
            
            print(f"[{datetime.now()}] 页面访问成功，等待内容加载...")
            
            # 等待并调试页面内容
            time.sleep(3)  # 额外等待时间让页面完全加载
            debug_page_content(page)
            take_screenshot(page, "page_loaded.png")
            
            # 尝试多种选择器来找到公告列表
            selectors = [
                ".el-table__body",
                ".el-table",
                "table",
                ".table",
                "[class*='table']",
                ".el-table__body-wrapper",
                ".el-table__body-wrapper tbody"
            ]
            
            table_found = False
            rows = []
            
            for selector in selectors:
                try:
                    print(f"尝试选择器: {selector}")
                    element = page.locator(selector)
                    count = element.count()
                    print(f"找到 {count} 个元素")
                    
                    if count > 0:
                        # 如果是表格，获取行
                        if 'table' in selector or 'tbody' in selector:
                            rows = element.locator('tr').all()
                        else:
                            # 尝试找到行
                            rows = element.locator('tr').all()
                            if not rows:
                                rows = element.all()
                        
                        if rows:
                            print(f"使用选择器 {selector} 找到 {len(rows)} 行数据")
                            table_found = True
                            break
                        
                except Exception as e:
                    print(f"选择器 {selector} 失败: {e}")
                    continue
            
            if not table_found:
                print("未找到表格数据，尝试获取整个页面内容...")
                take_screenshot(page, "page_debug.png")
                
                # 尝试获取页面中所有可能的公告元素
                all_elements = page.locator("div, li, tr").all()
                print(f"找到 {len(all_elements)} 个元素，尝试从中提取公告信息...")
                
                # 简单的文本匹配来寻找可能的公告
                for element in all_elements[:20]:  # 只检查前20个元素
                    try:
                        text = element.inner_text()
                        if len(text) > 10 and ('采购' in text or '招标' in text or '公告' in text):
                            print(f"找到可能的公告: {text[:100]}...")
                    except:
                        continue
            
            # 提取公告数据
            notices = []
            print(f"开始提取 {len(rows)} 行数据...")
            
            for i, row in enumerate(rows):
                try:
                    # 提取每一行的关键信息（需根据网页实际元素调整选择器）
                    # 尝试多种方式来提取标题和日期
                    title = ""
                    publish_date = ""
                    link = ""
                    
                    # 尝试不同的列选择器
                    for col_num in [1, 2, 3]:
                        try:
                            cell_text = row.locator(f"td:nth-child({col_num})").inner_text().strip()
                            if cell_text:
                                if not title and len(cell_text) > 5:
                                    title = cell_text
                                elif not publish_date and (len(cell_text) == 10 or '202' in cell_text or '2023' in cell_text or '2024' in cell_text or '2025' in cell_text):
                                    publish_date = cell_text
                        except:
                            continue
                    
                    # 尝试找到链接
                    try:
                        link_elem = row.locator("a").first
                        if link_elem:
                            link = link_elem.get_attribute("href") or ""
                    except:
                        pass
                    
                    # 如果还是没有标题，尝试获取整行文本
                    if not title:
                        try:
                            title = row.inner_text().strip()[:100]  # 限制长度
                        except:
                            continue
                    
                    # 生成唯一ID（避免重复）
                    notice_id = f"{title}_{publish_date}"

                    # 仅添加未抓取过的公告
                    if title and notice_id not in crawled_ids:
                        crawled_ids.add(notice_id)
                        notices.append({
                            "标题": title,
                            "发布日期": publish_date,
                            "链接": f"https://b2b.10086.cn{link}" if link else "",
                            "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        if len(notices) <= 3:  # 只打印前3个提取的公告
                            print(f"提取到公告: {title[:50]}... 日期: {publish_date}")
                            
                except Exception as e:
                    if i < 5:  # 只打印前5个错误
                        print(f"提取第{i+1}行失败：{e}")
                    continue

            # 关闭浏览器
            browser.close()

            # 保存数据
            if notices:
                print(f"总共提取到 {len(notices)} 条公告")
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
                
                # 显示前几条数据
                print("前几条数据预览:")
                print(df.head())
            else:
                print(f"[{datetime.now()}] 无新公告")

    except Exception as e:
        print(f"爬取失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 直接执行爬取（去掉定时任务部分）
    crawl_bidding_notices()