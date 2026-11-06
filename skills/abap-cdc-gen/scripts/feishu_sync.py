#!/usr/bin/env python3
"""Sync Feishu Bitable '14.标准化清单_OP&PCE' to a local markdown file.

Usage: python feishu_sync.py [output_path]
  Default output: feishu_checklist.md
  Config: feishu_config.json
  Token cache: .feishu_token_cache.json (gitignored)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# Paths relative to the skill folder (本技能目录)
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(SKILL_DIR, "feishu_config.json")
TOKEN_FILE = os.path.join(SKILL_DIR, ".feishu_token_cache.json")
DEFAULT_OUTPUT = os.path.join(SKILL_DIR, "feishu_checklist.md")

# CST timezone
CST = timezone(timedelta(hours=8))


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_token(app_id, app_secret):
    """Get tenant access token, using cache if still valid."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            cache = json.load(f)
        if cache.get("expires_at", 0) > time.time() + 60:
            return cache["token"]

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req).read())

    token = resp["tenant_access_token"]
    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token, "expires_at": time.time() + resp.get("expire", 7200) - 300}, f)
    return token


def api_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req).read())


def fetch_all_records():
    """Fetch all records from the Bitable."""
    config = load_config()
    token = get_token(config["app_id"], config["app_secret"])

    base = config["base_token"]
    table = config["table_id"]

    all_records = []
    page_token = None
    page_count = 0
    while True:
        page_count += 1
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{base}/tables/{table}/records?page_size=100"
        if page_token:
            url += f"&page_token={page_token}"
        data = api_get(url, token)
        items = data.get("data", {}).get("items", [])
        all_records.extend(items)
        if not data.get("data", {}).get("has_more"):
            break
        page_token = data.get("data", {}).get("page_token")

    return all_records


def escape_md(text):
    """Escape pipe and newline characters for markdown table cells."""
    if text is None:
        return "-"
    return str(text).replace("|", "\\|").replace("\n", " ")


def generate_markdown(records):
    """Generate markdown table from records."""
    now_str = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")

    # Define columns and their field keys
    columns = [
        ("程序名", "程序名"),
        ("描述", "开发程序描述"),
        ("事务代码", "事务代码"),
        ("函数名", "函数名"),
        ("一级分类", "一级分类"),
        ("二级分类", "二级分类"),
        ("开发类型", "开发类型"),
        ("类型描述", "类型描述"),
        ("开发申请", "开发申请"),
    ]

    lines = []
    lines.append(f"# 飞书开发清单")
    lines.append(f"")
    lines.append(f"> **数据源**: 飞书多维表格 - 14.标准化清单_OP&PCE")
    lines.append(f"> **同步时间**: {now_str}")
    lines.append(f"> **记录总数**: {len(records)}")
    lines.append(f"> **自动生成**: `feishu_sync.py`")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Table header
    header = "| " + " | ".join(c[0] for c in columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    lines.append(header)
    lines.append(separator)

    # Table rows
    for record in records:
        fields = record.get("fields", {})
        row = "| " + " | ".join(escape_md(fields.get(key, "-")) for _, key in columns) + " |"
        lines.append(row)

    lines.append("")
    lines.append(f"---")
    lines.append(f"*共 {len(records)} 条记录，最后同步于 {now_str}*")

    return "\n".join(lines)


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT

    print(f"[Sync] Fetching all records from Feishu Bitable...")
    try:
        records = fetch_all_records()
        print(f"[Sync] Fetched {len(records)} records.")

        markdown = generate_markdown(records)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"[Sync] Written to {output_path}")
        print(f"[Sync] Done — {len(records)} records synced at {datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S CST')}")

    except urllib.error.HTTPError as e:
        print(f"[Sync] Feishu API Error: {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Sync] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()