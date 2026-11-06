---
name: abap-workflow
description: ABAP 开发工作流规则 — 5 步编辑流程、工具约束、搜索规则、代码质量检查流程
---

# ABAP 开发工作流

## 代码生成前确认清单

**用户说"生成代码"时，必须弹出以下 5 项让用户确认，缺一不可。**

### 执行流程

**第 1 步**：用 `GetSession` 确认当前 MCP 连接的 SAP 系统（系统连接由 MCP 服务的 `.env` 配置文件决定。仅飞书相关操作使用飞书验证系统验证）。

**第 2 步**：使用 `AskUserQuestion` 弹出选择面板，一次性确认以下 5 项：

| # | 项目 | 选项来源 | 选择方式 |
|---|------|----------|----------|
| 1 | 连接系统 | `GetSession` 返回值（默认 `.env` 中的 `SAP_CLIENT` 配置） | 单选 |
| 2 | 开发类型 | Report / Dialog / Interface / Smartforms / Enhancement / BatchInput | 单选 |
| 3 | 对象名称 | 用户自由输入 | 输入 |
| 4 | 请求号 | `ListTransports` 获取可修改请求 → 从中选择；`$TMP` 可选 | 选择或输入 |
| 5 | 开发包 | `$TMP` + 自定义输入 | 选择或输入 |

> **请求号选择规则**：使用 `ListTransports(modifiable_only: true)` 获取当前用户的可修改传输请求。**必须使用父请求号（Workbench 类型，如 E19K905635），不能使用子请求（Task）**。子请求作为 `transport_request` 参数传入 `Create<Type>` 会导致工具拒绝（"is not a change request"）。如果用户提供了子请求号，用 `GetTransport` 获取父请求号。<!-- 复盘：子请求不能在 Create 工具中作为 transport_request 使用 -->

**第 3 步**：5 项全部确认后，才开始生成代码。

> **Interface 类型特别注意**：选择 Interface 开发类型时，必须按 DDIC 先行流程创建——先创建域→数据元素→结构→表类型→I/O 结构（I_REQ / O_RESP），再创建函数模块，最后生成逻辑。详见 [abap-interface.md](abap-interface.md#ddic-先行开发流程)。

### 开发类型说明

| 类型 | 说明 |
|------|------|
| Report | 报表程序 |
| Dialog | 对话程序 (Module Pool) |
| Interface | 接口 (RFC/BAPI/REST/IDoc) |
| Smartforms | 表单 |
| Enhancement | 增强 (BAdI/User Exit/隐式增强) |
| BatchInput | 批输入 (BDC/Session) |

---

## 核心原则

**每一次编辑 ABAP 代码，必须按以下 5 步流程执行，不可跳步、不可合并、不可颠倒顺序。**

**边界条件** — 以下情况不要继续：
- 不明确对象是否存在 → 先 `SearchObject` 确认
- 不明确函数/方法签名 → 先 `Get<Type>` 读取
- 编辑前没读代码 → 先去读，不要猜测内容

---

## 5 步编辑流程

### 完整流程

```
步骤 1: SearchObject   → 确认对象存在（不确定时）
步骤 2: Get<Type>      → 读取完整已激活源码
步骤 3: Update<Type>   → 写回修改后的完整源码
步骤 4: Check<Type>    → 语法检查
步骤 5: Activate<Type> → 激活编译
```

`<Type>` 按对象类型替换：`Class` / `Program` / `Table` / `View` / `Structure` / `Interface` / `FunctionModule` / `DataElement` / `Domain` / `ServiceDefinition` 等。

### 为什么必须这样

| 步骤 | 为什么不可跳过 |
|------|----------------|
| 步骤 2 | `Update<Type>` 是**整段源码写回**，必须先拿到完整源码才能在其上修改；凭空写会覆盖丢失原有逻辑 |
| 步骤 4 | 跳过语法检查直接激活，会将语法错误编译进系统，后续运行时才会暴露 |
| 步骤 5 | 不激活则修改不生效，且后续其他人读取到的仍是旧代码 |

### 错误示例

```
❌ 错误流程：
SearchObject → 直接 Update<Type>（没读代码）→ Activate（没做语法检查）

❌ 为什么会失败：
没读源码就 Update，等于用凭空捏造的"完整源码"覆盖对象，原有逻辑全部丢失
```

### 正确示例

```
✅ 正确流程：
SearchObject(object_name: "ZMMR001", object_type: "PROG")
  → 确认程序存在

GetProgram(program_name: "ZMMR001")
  → 返回完整源码，在返回内容上做修改

UpdateProgram(program_name: "ZMMR001", source_code: "<修改后的完整源码>", activate: false)
  → 写回（activate 默认关）

CheckProgram(program_name: "ZMMR001")
  → 0 errors → 继续；有错误 → 修复后重新检查

ActivateProgram(program_name: "ZMMR001")
  → 激活成功
```

---

## 工具约束

### 必须使用的工具

**所有 ABAP 操作使用 `mcp__mcp-abap-adt__*` 前缀的工具。**

### 禁止使用的工具

| 禁止的工具 | 原因 |
|------------|------|
| `mcp__mcp-sd1-*` | MCP Server 已删除 |
| `mcp__mcp-abap-abap-adt-api__*` | MCP Server 已删除 |
| `setObjectSource` | 已废弃，用 `Update<Type>` 整段写回 |
| `ReleaseTransport` | 释放传输请求是不可逆操作，AI 禁止执行 |
| `DeleteTransport` | 删除传输请求是不可逆操作，AI 禁止执行 |

### 编辑规则

- **不要手动管理锁**：`Update<Type>` 自动锁定、保存、解锁
- **不要编辑后回读验证**：工具是原子操作，失败会直接报错。回读浪费时间和 token
- **整段写回，不是片段替换**：`Update<Type>` 的 `source_code` / `ddl_code` 必须是**完整的**对象源码。先在 `Get<Type>` 返回的源码上修改，再把整个结果传回
- **activate 默认关**：`Update<Type>` 默认不激活，写完先 `Check<Type>` 再 `Activate<Type>`

---

## 搜索规则

- **搜索对象前先搜飞书**：创建新对象前必须先查飞书标准化清单，防止重复开发
- **maxResults 用默认 100**：`SearchObject` 默认返回 100 条，一般够用；需要更多再显式调大
- **飞书验证系统是统一代码库的唯一真相来源**：所有飞书相关代码验证在飞书验证系统上进行，不在目标系统验证。其他 ABAP 操作以 `.env` 文件配置为准

---

## 创建对象

- 使用 `Create<Type>`（`CreateClass` / `CreateProgram` / `CreateTable` / `CreateView` / `CreateStructure` 等）创建对象
- **创建前先 `SearchObject` 确认不存在**，避免 "already exists" 错误（复盘补充）
- 本地对象用 `package_name: "$TMP"`，不需要传输请求
- **创建后立即 `Get<Type>` 读取确认**，特别是对 `include` 结构，确保字段展开正确。不要假设创建结果一定符合预期（复盘补充）

---

## 代码质量

- **ATC 检查**：用 `RunAtc` 检查；发现 findings 后**必须先 `GetAtcWorklist` 复查或用 `GetFixProposals` 获取每个 finding 的修复建议**，再修复。不要只看 finding 标题就修复——标题信息不完整
- **单元测试**：创建/修改类后运行 `RunUnitTest` 验证
- **语法检查**：每次编辑后必须运行 `Check<Type>`
- **`Check<Type>` 报错时，用 `GetAbapSemanticAnalysis` 做二次确认**：MCP 的语法检查器对跨结构字段访问（如 `i_req-uuid`、`i_req-req-znumb`）可能误报。如果语义分析确认语法正确，可以直接激活（复盘补充）
