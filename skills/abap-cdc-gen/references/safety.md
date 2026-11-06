---
name: safety
description: ABAP 安全规则 — 激活安全、数据安全、编辑安全、传输安全
---

# ABAP 安全规则

## 核心原则

**安全优先于效率。任何可能破坏数据或系统的操作，必须先确认再执行。**

## 激活安全

### 规则

**永远不要跳过语法检查直接激活。** 未经 `Check<Type>` 检查的代码可能包含语法错误，激活后编译进系统，运行时才会暴露。

```text
# ❌ 错误 — 编辑后直接激活
UpdateProgram(program_name: "ZMMR001", source_code: "...", activate: true)

# ✅ 正确 — 先检查再激活
UpdateProgram(program_name: "ZMMR001", source_code: "...", activate: false)
  → CheckProgram(program_name: "ZMMR001")     # 语法检查
  → ActivateProgram(program_name: "ZMMR001")  # 激活
```

### 为什么

- 语法错误编译进系统后，运行时才会报错，排查困难
- 依赖该对象的其他对象可能因此被连带影响
- 语法检查是免费的，跳过它没有任何收益

### 不激活的对象

| 对象类型 | 策略 |
|----------|------|
| SAP 标准对象（非 Z/Y 开头） | **不激活**，除非用户明确要求 |
| 用户自己的 Z/Y 对象 | 语法检查通过后激活 |

---

## 数据安全

### 规则

**数据查询有上限，禁止绕过。**

| 约束 | 说明 |
|------|------|
| `GetSqlQuery` 的 `row_number` 默认 100 | 查询上限，不绕过 |
| 大表必须加 WHERE | MSEG、MKPF、BSEG 等表必须加 WHERE 条件限制结果集 |
| 生产表查询谨慎 | 只查必要字段，不用 `SELECT *` 拖全表 |

```sql
-- ❌ 错误 — 无 WHERE 全表查询
SELECT * FROM mseg

-- ✅ 正确 — WHERE 限制 + 行数上限
SELECT mblnr, zeile, matnr FROM mseg WHERE mblnr = '4900000001'
```

### 全表查询与 MANDT 条件

**查任何 SAP 表时，SELECT 语句必须加 `mandt = sy-mandt` 条件。** `sy-mandt` 由 ADT 请求中 `?sap-client=` 参数决定（来自 `.env` 的 `SAP_CLIENT`），不是硬编码。

```sql
-- ❌ 错误 — 不加 MANDT 可能读到缓冲中的过时数据
SELECT znumb, zfname FROM ztrest_conf ORDER BY znumb

-- ✅ 正确 — 加 MANDT 确保读当前客户端的最新数据
SELECT znumb, zfname FROM ztrest_conf WHERE mandt = sy-mandt ORDER BY znumb
```

> **为什么必须加**：全表查询可能命中 SAP 表缓冲，返回过时数据。`mandt = sy-mandt` 迫使 Open SQL 绕过缓冲直接读数据库。按主键查单条记录时也要加，保持习惯一致。

### 为什么

- SAP 生产表数据量巨大（BSEG 可达千万行），不加限制会导致超时甚至系统过载
- `row_number` 是强制安全措施，不是可选建议

---

## 编辑安全

### 规则

**编辑前必须读取，编辑后不验证。**

| 规则 | 为什么 |
|------|--------|
| 修改前必须 `Get<Type>` 读取完整源码 | `Update<Type>` 是整段写回，不读取就编辑会覆盖丢失原有逻辑 |
| 编辑后不要回读验证 | 工具是原子操作，失败直接报错。回读浪费时间和 token |
| 写回的 `source_code` 必须完整 | 在 `Get<Type>` 返回的源码上修改，再把完整结果传回 |

```text
# ❌ 错误 — 没读代码就 Update，凭空捏造"完整源码"
UpdateProgram(
  program_name: "ZMMR001",
  source_code: "REPORT zmmr001.\n  WRITE 'hello'."   # 猜测的内容，覆盖丢失原有逻辑
)

# ✅ 正确 — 先读完整源码，修改后再写回
# 1. GetProgram(program_name: "ZMMR001") 返回完整源码
# 2. 在返回的源码上做修改
# 3. UpdateProgram(program_name: "ZMMR001", source_code: "<修改后的完整源码>", activate: false)
```

- 不要手动管理锁：`Update<Type>` 自动锁定、保存、解锁
- 激活前必须 `Check<Type>` 通过

---

## 传输安全

### 规则

| 场景 | 策略 |
|------|------|
| 本地对象（`$TMP`） | 不需要传输请求 |
| 自定义包（ZMM01 等） | 用户管理传输分配，不主动创建传输 |
| 创建传输请求 | 除非用户明确要求，否则不创建 |
| **释放传输请求** | **禁止** — 不可逆操作，释放后请求无法修改 |
| **删除传输请求** | **禁止** — 不可逆操作，可能影响已分配的对象 |

### 禁止使用的工具

| 工具 | 原因 |
|------|------|
| `ReleaseTransport` | 释放传输请求是不可逆操作，释放后请求无法再修改。AI 不应执行此操作。 |
| `DeleteTransport` | 删除传输请求可能导致对象丢失或传输链断裂。AI 不应执行此操作。 |

### 为什么

- 传输请求涉及跨系统变更，创建不当会造成未授权对象进入生产系统
- 传输管理是用户的职责，AI 不应越权操作
