---
name: rest-api
description: SAP REST API 调用规范 — ZTREST_CONF 配置、请求格式、UUID 幂等、脚本调用方式
---

# SAP REST API 调用规范

> 下文脚本路径以 Claude Code 安装目录 `~/.claude/skills/abap-cdc-gen/` 为例；Codex 用户把 `.claude` 换成 `.codex`。

## 核心原则

**通过统一入口 `/sap/bc/rest/api` 调用 SAP 函数模块。所有接口必须在 ZTREST_CONF 表中配置后才能调用。**

**边界条件** — 以下情况不要调用：
- 接口未在 ZTREST_CONF 中配置 → 调用会失败，先确认 ZNUMB 是否已注册
- 密码未提供 → 向用户索要密码，不要使用明文存储的密码
- 生产系统 → 确认是否为测试数据，避免影响生产

---

## 架构

```
请求方 → POST /sap/bc/rest/api → REST Handler → ZTREST_CONF(查ZNUMB→ZFNAME) → 动态调用函数模块
```

- **ZTREST_CONF**：接口配置表，只有在此表配置的接口才能被调用
- **ZNUMB**：接口编号（主键），映射到函数模块名 ZFNAME
- 接口在 ZTREST_CONF 中配置后，通过统一入口 `/sap/bc/rest/api` 调用

---

## 请求格式

- **入口**：`POST https://{host}:{port}/sap/bc/rest/api?sap-client={client}`
- **认证**：HTTP Basic Auth
- **Content-Type**：`application/json`

### 请求体字段

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `ZNUMB` | 是 | CHAR30 | 接口编号，对应 ZTREST_CONF.ZNUMB，REST Handler 据此查找函数模块 |
| `UUID` | 是 | CHAR32 | 32位随机数，幂等键 |
| `FSYSID` | 是 | CHAR | 调用系统标识，如 `BEATBOT` |
| `FUNCTION` | 否 | CHAR30 | 函数模块名，由 ZTREST_CONF.ZFNAME 决定，传了用于校验 |
| `REQ` | 否 | Object | 业务参数，结构取决于具体接口 |

> **ZNUMB 是核心标识**：REST Handler 通过 ZNUMB 在 ZTREST_CONF 中查找对应的函数模块名（ZFNAME），然后动态调用。只有 ZTREST_CONF 中已配置的接口才能被调用。

### UUID 幂等规则

**为什么需要 UUID**：防止网络重试导致重复调用，保证一次业务操作只执行一次。

- **调用成功**：UUID 不可重复使用，下次必须换新的
- **调用失败**：可以沿用同一个 UUID 重试，直到成功为止

**UUID 幂等由 ZCL_REST_API 框架层处理**，在 inbound 方法中实现。函数模块内部**不需要**处理 UUID 幂等校验，**禁止**在函数模块中自行实现 UUID 幂等检查。
- 每次调用前自动生成新的 32 位随机 UUID

### 示例请求

```json
{
  "ZNUMB": "SDI008",
  "UUID": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
  "FSYSID": "BEATBOT",
  "REQ": {
    "KUNNR": "1000",
    "ZRDAT": "20250207"
  }
}
```

---

## ZTREST_CONF 配置表

| 字段 | 类型 | 说明 |
|------|------|------|
| `MANDT` | CLNT | 客户端 |
| `ZNUMB` | CHAR30 | 接口编号（主键） |
| `ZNAME` | CHAR | 接口名称 |
| `ZIFTY` | CHAR | 接口类型 |
| `ZISST` | CHAR | 接口状态 |
| `ZFNAME` | CHAR30 | 类/函数模块名 |
| `ZIPARA` | CHAR | 导入参数 |
| `ZOPARA` | CHAR | 导出参数 |
| `TSYSID` | CHAR | 目标系统 |
| `ZURLP` | CHAR | URL 路径 |

> 只有在此表中配置了 `ZNUMB` 的接口，才能通过 REST API 被调用。

---

## 系统连接信息

系统连接以 MCP 服务的 `.env` 配置文件为准，包括 `SAP_CLIENT`、`SAP_URL` 等。`.env` 文件修改后需要重启 MCP 服务才会生效。MCP 服务连接配置可在 `~/.claude.json` 中的 `mcpServers.mcp-abap-adt` 下查看。用户可通过 `GetSession` 确认当前连接的 SAP 系统。

密码不存储在文件中，通过 `--password` 参数或环境变量 `SAP_PASSWORD` 传入。

---

## 调用方式

### 方式一：使用脚本（推荐）

```bash
# 连接信息自动从 mcp-abap-adt 的 .env 文件读取
python "~/.claude/skills/abap-cdc-gen/scripts/rest_api_call.py" \
  --function ZFM_SDI008 \
  --znumb SDI008 \
  --password <密码> \
  --req '{"KUNNR":"","ZRDAT":"20250207"}'
```

**参数说明**：

| 参数 | 说明 |
|------|------|
| `--connection` | 可选，连接名（默认从 `.env` 自动读取） |
| `--function` | 函数模块名 |
| `--znumb` | 接口编号 |
| `--password` | SAP 密码（也可用环境变量 `SAP_PASSWORD`） |
| `--req` | 业务参数 JSON |
| `--uuid` | 可选，复用上次失败的 UUID 重试 |
| `--pretty` | 格式化输出（默认启用） |

### 方式二：直接 curl

```bash
curl -k -u "2657:password" -X POST -H "Content-Type: application/json" \
  -d '{"ZNUMB":"SDI008","UUID":"<32位随机>","FSYSID":"BEATBOT","REQ":{...}}' \
  "https://WHS4APP01.hand-china.com:44300/sap/bc/rest/api?sap-client=120"
```

### Before/After 示例

```bash
# ❌ 错误 — 硬编码 UUID，重复使用
curl ... -d '{"ZNUMB":"SDI008","UUID":"fixed-uuid-12345","FSYSID":"BEATBOT","REQ":{...}}'

# ✅ 正确 — 每次生成新 UUID，用脚本管理幂等
python "~/.claude/skills/abap-cdc-gen/scripts/rest_api_call.py" --znumb SDI008 --password xxx --req '{...}'
# 脚本自动生成新 UUID，失败时可通过 --uuid 沿用上次的重试
```

---

## ZGL001 — 接口平台配置维护接口

> 通过 REST API 维护 ZTREST_CONF 配置表（新增/更新），无需使用 SM30。

### 注册信息

| 字段 | 值 |
|------|-----|
| ZNUMB | ZGL001 |
| ZNAME | 接口平台配置维护 |
| ZIFTY | M |
| ZISST | X |
| ZFNAME | ZFM_GLI001 |
| ZIPARA | ZSGLI001_REQ |
| ZOPARA | ZSREST_OUT |

### 请求报文

```json
{
  "ZNUMB": "ZGL001",
  "UUID": "<32位随机>",
  "FSYSID": "BEATBOT",
  "REQ": {
    "ZNUMB": "ZGL001",
    "ZNAME": "接口平台配置维护",
    "ZIFTY": "M",
    "ZISST": "X",
    "ZFNAME": "ZFM_GLI001",
    "ZIPARA": "ZSGLI001_REQ",
    "ZOPARA": "ZSREST_OUT"
  }
}
```

### 字段说明

| REQ 字段 | 对应表字段 | 说明 |
|----------|-----------|------|
| ZNUMB | ZTREST_CONF-ZNUMB | 接口编号（主键，**必填**） |
| ZNAME | ZTREST_CONF-ZNAME | 接口名称 |
| ZIFTY | ZTREST_CONF-ZIFTY | 接口类型 |
| ZISST | ZTREST_CONF-ZISST | 接口状态（新增时默认 X） |
| ZFNAME | ZTREST_CONF-ZFNAME | 函数模块名 |
| ZIPARA | ZTREST_CONF-ZIPARA | 导入参数结构 |
| ZOPARA | ZTREST_CONF-ZOPARA | 导出参数结构 |
| TSYSID | ZTREST_CONF-TSYSID | 目标系统 |
| ZURLP | ZTREST_CONF-ZURLP | URL 路径 |

### 行为说明

- **新增**：ZNUMB 在 ZTREST_CONF 中不存在时，执行 INSERT
- **更新**：ZNUMB 已存在时，仅更新非空字段（支持部分更新）
- 新增时 ZISST 默认为 'X'（启用）

### 调用示例

```bash
# 新增接口配置
python "~/.claude/skills/abap-cdc-gen/scripts/rest_api_call.py" \
  --function ZFM_GLI001 \
  --znumb ZGL001 \
  --password <密码> \
  --req '{"ZNUMB":"ZGL001","ZNAME":"接口平台配置维护","ZIFTY":"M","ZISST":"X","ZFNAME":"ZFM_GLI001","ZIPARA":"ZSGLI001_REQ","ZOPARA":"ZSREST_OUT"}'

# 部分更新（仅修改 ZNAME）
python "~/.claude/skills/abap-cdc-gen/scripts/rest_api_call.py" \
  --function ZFM_GLI001 \
  --znumb ZGL001 \
  --password <密码> \
  --req '{"ZNUMB":"ZGL001","ZNAME":"新接口名称"}'
```

---

## 复盘：REST API 调用全流程规则

### 1. 调用前：查清接口入参结构

**不要直接猜测请求 JSON 格式。** 必须先查 DDIC 结构，按以下顺序：

```bash
# 第 1 步：从 ZTREST_CONF 获取接口的 ZIPARA（入参结构名）
GetSqlQuery(sql_query: "SELECT ZNUMB, ZFNAME, ZIPARA, ZOPARA FROM ZTREST_CONF WHERE ZNUMB = 'AIGCI001'")

# 第 2 步：读取入参结构（REQ 层）
GetStructure(structure_name: "ZSAIGC001_REQ")
# → 看到 include zsrest_in（公共字段）+ req: zsaigc001_in

# 第 3 步：读取业务参数结构（REQ.REQ 层）
GetStructure(structure_name: "ZSAIGC001_IN")
# → 看到 iv_mode, rt_matnr, rt_werks 等字段

# 第 4 步：读取嵌套的 RANGE 表/子结构
GetStructure(structure_name: "ZSAIGC_MATNR_RANGE")
# → 看到 sign, option, low, high — 标准的 RANGE 结构
```

**关键规则**：字段名从 DDIC 的 `snake_case` 转为 `camelCase`（如 `iv_mode` → `ivMode`，`rt_matnr` → `rtMatnr`）。

### 2. 调用中：请求 JSON 组装规则

```json
{
  "ZNUMB": "AIGCI001",         // ← 接口编号（顶层字段，大写）
  "UUID": "<自动生成32位>",     // ← 脚本自动生成
  "FSYSID": "BEATBOT",         // ← 调用系统标识
  "REQ": {                     // ← 业务参数（对应 ZSxxx_IN）
    "ivMode": "02",            // ← DDIC iv_mode → camelCase ivMode
    "rtMatnr": [               // ← RANGE 表用数组
      {"sign":"I", "option":"EQ", "low":"000000001000000420"}
    ],
    "rtWerks": [
      {"sign":"I", "option":"EQ", "low":"1000"}
    ]
  }
}
```

| 规则 | 说明 | 示例 |
|------|------|------|
| **字段名 camelCase** | DDIC `snake_case` 转 `camelCase` | `iv_mode` → `ivMode` |
| **RANGE 用数组** | SIGN/OPTION/LOW/HIGH 结构 | `[{"sign":"I","option":"EQ","low":"..."}]` |
| **物料号带前导零** | SAP 内部格式，18 位 | `000000001000000420` |
| **工厂不带前导零** | 数字型，原样传 | `1000` |
| **必填参数先确认** | 查函数源码确认哪些字段必填 | 查 `GetFunctionModule` 中的校验逻辑 |

### 3. 调用后：结果解读

```python
# 脚本返回结果结构
{
  "http_status": 200,            # HTTP 状态码
  "uuid": "32位hex",             # 本次调用的 UUID
  "response": {
    "msgty": "S" / "E",          # S=成功, E=错误
    "msgtx": "查询成功！",        # 消息文本（UTF-8）
    "uuid": "...",               # 回显 UUID
    "sapnum": "...",             # 单据号（写入接口）
    "resp": [...]                # 数据表（查询接口）
  }
}
```

| HTTP 状态 | 含义 | 处理方式 |
|-----------|------|----------|
| `200` | 请求已处理 | 看 `msgty` 判断业务成功/失败 |
| `401` | 认证失败 | 检查密码 |
| `404` | 接口不存在 | 检查 ZNUMB 是否配置、SICF 服务是否激活 |
| `500` | 函数模块内部异常 | 检查函数模块语法/参数 |

### 4. 常见错误及排查

| 错误现象 | 原因 | 解决 |
|----------|------|------|
| `msgty=E` + "入参错误，工厂为必输条件" | 工厂 RANGE 未传或为空 | 补传 `rtWerks` |
| `msgty=E` + "查询失败，没有符合条件的数据" | 物料/工厂无数据，或物料号格式不对 | 确认物料号带前导零，或换物料测试 |
| `msgty=E` + "MODE入参错误" | `ivMode` 传了非法值 | 传空字符串或 `01`/`02`/`03`/`04` |
| 终端中文乱码 | 终端不支持 UTF-8 中文 | 用 `--no-pretty` 看原始 JSON |
| HTTP 200 + 空响应 | `ZTREST_CONF` 中 `ZOPARA` 与函数实际返回结构不匹配 | 检查 `ZOPARA` 是否正确 |

### 5. 安全规则

- **密码不硬编码**：通过 `--password` 传入或用环境变量 `SAP_PASSWORD`
- **UUID 幂等**：写入接口调用失败可重试（传 `--uuid` 沿用上次 UUID），查询接口不需要幂等
- **查询优先用 `ivMode=02`**（实时查询不落表），避免在数据库产生垃圾数据
- **确认是测试环境再调用**：调用前确认当前 `.env` 的 `SAP_CLIENT` 是测试客户端
```