---
name: abap-cdc-gen
description: >
  ABAP 开发完整指南 — 覆盖四类开发任务：报表、批导、接口、接口测试。
  通过 mcp__mcp-abap-adt__ MCP Server 连接 SAP 系统（系统连接从 .env 文件读取），
  对 ABAP 对象进行创建、读取、修改、激活、搜索、测试、代码质量检查。
  编码规范涵盖命名、格式化、SELECT、错误处理、ALV、现代 ABAP 语法。
  开发前必须先查飞书标准化清单（feishu_search.py）防止重复开发。
  支持通过 REST API 脚本（rest_api_call.py）调用 SAP 函数模块。
  触发词：编写ABAP代码、修改ABAP程序、创建报表、查找SAP对象、
  调用SAP REST API、查询飞书开发清单、代码质量检查、ATC分析、
  单元测试、激活程序、语法检查、搜索函数、创建类、创建表、
  ABAP、SAP、飞书、Z-report、function module、class、CDS view。
version: 1.0.0
---

# ABAP Development Skill

## 指令

本技能的核心内容以编译格式存储在 `build/bundle.json` 中。
请按以下顺序加载并执行：

1. 读取 `build/bundle.json`，解析其中的所有指令
2. 执行 `workflow` 段中的需求纪律检查和 5 步编辑流程
3. 执行 `safety` 段中的安全规则
4. 执行 `standards` 段中的编码规范（coding/class/interface/batchinput）
5. 执行 `feishu` 段中的飞书清单查询流程
6. 执行 `rest_api` 段中的 REST API 调用流程

**不读取 bundle.json 直接使用 = 缺少完整指令，可能违规。**

---

## 核心任务

通过 `mcp__mcp-abap-adt__` MCP Server 连接 SAP 系统，系统连接由 MCP 服务的 `.env` 配置文件决定（包括 `SAP_CLIENT`、`SAP_URL` 等）。`.env` 文件修改后需要重启 MCP 服务才会生效。

> **重要**：除飞书相关操作需要在飞书验证系统验证外，其余所有 ABAP 操作（创建、读取、修改、搜索、测试等）都以 MCP 服务当前连接的 SAP 系统为准，不纠结 MANDT/CLIENT 问题。

## 开发任务选择

本技能覆盖四类 ABAP 开发任务。用户提出需求时，先判断任务类型，再按对应流程执行：

| 任务类型 | 典型需求 | 规范依据 | 关键流程 |
|----------|----------|----------|----------|
| **报表** | "创建 Z 报表"、"查询报表"、"ALV 报表" | [abap-coding.md](references/abap-coding.md)（SELECT/ALV/命名） | ①查飞书 → ②确认需求 → ③创建程序 → ④编写 SELECT+ALV → ⑤语法检查 → ⑥激活 |
| **批导** | "Excel 导入"、"BDC 录屏"、"批量创建/修改" | [abap-batchinput.md](references/abap-batchinput.md)（BDC/上传/ALV） | ①查飞书 → ②确认需求 → ③DDIC 先行 → ④创建程序 → ⑤模板下载+上传+ALV+BDC → ⑥语法检查 → ⑦激活 |
| **接口** | "创建 RFC/BAPI/REST 接口"、"接口函数" | [abap-interface.md](references/abap-interface.md)（DDIC 先行/参数规范/JSON） | ①查飞书 → ②确认需求 → ③DDIC 先行（域→数据元素→结构→表类型→I/O 结构）→ ④创建函数模块 → ⑤编写逻辑 → ⑥语法检查 → ⑦激活 → ⑧注册 ZTREST_CONF |
| **接口测试** | "调用已有接口"、"测试报文"、"REST API 调用" | [rest-api.md](references/rest-api.md)（ZTREST_CONF/UUID 幂等/参数） | ①查 api-catalog 匹配接口 → ②查 ZTREST_CONF 确认函数模块 → ③查 DDIC 结构确认参数 → ④调用脚本 → ⑤反馈结果 |

> **接口测试**与**接口开发**不同：测试是调用已有接口，开发是创建新接口。开发新接口必须先走 DDIC 先行流程，完成后再通过测试验证。

---

## 常用工具速查

### 编辑相关

| 操作 | 工具 | 关键参数 |
|------|------|----------|
| 确认存在 | `SearchObject` | object_name（支持 `Z*` 通配），可加 object_type |
| 读取源码 | `GetClass` / `GetProgram` / `GetTable` / `GetView` / `GetStructure` | class_name / program_name / table_name / view_name / structure_name |
| 写回源码 | `UpdateClass` / `UpdateProgram` / `UpdateTable` / `UpdateView` / `UpdateStructure` | source_code / ddl_code（**整段源码**，非片段）；activate 默认关 |
| 语法检查 | `CheckClass` / `CheckProgram` / `CheckTable` / `CheckView` / `CheckStructure` | 对象名 |
| 激活 | `ActivateClass` / `ActivateProgram` / `ActivateTable` / `ActivateView` / `ActivateStructure` | 对象名；多个依赖对象用 `ActivateObjects` |
| 创建对象 | `CreateClass` / `CreateProgram` / `CreateTable` / `CreateView` / `CreateStructure` | name, package_name（本地用 `$TMP`） |

### 搜索相关

| 操作 | 工具 | 关键约束 |
|------|------|----------|
| 搜索对象 | `SearchObject` | object_name 通配（如 `Z*`）；maxResults 默认 100 |
| 源码搜索 | `SearchSource` | query + packages（按包扫描源码） |
| 对象信息 | `GetObjectInfo` / `DescribeByList` | parent_type, parent_name |
| 引用查找 | `GetWhereUsed` | object_name + object_type |

### 代码质量

| 操作 | 工具 | 关键约束 |
|------|------|----------|
| ATC 检查 | `RunAtc` | object_name + object_type；发现 findings 后先 `GetAtcWorklist` / `GetFixProposals` 获取详情再修复 |
| 单元测试 | `RunUnitTest` | tests（container_class + test_class） |
| 编写测试 | `UpdateLocalTestClass` | 在类的 testclasses include 写 LTCL_ 测试类 |
| 数据查询 | `GetSqlQuery` | sql_query + row_number（默认 100） |

### 其他

| 操作 | 工具 |
|------|------|
| 会话信息 | `GetSession` |
| 版本历史 | `GetObjectRevisions` |
| 批量读取 | `GetIncludesList` / `GetObjectsList` |
| 传输管理 | `GetTransport` / `ListTransports`（**禁止** `ReleaseTransport` / `DeleteTransport`） |
| 执行程序 | `RuntimeRunClass` / `RuntimeRunProgram` |
| Dump 分析 | `RuntimeListFeeds`（dumps）/ `RuntimeGetDumpById` |
| 性能追踪 | `RuntimeListProfilerTraceFiles` / `RuntimeAnalyzeProfilerTrace` |

---

## 相关文件

| 文件 | 说明 |
|------|------|
| [build/bundle.json](build/bundle.json) | 编译后的完整指令（编码规范、工作流、安全规则等） |
| [scripts/feishu_search.py](scripts/feishu_search.py) | 飞书搜索脚本 |
| [scripts/rest_api_call.py](scripts/rest_api_call.py) | REST API 调用脚本 |
| [feishu_config.json](feishu_config.json) | 飞书配置（随包提交） |
| [references/api-catalog.md](references/api-catalog.md) | 接口目录 — 接口匹配、参数说明、JSON 示例 |

> **接口开发完成后的 ZTREST_CONF 注册**：每个接口函数模块开发完成后，自动检查是否需要注册到 ZTREST_CONF。前提是 ZGL001 记录必须已存在（参见 [abap-interface.md](references/abap-interface.md#6-接口开发完成后提示注册-zrest_conf)）。

---

## 强制规则（违反即停止）

**所有 `references/*.md` 中的规范都是强制规则，必须严格遵守。** 包括但不限于：

| 文件 | 强制范围 |
|------|----------|
| [abap-coding.md](references/abap-coding.md) | 命名、格式化、SELECT、错误处理、ALV、现代 ABAP 语法等全部编码规范 |
| [abap-class.md](references/abap-class.md) | 类定义、方法签名、继承、接口实现等全部类规范 |
| [abap-interface.md](references/abap-interface.md) | 函数模块签名、参数、异常、DDIC 先行、接口结构模板、JSON 处理等全部接口规范 |
| [abap-batchinput.md](references/abap-batchinput.md) | BDC 录屏、CALL TRANSACTION、消息处理等全部 BDC 规范 |
| [safety.md](references/safety.md) | 安全规则、生产系统保护、数据保护等全部安全规范 |
| [rest-api.md](references/rest-api.md) | REST API 调用格式、ZTREST_CONF 配置、UUID 幂等等全部 API 规范 |
| [api-catalog.md](references/api-catalog.md) | 接口目录 — 接口编号与业务映射、触发关键词、参数必填、JSON 示例 |

## REST API 调用流程

当用户提出业务需求（如"创建采购订单"）时，按以下流程操作：

1. **匹配接口**：查阅 [api-catalog.md](references/api-catalog.md) 的"自然语言 → 接口匹配指南"，找到对应接口
2. **查看参数**：查阅该接口详情的参数说明，确认必填字段
3. **向用户提问**：列出需要用户提供的必填参数值
4. **调用接口**：使用 `rest_api_call.py` 脚本组装 JSON 并调用
5. **反馈结果**：告知用户调用结果（成功/失败，单据号等）

> 接口编号（ZNUMB）只是路由编号，实际业务由函数模块决定。同一 ZNUMB 在不同系统可能映射不同的函数模块，以当前连接系统的 ZTREST_CONF 配置为准。