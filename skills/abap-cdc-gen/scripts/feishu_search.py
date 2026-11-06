#!/usr/bin/env python3
"""Search Feishu Bitable for ABAP development checklist records.

Usage:
  python feishu_search.py <keyword> [max_results]
  python feishu_search.py <keyword> --offline     # search local cache only
  python feishu_search.py <keyword> --sync         # sync first, then search

  Config: feishu_config.json
  Token cache: .feishu_token_cache.json (gitignored)
  Local cache: feishu_checklist.md (synced via feishu_sync.py)
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

# Paths relative to the skill folder (本技能目录)
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(SKILL_DIR, "feishu_config.json")
TOKEN_FILE = os.path.join(SKILL_DIR, ".feishu_token_cache.json")
CACHE_FILE = os.path.join(SKILL_DIR, "feishu_checklist.md")


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


def search_records(keyword, max_results=15):
    """Search Bitable records by keyword across all search fields."""
    config = load_config()
    token = get_token(config["app_id"], config["app_secret"])

    base = config["base_token"]
    table = config["table_id"]
    search_fields = config["search_fields"]

    # Fetch all records
    all_records = []
    page_token = None
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{base}/tables/{table}/records?page_size=100"
        if page_token:
            url += f"&page_token={page_token}"
        data = api_get(url, token)
        items = data.get("data", {}).get("items", [])
        all_records.extend(items)
        if not data.get("data", {}).get("has_more"):
            break
        page_token = data.get("data", {}).get("page_token")

    # Search
    keyword_lower = keyword.lower()
    results = []
    for record in all_records:
        fields = record.get("fields", {})
        score = 0
        matched_fields = []

        for fname in search_fields:
            value = str(fields.get(fname, "")).lower()
            if keyword_lower in value:
                if value == keyword_lower:
                    score += 10
                elif value.startswith(keyword_lower):
                    score += 5
                else:
                    score += 2
                matched_fields.append(fname)

        if score > 0:
            results.append({
                "record_id": record["record_id"],
                "score": score,
                "matched_fields": matched_fields,
                "fields": fields,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


def format_results(results, keyword, source="API"):
    """Format search results for display."""
    if not results:
        return f"未找到与「{keyword}」相关的开发清单记录。（数据源: {source}）"

    lines = [f"[Search] 「{keyword}」在开发清单中找到 {len(results)} 条相关记录（数据源: {source}）：\n"]
    for i, r in enumerate(results, 1):
        f = r["fields"]
        prog = f.get("程序名", "-")
        desc = f.get("开发程序描述", "-")
        tcode = f.get("事务代码", "-")
        func = f.get("函数名", "-")
        cat1 = f.get("一级分类", "-")
        cat2 = f.get("二级分类", "-")
        dev_type = f.get("开发类型", "-")
        type_desc = f.get("类型描述", "-")
        req = f.get("开发申请", "-")

        lines.append(f"--- 第 {i} 条 (匹配度: {r['score']}) ---")
        lines.append(f"  程序名:     {prog}")
        lines.append(f"  描述:       {desc}")
        lines.append(f"  事务代码:   {tcode}")
        lines.append(f"  函数名:     {func}")
        lines.append(f"  一级分类:   {cat1} - {f.get('一级分类描述', '')}")
        lines.append(f"  二级分类:   {cat2} - {f.get('二级分类描述', '')}")
        lines.append(f"  开发类型:   {dev_type} - {type_desc}")
        lines.append(f"  开发申请:   {req}")
        lines.append(f"  匹配字段:   {', '.join(r['matched_fields'])}")
        lines.append("")

    return "\n".join(lines)


def parse_markdown_cache():
    """Parse cached markdown file into records list.
    Returns (records, sync_time) or (None, None) if cache not found.
    """
    if not os.path.exists(CACHE_FILE):
        return None, None

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract sync time
    sync_match = re.search(r"\*\*同步时间\*\*:\s*(.+?)\s*$", content, re.MULTILINE)
    sync_time = sync_match.group(1) if sync_match else "未知"

    # Extract table rows (skip header and separator)
    lines = content.split("\n")
    records = []
    in_table = False
    columns = []

    for line in lines:
        line = line.strip()
        if line.startswith("| 程序名 |"):
            in_table = True
            columns = [c.strip() for c in line.split("|")[1:-1]]
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("| ") and " | " in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) == len(columns):
                field_map = {
                    "程序名": "程序名",
                    "描述": "开发程序描述",
                    "事务代码": "事务代码",
                    "函数名": "函数名",
                    "一级分类": "一级分类",
                    "二级分类": "二级分类",
                    "开发类型": "开发类型",
                    "类型描述": "类型描述",
                    "开发申请": "开发申请",
                }
                fields = {}
                for col, cell in zip(columns, cells):
                    key = field_map.get(col, col)
                    fields[key] = cell if cell != "-" else ""
                records.append({"fields": fields})
        elif in_table and not line.startswith("|"):
            break

    return records, sync_time


def search_offline(keyword, max_results=15):
    """Search local markdown cache for matching records."""
    records, sync_time = parse_markdown_cache()
    if records is None:
        print("[Warning] 本地缓存不存在，请先运行 feishu_sync.py 同步数据。")
        print("[Fallback] 尝试在线搜索...")
        return None, None

    keyword_lower = keyword.lower()
    search_fields = ["程序名", "开发程序描述", "事务代码", "函数名", "一级分类", "二级分类"]

    results = []
    for record in records:
        fields = record.get("fields", {})
        score = 0
        matched_fields = []

        for fname in search_fields:
            value = str(fields.get(fname, "")).lower()
            if keyword_lower in value:
                if value == keyword_lower:
                    score += 10
                elif value.startswith(keyword_lower):
                    score += 5
                else:
                    score += 2
                matched_fields.append(fname)

        if score > 0:
            results.append({
                "record_id": "",
                "score": score,
                "matched_fields": matched_fields,
                "fields": fields,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results], sync_time


def main():
    if len(sys.argv) < 2:
        print("Usage: python feishu_search.py <keyword> [max_results] [--offline|--sync]")
        print("  --offline  搜索本地缓存 feishu_checklist.md")
        print("  --sync     先同步最新数据，再在线搜索")
        print("  (default)   在线搜索（飞书 API）")
        sys.exit(1)

    # Parse flags
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    keyword = args[0] if args else ""
    max_results = int(args[1]) if len(args) > 1 else 15

    use_offline = "--offline" in flags
    use_sync = "--sync" in flags

    if use_sync:
        print("[Sync] 正在同步最新数据...")
        import subprocess
        sync_script = os.path.join(SKILL_DIR, "scripts", "feishu_sync.py")
        result = subprocess.run([sys.executable, sync_script], capture_output=True, text=True)
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            sys.exit(1)

    if use_offline:
        results, sync_time = search_offline(keyword, max_results)
        if results is None:
            # Fallback to online
            try:
                results = search_records(keyword, max_results)
                print(format_results(results, keyword, "API (fallback)"))
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)
            return
        source = f"本地缓存 (同步于 {sync_time})"
        print(format_results(results, keyword, source))
        return

    try:
        results = search_records(keyword, max_results)
        print(format_results(results, keyword, "API"))
    except urllib.error.HTTPError as e:
        print(f"Feishu API Error: {e.code} - {e.reason}")
        # Fallback to offline
        print("[Fallback] 尝试本地缓存搜索...")
        results, sync_time = search_offline(keyword, max_results)
        if results is not None:
            source = f"本地缓存 (同步于 {sync_time})"
            print(format_results(results, keyword, source))
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()