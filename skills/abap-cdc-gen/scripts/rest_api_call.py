#!/usr/bin/env python3
"""SAP REST API 调用工具

调用 SAP 统一 REST API 入口 /sap/bc/rest/api，通过 ZNUMB 定位接口函数模块。

Usage:
  python rest_api_call.py --connection SD1_120 \\
    --function ZFM_SDI008 --znumb SDI008 --password <密码> \\
    --req '{"KUNNR":"","ZRDAT":"20250207"}'

  # 复用上次失败的 UUID 重试
  python rest_api_call.py --connection SD1_120 \\
    --function ZFM_SDI008 --znumb SDI008 --password <密码> \\
    --uuid a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 \\
    --req '{"KUNNR":"","ZRDAT":"20250207"}'

Connection config read from:
  - .vscode/settings.json (workspace level)
  - %APPDATA%/Code/User/settings.json (global level)
"""

import argparse
import json
import os
import sys
import ssl
import uuid
import urllib.request
import urllib.error

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CLAUDE_JSON = os.path.expanduser("~/.claude.json")


# ── Connection Config ────────────────────────────────────────────────────────
def load_env_file(path):
    """Parse a simple KEY=VALUE .env file, returning a dict."""
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()
    except (FileNotFoundError, IOError):
        pass
    return env


def find_mcp_env_paths():
    """Discover MCP server .env paths from ~/.claude.json mcpServers config.

    Scans every MCP server's args for --env-path=<path> or --env-path <path>
    and returns the resolved file paths.
    """
    paths = []
    try:
        with open(CLAUDE_JSON, "r", encoding="utf-8") as f:
            config = json.load(f)
        servers = config.get("mcpServers", {})
        for name, srv in servers.items():
            args = srv.get("args", [])
            for i, a in enumerate(args):
                if a.startswith("--env-path="):
                    paths.append(a.split("=", 1)[1])
                elif a == "--env-path" and i + 1 < len(args):
                    paths.append(args[i + 1])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return paths


def load_connections():
    """Load SAP connection from MCP .env files (auto-discovered from ~/.claude.json).

    Falls back to VS Code abapfs.remote for legacy setups.
    """
    connections = {}

    # 1) Auto-discover MCP .env files from ~/.claude.json mcpServers
    for env_path in find_mcp_env_paths():
        env = load_env_file(env_path)
        url = env.get("SAP_URL", "")
        client = env.get("SAP_CLIENT", "")
        username = env.get("SAP_USERNAME", "")
        if url:
            name = f"{username}@{url}" if username else url
            connections["default"] = {
                "name": "default",
                "url": url,
                "username": username,
                "client": client,
            }
            break  # use the first MCP server that has SAP_URL

    # 2) Fallback: VS Code abapfs.remote (legacy)
    vscode_ws = os.path.join(PROJECT_ROOT, ".vscode", "settings.json")
    vscode_global = os.path.join(
        os.environ.get("APPDATA", ""), "Code", "User", "settings.json"
    )
    for path in (vscode_ws, vscode_global):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            remote = data.get("abapfs.remote", {})
            for name, cfg in remote.items():
                if isinstance(cfg, dict) and "url" in cfg:
                    connections[name.lower()] = {
                        "name": name,
                        "url": cfg["url"],
                        "username": cfg.get("username", ""),
                        "client": cfg.get("client", ""),
                    }
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    return connections


def parse_url(url):
    """Parse URL into host and port. Returns (host, port)."""
    # https://host:port
    url = url.replace("https://", "").replace("http://", "")
    if ":" in url:
        host, port = url.split(":", 1)
        return host, int(port)
    return url, 443


# ── API Client ───────────────────────────────────────────────────────────────
def call_rest_api(host, port, client, username, password, function, znumb, fsysid, req_data, uuid_str=None):
    """Call the SAP REST API and return the parsed JSON response."""
    if uuid_str is None:
        uuid_str = uuid.uuid4().hex  # 32-char hex string

    body = {
        "ZNUMB": znumb,
        "UUID": uuid_str,
        "FSYSID": fsysid,
        "REQ": req_data,
    }
    if function:
        body["FUNCTION"] = function

    url = f"https://{host}:{port}/sap/bc/rest/api?sap-client={client}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    # Basic Auth
    credentials = f"{username}:{password}"
    import base64
    auth_header = base64.b64encode(credentials.encode()).decode()

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_header}",
        },
        method="POST",
    )

    # Allow self-signed certs
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            response_body = resp.read().decode("utf-8")
            return {
                "uuid": uuid_str,
                "http_status": resp.status,
                "response": json.loads(response_body),
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {
            "uuid": uuid_str,
            "http_status": e.code,
            "error": error_body,
        }
    except urllib.error.URLError as e:
        return {
            "uuid": uuid_str,
            "http_status": 0,
            "error": str(e.reason),
        }


# ── Output Formatting ────────────────────────────────────────────────────────
def format_output(result, pretty=True):
    """Format the API call result for display."""
    if not pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    resp = result.get("response", {})
    http_status = result.get("http_status", 0)

    print()
    print("=" * 60)
    print(f"  HTTP Status: {http_status}")
    print(f"  UUID: {result.get('uuid', 'N/A')}")

    if result.get("error"):
        print(f"  ERROR: {result['error']}")
        print("=" * 60)
        return

    if not resp:
        print("  (empty response)")
        print("=" * 60)
        return

    msgty = resp.get("msgty", "?")
    msgtx = resp.get("msgtx", "")
    status_icon = "OK" if msgty == "S" else "ERR" if msgty == "E" else "WARN"

    print(f"  Status: {status_icon} | {msgtx}")
    print(f"  UUID:  {resp.get('uuid', 'N/A')}")
    print("-" * 60)

    # Print response table
    resp_data = resp.get("resp", [])
    if resp_data and isinstance(resp_data, list):
        print(f"  Records: {len(resp_data)}")
        print("-" * 60)
        for i, row in enumerate(resp_data):
            if i == 0:
                # Print header
                keys = list(row.keys())
                header = "  " + " | ".join(f"{k:<16}" for k in keys)
                print(header)
                print("  " + "-" * (len(header) - 2))
            values = "  " + " | ".join(f"{str(row.get(k, '')):<16}" for k in row.keys())
            print(values)
            if i >= 50:
                print(f"  ... and {len(resp_data) - 50} more rows")
                break
    else:
        # Print all non-list fields
        for k, v in resp.items():
            if k != "resp":
                print(f"  {k}: {v}")

    print("=" * 60)
    print()


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="SAP REST API 调用工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rest_api_call.py --connection SD1_120 --function ZFM_SDI008 \\
      --znumb SDI008 --password xxx --req '{"KUNNR":"","ZRDAT":"20250207"}'
  python rest_api_call.py --connection SD1_120 --function ZFM_SDI008 \\
      --znumb SDI008 --password xxx --uuid <reuse-uuid> --req '{"KUNNR":"","ZRDAT":"20250207"}'
        """,
    )
    parser.add_argument("--connection", "-c",
                        help="连接名: SD1_120")
    parser.add_argument("--function", "-f",
                        help="函数模块名 (如 ZFM_SDI008)，可选，由 ZTREST_CONF.ZFNAME 决定")
    parser.add_argument("--znumb", "-z",
                        help="接口编号 (如 SDI008)")
    parser.add_argument("--fsysid", default="BEATBOT",
                        help="调用系统标识 (默认: BEATBOT)")
    parser.add_argument("--password", "-p", default=None,
                        help="SAP 密码 (也可用环境变量 SAP_PASSWORD)")
    parser.add_argument("--req", "-r", default="{}",
                        help="业务参数 JSON (如 '{\"KUNNR\":\"\",\"ZRDAT\":\"20250207\"}')")
    parser.add_argument("--uuid", "-u", default=None,
                        help="复用上次失败的 UUID")
    parser.add_argument("--no-pretty", action="store_true",
                        help="禁用格式化输出")
    parser.add_argument("--list-connections", action="store_true",
                        help="列出所有可用连接")
    args = parser.parse_args()

    # Load connections
    connections = load_connections()

    if args.list_connections:
        print("\nAvailable connections:")
        for name, cfg in sorted(connections.items()):
            print(f"  {name:<20} {cfg['url']}  (client={cfg['client']}, user={cfg['username']})")
        print()
        return

    # Validate required args for API call
    missing = []
    if not args.connection:
        missing.append("--connection")
    if not args.znumb:
        missing.append("--znumb")
    if missing:
        print(f"\nERROR: Missing required arguments: {', '.join(missing)}", file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)

    # Resolve connection
    conn_key = args.connection.lower()
    if conn_key not in connections:
        print(f"\nERROR: Connection '{args.connection}' not found.", file=sys.stderr)
        print("\nAvailable connections:", file=sys.stderr)
        for name, cfg in sorted(connections.items()):
            print(f"  {name:<20} {cfg['url']}  (client={cfg['client']}, user={cfg['username']})",
                  file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)

    conn = connections[conn_key]
    host, port = parse_url(conn["url"])
    username = conn["username"]
    client = conn["client"]

    # Password
    password = args.password or os.environ.get("SAP_PASSWORD")
    if not password:
        print("\nERROR: Password required. Use --password or set SAP_PASSWORD env var.",
              file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)

    # Parse request body
    try:
        req_data = json.loads(args.req)
    except json.JSONDecodeError as e:
        print(f"\nERROR: Invalid JSON in --req: {e}", file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)

    # Call API
    fn_label = args.function or "(from ZTREST_CONF)"
    print(f"\nCalling {fn_label} ({args.znumb}) on {conn['name']} "
          f"({host}:{port}, client={client}) ...", file=sys.stderr)

    result = call_rest_api(
        host=host,
        port=port,
        client=client,
        username=username,
        password=password,
        function=args.function,
        znumb=args.znumb,
        fsysid=args.fsysid,
        req_data=req_data,
        uuid_str=args.uuid,
    )

    format_output(result, pretty=not args.no_pretty)

    # Exit code based on status
    resp = result.get("response", {})
    if resp.get("msgty") == "S":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()