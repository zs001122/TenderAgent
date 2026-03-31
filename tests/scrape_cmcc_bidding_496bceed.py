"""
中国移动采购与招标网 - 招标大厅抓取脚本
抓取"正在招标"公告列表（前N页），包括：
  - 公告基本信息（标题、单位、发布时间、截止时间等）
  - 公告详情链接
  - 公告PDF正文内容（自动解码并提取文字）
  - 相关附件列表及下载链接

依赖：
  pip install pymupdf
  需要 playwright-cli 可用（已安装浏览器）

用法：
  python scrape_cmcc_bidding.py
"""

import json
import base64
import subprocess
import csv
import os
import sys
import time

try:
    import fitz  # PyMuPDF
except ImportError:
    print("请先安装 pymupdf: pip install pymupdf")
    sys.exit(1)


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
PAGES_TO_SCRAPE = 2          # 要抓取的页数
PAGE_SIZE = 20               # 每页条数（与网站一致）
BASE_URL = "https://b2b.10086.cn"
PDF_DIR = "pdfs"             # 临时PDF保存目录
OUTPUT_CSV = "中国移动招标公告.csv"
CONTENT_MAX_LEN = 5000       # CSV中公告正文最大字符数

# API 端点
API_LIST = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryList"
API_DETAIL = "/api-b2b/api-sync-es/white_list_api/b2b/publish/queryDetail"
API_FILES = "/api-b2b/api-file/file/listByAttrOnAuth"

# 附件下载链接模板
FILE_DOWNLOAD_TPL = (
    f"{BASE_URL}/api-b2b/api-file/file/download"
    "?fileId={fileId}&waterMarkFlag=N"
)


# ──────────────────────────────────────────────
# playwright-cli 封装
# ──────────────────────────────────────────────
def cli(*args, timeout=60):
    result = subprocess.run(
        ["playwright-cli", *args],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout


def run_code(js, timeout=120):
    return cli("run-code", js, timeout=timeout)


def js_eval(expr, timeout=30):
    out = cli("eval", expr, timeout=timeout)
    for line in out.splitlines():
        if line.startswith('"'):
            return line.strip().strip('"').replace('\\"', '"')
    return ""


def get_long_string(var_name):
    length_str = js_eval(f"window.{var_name}.length.toString()")
    if not length_str:
        return ""
    length = int(length_str)
    if length == 0:
        return ""
    chunk_size = 80000
    parts = []
    for start in range(0, length, chunk_size):
        end = min(start + chunk_size, length)
        chunk = js_eval(f"window.{var_name}.substring({start}, {end})")
        parts.append(chunk)
    return "".join(parts)


# ──────────────────────────────────────────────
# PDF 解码
# ──────────────────────────────────────────────
def decode_pdf_base64(b64_str, idx):
    os.makedirs(PDF_DIR, exist_ok=True)
    pdf_path = os.path.join(PDF_DIR, f"notice_{idx}.pdf")
    try:
        pdf_bytes = base64.b64decode(b64_str)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        doc = fitz.open(pdf_path)
        texts = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(texts).strip()
    except Exception as e:
        return f"[PDF解析错误: {e}]"


def build_detail_url(item_id, item_uuid):
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
    try:
        # 1. 启动浏览器
        print("[1/5] 启动浏览器...")
        cli("open", f"{BASE_URL}/#/biddingHall")
        time.sleep(3)

        # 2. 在浏览器内一次性获取两页列表
        print("[2/5] 获取列表...")
        for pg in range(1, PAGES_TO_SCRAPE + 1):
            body = json.dumps({
                "size": PAGE_SIZE, "current": pg,
                "companyType": "", "name": "",
                "publishType": "PROCUREMENT",
                "publishOneType": "PROCUREMENT",
                "sfactApplColumn5": "PC",
            })
            run_code(
                f'async (page) => {{'
                f'  const r = await page.evaluate(async () => {{'
                f'    const resp = await fetch("{API_LIST}", {{'
                f'      method:"POST", headers:{{"Content-Type":"application/json"}},'
                f'      body: JSON.stringify({body})'
                f'    }}); return await resp.text();'
                f'  }});'
                f'  await page.evaluate((d) => {{ window.__p{pg} = d; }}, r);'
                f'}}'
            )

        # 合并列表
        items = []
        for pg in range(1, PAGES_TO_SCRAPE + 1):
            raw = js_eval(f"window.__p{pg}")
            data = json.loads(raw)
            records = data.get("data", {}).get("content", [])
            for r in records:
                r["_page"] = pg
            items.extend(records)
            print(f"       第 {pg} 页: {len(records)} 条")
        print(f"       合计: {len(items)} 条")

        # 3. 在浏览器内批量获取详情meta + 附件（每批5条）
        #    详情的 noticeContent(PDF base64) 太大，单独处理
        print("[3/5] 获取详情元数据与附件...")
        detail_meta = []   # [{projectName, tenderSaleDeadline, contentType}, ...]
        attachments = []   # [[ {filename, fileId}, ... ], ...]

        for batch_start in range(0, len(items), 5):
            batch = items[batch_start:batch_start+5]
            batch_params = json.dumps([
                {"id": it["id"], "uuid": it["uuid"]} for it in batch
            ])
            bi = batch_start // 5

            run_code(
                f'async (page) => {{'
                f'  const params = {batch_params};'
                f'  const metas = []; const atts = [];'
                f'  for (const p of params) {{'
                f'    const dr = await page.evaluate(async (pp) => {{'
                f'      const r = await fetch("{API_DETAIL}", {{'
                f'        method:"POST", headers:{{"Content-Type":"application/json"}},'
                f'        body: JSON.stringify({{publishId:pp.id, publishUuid:pp.uuid,'
                f'          publishType:"PROCUREMENT", publishOneType:"PROCUREMENT"}})'
                f'      }}); return await r.json();'
                f'    }}, p);'
                f'    const d = dr.data || {{}};'
                f'    metas.push({{projectName:d.projectName||"", tenderSaleDeadline:d.tenderSaleDeadline||"", contentType:d.contentType||""}});'
                f'    const fr = await page.evaluate(async (pp) => {{'
                f'      const r = await fetch("{API_FILES}", {{'
                f'        method:"POST", headers:{{"Content-Type":"application/json"}},'
                f'        body: JSON.stringify({{attr1:"PT_VENDOR_PUBLISH", attr2:pp.uuid, attr3:"PT_VENDOR_PUBLISH_FILE", authFlag:"N"}})'
                f'      }}); return await r.json();'
                f'    }}, p);'
                f'    const files = (fr.data || []).map(function(f){{ return {{filename:f.filename||"", fileId:f.fileId||""}}; }});'
                f'    atts.push(files);'
                f'  }}'
                f'  await page.evaluate((d) => {{ window.__bm{bi} = d; }}, JSON.stringify(metas));'
                f'  await page.evaluate((d) => {{ window.__ba{bi} = d; }}, JSON.stringify(atts));'
                f'}}',
                timeout=120
            )
            bm = json.loads(js_eval(f"window.__bm{bi}"))
            ba = json.loads(js_eval(f"window.__ba{bi}"))
            detail_meta.extend(bm)
            attachments.extend(ba)
            print(f"       批次 {bi+1}/{(len(items)+4)//5}: {len(bm)} 条")

        # 4. 逐条获取PDF正文
        print("[4/5] 提取PDF正文...")
        pdf_texts = []
        for i, (item, meta) in enumerate(zip(items, detail_meta)):
            short = item.get("name", "")[:40]
            if meta["contentType"] != "pdf":
                pdf_texts.append("")
                print(f"  [{i+1}/{len(items)}] {short} (非PDF，跳过)")
                continue

            print(f"  [{i+1}/{len(items)}] {short}...")
            # 获取单条详情的 noticeContent
            run_code(
                f'async (page) => {{'
                f'  const r = await page.evaluate(async () => {{'
                f'    const resp = await fetch("{API_DETAIL}", {{'
                f'      method:"POST", headers:{{"Content-Type":"application/json"}},'
                f'      body: JSON.stringify({{publishId:"{item["id"]}", publishUuid:"{item["uuid"]}",'
                f'        publishType:"PROCUREMENT", publishOneType:"PROCUREMENT"}})'
                f'    }}); const d = await resp.json(); return (d.data||{{}}).noticeContent||"";'
                f'  }});'
                f'  await page.evaluate((d) => {{ window.__nc = d; }}, r);'
                f'}}',
                timeout=120
            )
            b64 = get_long_string("__nc")
            text = decode_pdf_base64(b64, i) if b64 else ""
            pdf_texts.append(text)

        # 5. 输出CSV
        print(f"[5/5] 写入 {OUTPUT_CSV}...")
        fieldnames = [
            "页码", "单位", "标题", "项目名称",
            "发布时间", "截止时间", "详情链接",
            "附件名称", "附件下载链接", "公告正文",
        ]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, item in enumerate(items):
                att_list = attachments[i] if i < len(attachments) else []
                att_names = " | ".join(a["filename"] for a in att_list)
                att_urls = " | ".join(
                    FILE_DOWNLOAD_TPL.format(fileId=a["fileId"])
                    for a in att_list if a["fileId"]
                )
                writer.writerow({
                    "页码": item["_page"],
                    "单位": item.get("companyTypeName", ""),
                    "标题": item.get("name", ""),
                    "项目名称": detail_meta[i]["projectName"],
                    "发布时间": item.get("publishDate", ""),
                    "截止时间": detail_meta[i]["tenderSaleDeadline"],
                    "详情链接": build_detail_url(item["id"], item["uuid"]),
                    "附件名称": att_names,
                    "附件下载链接": att_urls,
                    "公告正文": pdf_texts[i][:CONTENT_MAX_LEN] if pdf_texts[i] else "",
                })

        print(f"\n完成！共 {len(items)} 条记录已写入 {OUTPUT_CSV}")

    finally:
        cli("session-stop")


if __name__ == "__main__":
    main()
