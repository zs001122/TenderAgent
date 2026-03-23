"""
中国移动采购与招标网 - 招标大厅抓取脚本
抓取"正在招标"公告列表（前N页），包括：
  - 公告基本信息（标题、单位、发布时间、截止时间等）
  - 公告详情链接
  - 公告PDF正文内容（自动解码并提取文字）
  - 相关附件列表及下载链接
  - 附件文件下载保存到本地文件夹

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
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("请先安装 pymupdf：pip install pymupdf")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("请先安装 playwright：pip install playwright && playwright install chromium")
    sys.exit(1)


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
PAGES_TO_SCRAPE = 2           # 要抓取的页数
PAGE_SIZE = 20                # 每页条数（与网站一致）
BASE_URL = "https://b2b.10086.cn"
PDF_DIR = "pdfs"              # 临时 PDF 保存目录
ATTACH_DIR = "attachments"    # 附件保存根目录
OUTPUT_CSV = "中国移动招标公告.csv"
CONTENT_MAX_LEN = 5000        # CSV 中公告正文最大字符数
DOWNLOAD_TIMEOUT = 120000     # 单个附件下载超时（毫秒）
CHROMIUM_PATH = None          # chromium 可执行文件路径，None 则使用默认

# API 端点（相对路径，通过浏览器 page.evaluate + fetch 调用）
API_LIST = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryList"
API_DETAIL = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryDetail"
API_FILES = "/api-b2b/api-file/file/listByAttrOnAuth"


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────
def safe_dirname(name: str) -> str:
    """将公告标题转为安全的文件夹名（去除特殊字符，截断长度）。"""
    name = re.sub(r'[\\/:*?"<>|\n\r]', '_', name)
    return name[:80].strip(' _.')


def browser_post(page, api_path: str, payload: dict):
    """在浏览器上下文内发起 POST 请求，返回 JSON 解析后的 dict。"""
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
    """同上，但只返回 noticeContent 字段（base64 PDF）。"""
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
    """获取单条公告详情的元数据。"""
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


def fetch_attachments_meta(page, item_uuid: str) -> list:
    """获取附件列表元数据，返回 [{filename, fileId}, ...]。"""
    payload = {
        "attr1": "PT_VENDOR_PUBLISH",
        "attr2": item_uuid,
        "attr3": "PT_VENDOR_PUBLISH_FILE",
        "authFlag": "N",
    }
    data = browser_post(page, API_FILES, payload)
    files = data.get("data", []) or []
    return [
        {"filename": f.get("filename", ""), "fileId": f.get("fileId", "")}
        for f in files
    ]


# ──────────────────────────────────────────────
# 附件下载（通过 Playwright download 事件）
# ──────────────────────────────────────────────
def download_attachments(page, item: dict, att_meta: list, save_dir: str) -> list:
    """
    导航到公告详情页，依次点击每个附件的"下载"按钮，
    通过 Playwright 的 download 事件捕获文件并保存。

    返回 [{filename, local_path}, ...] 表示成功下载的附件。
    """
    if not att_meta:
        return []

    detail_url = build_detail_url(item["id"], item["uuid"])
    os.makedirs(save_dir, exist_ok=True)

    # 导航到详情页
    page.goto(detail_url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)

    # 找到所有下载按钮
    download_links = page.locator(
        ".cmcc-upload-file-file-list-horizontal-file"
    )
    count = download_links.count()

    downloaded = []
    for idx in range(count):
        file_item = download_links.nth(idx)
        btn = file_item.locator("a")
        if btn.count() == 0:
            continue

        # 读取文件名
        name_el = file_item.locator(".cmcc-upload-file-file-name")
        filename = name_el.text_content().strip() if name_el.count() else f"attachment_{idx}"

        save_path = os.path.join(save_dir, filename)

        try:
            with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as dl_info:
                btn.first.click()
            download = dl_info.value
            download.save_as(save_path)
            downloaded.append({"filename": filename, "local_path": save_path})
            print(f"           ✓ {filename}")
        except PwTimeout:
            print(f"           ✗ {filename} (下载超时)")
        except Exception as e:
            print(f"           ✗ {filename} ({e})")

    return downloaded


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
        print("[1/6] 启动浏览器...")
        browser = p.chromium.launch(
            headless=True,
            **({"executable_path": CHROMIUM_PATH} if CHROMIUM_PATH else {}),
        )
        # accept_downloads=True 是默认值，但显式声明更清晰
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # 访问目标页面（建立 session / cookie）
        page.goto(
            f"{BASE_URL}/#/biddingHall",
            wait_until="networkidle",
            timeout=30000,
        )

        # 2. 获取列表
        print(f"[2/6] 获取前 {PAGES_TO_SCRAPE} 页列表...")
        all_items = []
        for pg in range(1, PAGES_TO_SCRAPE + 1):
            records = fetch_list(page, pg)
            for r in records:
                r["_page"] = pg
            all_items.extend(records)
            print(f"       第 {pg} 页: {len(records)} 条")
        print(f"       合计: {len(all_items)} 条")

        # 3. 获取详情元数据 + 附件列表
        print("[3/6] 获取详情元数据与附件列表...")
        detail_metas = []
        attachments_meta = []
        for i, item in enumerate(all_items):
            short = item.get("name", "")[:40]
            print(f"  [{i+1}/{len(all_items)}] (meta) {short}...")

            meta = fetch_detail_meta(page, item["id"], item["uuid"])
            detail_metas.append(meta)

            att = fetch_attachments_meta(page, item["uuid"])
            attachments_meta.append(att)

        # 4. 提取 PDF 正文
        print("[4/6] 提取 PDF 正文...")
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

        # 5. 下载附件文件
        print(f"[5/6] 下载附件到 {ATTACH_DIR}/ ...")
        downloaded_files = []  # 每条公告的下载结果
        items_with_att = sum(1 for a in attachments_meta if a)
        att_idx = 0
        for i, item in enumerate(all_items):
            att = attachments_meta[i]
            if not att:
                downloaded_files.append([])
                continue

            att_idx += 1
            title = item.get("name", "")
            short = title[:40]
            folder_name = safe_dirname(f"{i+1:02d}_{title}")
            save_dir = os.path.join(ATTACH_DIR, folder_name)

            print(f"  [{att_idx}/{items_with_att}] {short}...")
            dl = download_attachments(page, item, att, save_dir)
            downloaded_files.append(dl)

            # 下载完回到列表页，为下一次 API fetch 保持正确的域
            page.goto(
                f"{BASE_URL}/#/biddingHall",
                wait_until="domcontentloaded",
                timeout=15000,
            )

        # 6. 输出 CSV
        print(f"[6/6] 写入 {OUTPUT_CSV}...")
        fieldnames = [
            "页码", "单位", "标题", "项目名称",
            "发布时间", "截止时间", "详情链接",
            "附件名称", "附件本地路径", "公告正文",
        ]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, item in enumerate(all_items):
                att = attachments_meta[i]
                dl = downloaded_files[i]

                att_names = " | ".join(a["filename"] for a in att)

                # 优先用实际下载路径，没下载成功的显示空
                if dl:
                    att_paths = " | ".join(d["local_path"] for d in dl)
                else:
                    att_paths = ""

                writer.writerow({
                    "页码": item["_page"],
                    "单位": item.get("companyTypeName", ""),
                    "标题": item.get("name", ""),
                    "项目名称": detail_metas[i]["projectName"],
                    "发布时间": item.get("publishDate", ""),
                    "截止时间": detail_metas[i]["tenderSaleDeadline"],
                    "详情链接": build_detail_url(item["id"], item["uuid"]),
                    "附件名称": att_names,
                    "附件本地路径": att_paths,
                    "公告正文": (
                        pdf_texts[i][:CONTENT_MAX_LEN]
                        if pdf_texts[i]
                        else ""
                    ),
                })

        browser.close()

        # 统计
        total_dl = sum(len(d) for d in downloaded_files)
        total_att = sum(len(a) for a in attachments_meta)
        print(f"\n完成！")
        print(f"  公告记录: {len(all_items)} 条 → {OUTPUT_CSV}")
        print(f"  附件下载: {total_dl}/{total_att} 个 → {ATTACH_DIR}/")


if __name__ == "__main__":
    main()
