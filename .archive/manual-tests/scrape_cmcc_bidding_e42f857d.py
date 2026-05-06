"""
中国移动采购与招标网 - 招标大厅抓取脚本
抓取"正在招标"公告列表（前N页），包括：
  - 公告基本信息（标题、单位、发布时间、截止时间等）
  - 公告详情链接
  - 公告PDF正文内容（自动解码并提取文字）
  - 相关附件列表及下载链接

依赖安装：
  pip install playwright pymupdf
  playwright install chromium

用法：
  python scrape_cmcc_bidding.py
"""

import json
import base64
import csv
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("请先安装 pymupdf：pip install pymupdf")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("请先安装 playwright：pip install playwright && playwright install chromium")
    sys.exit(1)


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
PAGES_TO_SCRAPE = 2          # 要抓取的页数
PAGE_SIZE = 20               # 每页条数（与网站一致）
BASE_URL = "https://b2b.10086.cn"
PDF_DIR = "pdfs"             # 临时 PDF 保存目录
OUTPUT_CSV = "中国移动招标公告.csv"
CONTENT_MAX_LEN = 5000       # CSV 中公告正文最大字符数

# API 端点（相对路径，通过浏览器 page.evaluate + fetch 调用）
API_LIST = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryList"
API_DETAIL = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryDetail"
API_FILES = "/api-b2b/api-file/file/listByAttrOnAuth"

# 附件下载链接模板
FILE_DOWNLOAD_TPL = (
    f"{BASE_URL}/api-b2b/api-file/file/download"
    "?fileId={fileId}&waterMarkFlag=N"
)


# ──────────────────────────────────────────────
# 浏览器内 fetch 封装
# ──────────────────────────────────────────────
def browser_post(page, api_path: str, payload: dict):
    """在浏览器上下文内发起 POST 请求，返回 JSON 解析后的 dict。
    利用浏览器自身的 TLS 和 Cookie，无需处理 SSL 证书等问题。
    """
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


def browser_post_text(page, api_path: str, payload: dict) -> str:
    """同上，但返回原始文本（用于获取大字段如 noticeContent）。"""
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
        [api_path, payload],
    )


# ──────────────────────────────────────────────
# 数据抓取
# ──────────────────────────────────────────────
def fetch_list(page, page_no: int) -> list:
    """获取第 page_no 页的公告列表。"""
    payload = {
        "size": PAGE_SIZE,
        "current": page_no,
        "companyType": "",
        "name": "",
        "publishType": "PROCUREMENT",
        "publishOneType": "PROCUREMENT",
        "sfactApplColumn5": "PC",
    }
    data = browser_post(page, API_LIST, payload)
    return data.get("data", {}).get("content", [])


def fetch_detail_meta(page, item_id: str, item_uuid: str) -> dict:
    """获取单条公告详情的元数据（不含大体积的 noticeContent）。"""
    payload = {
        "publishId": item_id,
        "publishUuid": item_uuid,
        "publishType": "PROCUREMENT",
        "publishOneType": "PROCUREMENT",
    }
    data = browser_post(page, API_DETAIL, payload)
    d = data.get("data", {})
    return {
        "projectName": d.get("projectName", ""),
        "tenderSaleDeadline": d.get("tenderSaleDeadline", ""),
        "contentType": d.get("contentType", ""),
    }


def fetch_pdf_content(page, item_id: str, item_uuid: str) -> str:
    """获取公告 PDF 的 base64 编码内容。"""
    payload = {
        "publishId": item_id,
        "publishUuid": item_uuid,
        "publishType": "PROCUREMENT",
        "publishOneType": "PROCUREMENT",
    }
    return browser_post_text(page, API_DETAIL, payload)


def fetch_attachments(page, item_uuid: str) -> list:
    """获取附件列表，返回 [{filename, fileId, download_url}, ...]。"""
    payload = {
        "attr1": "PT_VENDOR_PUBLISH",
        "attr2": item_uuid,
        "attr3": "PT_VENDOR_PUBLISH_FILE",
        "authFlag": "N",
    }
    data = browser_post(page, API_FILES, payload)
    files = data.get("data", []) or []
    result = []
    for f in files:
        fid = f.get("fileId", "")
        result.append({
            "filename": f.get("filename", ""),
            "fileId": fid,
            "download_url": FILE_DOWNLOAD_TPL.format(fileId=fid) if fid else "",
        })
    return result


# ──────────────────────────────────────────────
# PDF base64 解码 → 文字
# ──────────────────────────────────────────────
def decode_pdf_base64(b64_str: str, idx: int) -> str:
    """将 base64 编码的 PDF 解码并用 PyMuPDF 提取文字。"""
    os.makedirs(PDF_DIR, exist_ok=True)
    pdf_path = os.path.join(PDF_DIR, f"notice_{idx}.pdf")
    try:
        pdf_bytes = base64.b64decode(b64_str)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        doc = fitz.open(pdf_path)
        texts = [p.get_text() for p in doc]
        doc.close()
        return "\n".join(texts).strip()
    except Exception as e:
        return f"[PDF解析错误: {e}]"


def build_detail_url(item_id: str, item_uuid: str) -> str:
    """构建公告详情页面的访问链接。"""
    return (
        f"{BASE_URL}/#/noticeDetail"
        f"?publishId={item_id}"
        f"&publishUuid={item_uuid}"
        f"&publishType=PROCUREMENT"
        f"&publishOneType=PROCUREMENT"
    )


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
def main():
    with sync_playwright() as p:
        # 1. 启动浏览器
        print("[1/5] 启动浏览器...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 访问目标页面（建立 session / cookie）
        page.goto(
            f"{BASE_URL}/#/biddingHall",
            wait_until="networkidle",
            timeout=30000,
        )

        # 2. 获取列表
        print(f"[2/5] 获取前 {PAGES_TO_SCRAPE} 页列表...")
        all_items = []
        for pg in range(1, PAGES_TO_SCRAPE + 1):
            records = fetch_list(page, pg)
            for r in records:
                r["_page"] = pg
            all_items.extend(records)
            print(f"       第 {pg} 页: {len(records)} 条")
        print(f"       合计: {len(all_items)} 条")

        # 3. 获取详情元数据 + 附件
        print("[3/5] 获取详情元数据与附件...")
        detail_metas = []
        attachments_list = []
        for i, item in enumerate(all_items):
            short = item.get("name", "")[:40]
            print(f"  [{i+1}/{len(all_items)}] (meta) {short}...")

            meta = fetch_detail_meta(page, item["id"], item["uuid"])
            detail_metas.append(meta)

            atts = fetch_attachments(page, item["uuid"])
            attachments_list.append(atts)

        # 4. 提取 PDF 正文
        print("[4/5] 提取 PDF 正文...")
        pdf_texts = []
        for i, item in enumerate(all_items):
            short = item.get("name", "")[:40]
            ct = detail_metas[i]["contentType"]
            if ct != "pdf":
                pdf_texts.append("")
                print(f"  [{i+1}/{len(all_items)}] (skip) {short}")
                continue

            print(f"  [{i+1}/{len(all_items)}] (pdf)  {short}...")
            b64 = fetch_pdf_content(page, item["id"], item["uuid"])
            text = decode_pdf_base64(b64, i) if b64 else ""
            pdf_texts.append(text)

        # 5. 输出 CSV
        print(f"[5/5] 写入 {OUTPUT_CSV}...")
        fieldnames = [
            "页码", "单位", "标题", "项目名称",
            "发布时间", "截止时间", "详情链接",
            "附件名称", "附件下载链接", "公告正文",
        ]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, item in enumerate(all_items):
                att = attachments_list[i]
                att_names = " | ".join(a["filename"] for a in att)
                att_urls = " | ".join(
                    a["download_url"] for a in att if a["fileId"]
                )
                writer.writerow({
                    "页码": item["_page"],
                    "单位": item.get("companyTypeName", ""),
                    "标题": item.get("name", ""),
                    "项目名称": detail_metas[i]["projectName"],
                    "发布时间": item.get("publishDate", ""),
                    "截止时间": detail_metas[i]["tenderSaleDeadline"],
                    "详情链接": build_detail_url(item["id"], item["uuid"]),
                    "附件名称": att_names,
                    "附件下载链接": att_urls,
                    "公告正文": (
                        pdf_texts[i][:CONTENT_MAX_LEN]
                        if pdf_texts[i]
                        else ""
                    ),
                })

        browser.close()
        print(f"\n完成！共 {len(all_items)} 条记录已写入 {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
