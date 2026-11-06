---
name: abap-interface
description: ABAP 函数模块开发规范 — 命名、参数、异常、RFC、BAPI、查询接口、写入接口、JSON处理、动态调用、文档
---

# ABAP 函数模块规范

> **需求文档模板**：[abap-interface-req-template.md](abap-interface-req-template.md) — 开发前使用此模板收集需求，可避免信息不全导致的反复确认。

## 目录

- [核心要求](#核心要求)
  - [接口函数模块整体流程](#接口函数模块整体流程)
  - [接口类型分类](#接口类型分类)
  - [DDIC 先行开发流程](#ddic-先行开发流程)
- [写入接口](#写入接口)
  - [接口函数模块模板（写入接口）](#接口函数模块模板写入接口)
  - [写入接口进阶模式](#写入接口进阶模式)
- [查询接口](#查询接口)
  - [查询接口模板](#查询接口模板)
  - [查询接口进阶模式](#查询接口进阶模式)
- [通用规范](#通用规范)
  - [命名规范](#命名规范)
  - [函数结构](#函数结构)
  - [参数规范](#参数规范)
  - [异常处理](#异常处理)
  - [RFC 函数模块](#rfc-函数模块)
  - [函数模块文档](#函数模块文档)
  - [JSON 处理与 REST 接口](#json-处理与-rest-接口)
- [禁止事项](#禁止事项)

---

## 核心要求

**所有 ABAP 函数模块必须遵循以下规范。通用编码规范（命名、SELECT、注释等）见 [abap-coding.md](abap-coding.md)。**

### 接口结构模板规则（强制）

> 此规则不可跳过。生成代码前必须逐项确认，不符合模板则停止并修正。

所有 REST API 接口的输入结构必须采用**两层结构**模式：

```
ZSxxx_REQ（顶层请求结构）
  ├── include : ZSREST_IN    ← 公共字段（UUID, ZNUMB, FSYSID）
  └── req     : ZSxxx_IN     ← 业务数据字段
```

**不允许创建扁平结构**（即所有字段直接平铺在顶层 REQ 中）。

**结构创建前检查清单**（必须逐项确认）：

```
[ ] 是否创建了两个结构（ZSxxx_IN + ZSxxx_REQ）？
[ ] ZSxxx_IN 是否只包含业务字段（不含 ZSREST_IN）？
[ ] ZSxxx_REQ 是否包含 include : zsrest_in？
[ ] ZSxxx_REQ 是否包含 req 字段指向 ZSxxx_IN？
[ ] 是否已经确认过项目中已有的类似接口结构（如 ZSMMI009_REQ）？
```

> 不符合模板的场景需要先与用户确认再动手，不能自行假设"这个接口简单，不需要两层"。

### 复盘补充规则

以下规则来自项目复盘，在接口开发中必须遵守：

#### 1. 创建结构前先查已有接口

在创建 DDIC 结构前，先搜索项目中已有的类似接口结构作为参考（如 `ZSMMI009_REQ`），确认模式后再动手，不要凭经验假设。

#### 2. 创建后立即验证结构

创建结构（特别是带 `include` 的结构）后，立即用 `GetStructure` 读取确认字段展开正确。不要假设 `CreateStructure` 的结果一定符合预期——`include` 的字段展开、字段顺序、类型都需要验证。

#### 3. 创建函数模块前先确认父请求号

使用 `ListTransports` 获取用户的可修改传输请求，确认父请求号（类型为 Workbench 的开发/修改请求）。**不要使用子请求（Task）作为 CreateFunctionModule 的 transport_request 参数**。

#### 4. 先查消息类再引用

使用 `MESSAGE xxx(yyy)` 前，先通过 `GetMessageClass` 或 `GetSqlQuery` 查询消息类中已有的消息号，确保引用的消息号存在。

#### 5. 鸡和蛋预判

如果创建的接口是用于维护 ZTREST_CONF 配置表的，必须在创建函数模块的同时预判：该接口需要先注册到 ZTREST_CONF 才能被调用。此时需要：
- 告知用户这个情况
- 提供临时插入配置记录的方案（临时 ABAP 程序或 SM30）

#### 6. 接口开发完成后提示注册 ZTREST_CONF

每个接口函数模块开发完成后，自动检查是否需要注册到 ZTREST_CONF：

```
接口开发完成
  │
  ├── 是否需要注册到 ZTREST_CONF？
  │     ├── 否 → 结束
  │     └── 是 → 继续
  │
  ├── ZGL001（配置维护接口）是否已注册？
  │     ├── 否 → 先插入 ZGL001 记录（临时程序）
  │     └── 是 → 继续
  │
  └── 插入新接口配置记录到 ZTREST_CONF
```

**前提条件**：ZGL001 记录必须已存在，否则无法通过 REST API 维护 ZTREST_CONF。首次使用 ZGL001 时，需要通过 SM30 或临时 ABAP 程序手动插入。

#### 7. 接口开发完成后自动生成测试报文并调用

每个接口函数模块注册到 ZTREST_CONF 后，自动生成测试报文并调用 REST API 进行验证：

```
ZTREST_CONF 注册完成
  │
  ├── 收集测试数据
  │     ├── 从接口结构（ZSxxx_IN）中提取字段清单
  │     ├── 字段含义不清楚的，向用户提问
  │     └── 生成测试报文 JSON（用示例数据填充）
  │
  ├── 调用 REST API
  │     └── rest_api_call.py --connection SD1_120 --znumb ZGL001 --function ZFM_GLI001 --req '{...}'
  │
  └── 验证结果
        ├── msgty = 'S' → 测试通过
        └── msgty = 'E' → 分析错误，修复后重新测试
```

**测试数据生成规则**：
- 必填字段用示例值（如 `'TEST001'`、`'X'`、`'测试描述'`）
- 选填字段可以省略（不传）
- 字段含义不明确的，向用户提问确认后再填充
- 测试完成后提示用户清理测试数据（如适用）

### 接口函数模块整体流程

接口函数模块按业务类型分为**查询接口**和**写入接口**，流程不同：

```
接口函数模块
│
├── 查询接口（只读）
│   ├── 1. 参数转换为 RANGE（可选过滤）
│   ├── 2. SELECT 查询数据
│   ├── 3. 检查结果 → 设置 MSGTY/MSGTX
│   └── 4. 返回 RESP 数据表
│
└── 写入接口（增删改）
    ├── 1. 初始化响应 (O_RESP-MSGTY = 'S', O_RESP-UUID = I_REQ-UUID)
    ├── 2. 排序去重 (SORT + DELETE ADJACENT DUPLICATES)
    ├── 3. 调用 FORM (PERFORM frm_maintain)
    │   ├── 3.1 判断新增/修改 (SELECT COUNT + CHECK)
    │   ├── 3.2 参数校验 (基础视图必填等)
    │   ├── 3.3 编号范围处理 → 见 [abap-coding.md](abap-coding.md#编号范围处理)
    │   ├── 3.4 单位转换 → 见 [abap-coding.md](abap-coding.md#单位转换)
    │   ├── 3.5 构建 BAPI 参数表
    │   ├── 3.6 测试运行 (TESTRUN = 'X')
    │   ├── 3.7 检查测试结果
    │   ├── 3.8 正式运行 (TESTRUN = '')
    │   ├── 3.9 检查正式结果
    │   ├── 3.10 提交 (BAPI_TRANSACTION_COMMIT) 或回滚 (BAPI_TRANSACTION_ROLLBACK)
    │   ├── 3.11 分类视图处理 → 见 [abap-coding.md](abap-coding.md#分类视图处理)
    │   └── 3.12 设置响应 (SAPNUM, MSGTX, MSGTY)
    └── 4. 返回结果
```

### 接口类型分类

接口函数模块按业务操作分为两类，采用不同的输出结构和处理流程：

| 类型 | 特征 | 输出结构 | 典型场景 |
|------|------|----------|----------|
| **查询接口** | 只读，SELECT 查询 | `ZSXX_XXXXX_RESP`（含 RESP 数据表） | 成本中心查询、物料搜索、订单查询 |
| **写入接口** | 增删改，调用 BAPI | `ZSREST_OUT`（统一结构） | 物料主数据同步、订单创建、成本中心维护 |

#### 查询接口 vs 写入接口 关键差异

| 对比维度 | 查询接口 | 写入接口 |
|----------|----------|----------|
| 输出结构 | 专用 `ZSXX_XXXXX_RESP` | 统一 `ZSREST_OUT` |
| 返回数据 | `RESP` 字段（内表） | `SAPNUM` 字段（单据号） |
| 事务处理 | 不需要 | 两阶段 BAPI + COMMIT/ROLLBACK |
| 排序去重 | 不需要 | 需要 |
| 参数处理 | 转 RANGE 实现可选过滤 | HEAD 控制字段 + 多表嵌套 |
| 数据为空 | 正常返回空表，MSGTY = 'E' | 异常，抛出或返回错误 |

#### 命名约定

| 类型 | 函数组 | 函数模块 | 输入结构 | 输出结构 | 输出表类型 | 输出行结构 |
|------|--------|----------|----------|----------|-----------|-----------|
| 查询 | `ZFG_XX` | `ZFM_XXI001` | `ZSXXI001_REQ` | `ZSXXI001_RESP` | `ZTTXXI001_OUT` | `ZSXXI001_OUT` |
| 写入 | `ZFG_XX` | `ZFM_XXI001` | `ZSMMI001_REQ` | `ZSREST_OUT` | — | — |

> 函数模块命名用 `I` 表示接口（Interface），如 `ZFM_FII001` = FI 模块接口 001。
> 查询接口输出结构用 `_RESP`，输出数据表字段用 `RESP`，表类型用 `_OUT` 后缀。

### DDIC 先行开发流程

**创建函数模块前，必须先创建 DDIC 对象。** 输入结构 `I_REQ` 和输出结构 `O_RESP` 有层级类型引用，最终用于生成 JSON。不按此顺序创建会导致编译错误。

```
第 1 步：创建 DDIC 对象（按依赖层级）
  域 (DOMA)
  └─ 数据元素 (DTEL)
     └─ 结构 (STRU)
        └─ 表类型 (TTYP)
           └─ I/O 结构 (I_REQ / O_RESP)

第 2 步：创建函数模块
  └─ 传入参数：I_REQ TYPE ZSXX_XXXXX_REQ
  └─ 传出参数：O_RESP TYPE ZSREST_OUT

第 3 步：生成函数逻辑
  └─ 按接口模板编写业务逻辑
```

**字段选择原则**：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | SAP 标准数据元素 | 直接使用，如 `MTART`, `MBRSH`, `LVORM`, `WERKS_D`, `MAKTX`, `MEINS` |
| 2 | 已有 Z 数据元素 | 复用，如 `ZEQUAN13`（多个结构中复用） |
| 3 | 新建 Z 数据元素 | 标准字段不存在时创建，命名 `ZE{描述}` |

**DDIC 命名速查**（详见 [abap-coding.md](abap-coding.md#ddic-对象命名)）：

**核心规则**：结构 = `ZS` + **接口编号** + 后缀；表类型 = `ZTT` + **接口编号** + 后缀。**中间永远是接口编号**（`{模块}I{序号}`，如 `PSI001`、`MMI001`）。传入/传出参数都遵循此规则。

> **接口编号未知时，必须向用户询问，禁止自行猜测或编造。** 接口编号是命名的核心，编错会导致整个 DDIC 对象集命名错误、无法追溯。

| 对象类型 | 命名规则 | 示例 |
|----------|----------|------|
| 域 | `ZD` + 描述 | `ZDNUMB`, `ZDFSYSID`, `ZDSYSUUID_C32` |
| 数据元素 | `ZE` + 描述 | `ZEQUAN13`, `ZEDEC3`, `ZENUMB`, `ZEFSYSID` |
| 结构 | `ZS` + 接口编号 + 后缀 | `ZSPSI001_OUT`, `ZS2657_DEMO03_OUT` |
| 表类型 | `ZTT` + 接口编号 + 后缀 | `ZTTPSI001_OUT`, `ZTTPSI001_WBS_OUT` |
| 函数组 | `ZFG_{模块}` | `ZFG_PS`, `ZFG_MM` |
| 函数模块 | `ZFM_{模块}I{序号}` | `ZFM_PSI001`, `ZFM_MMI001` |

> **命名注意**：`ZS` 后直接接接口编号，**不插入下划线**。SAP 不允许下划线在名称第 2-3 位。`ZS2657_DEMO03_OUT` 合法，`ZS_2657_DEMO03_OUT` 非法。函数组 `ZFG_` 不受此限制（函数组允许下划线）。

**后缀说明**（传入/传出通用）：

| 后缀 | 用途 | 示例 |
|------|------|------|
| `_REQ` | 顶层输入结构 | `ZSPSI001_REQ` |
| `_IN` | 输入业务数据 | `ZSPSI001_IN` |
| `_HEAD_IN` | 输入头结构 | `ZSMMI001_HEAD_IN` |
| `_{表}_IN` | 输入业务子表结构 | `ZSMMI001_MARA_IN`, `ZSMMI001_MARC_IN` |
| `_RESP` | 顶层输出结构 | `ZSPSI001_RESP` |
| `_OUT` | 输出行结构 / 输出表类型 | `ZSPSI001_OUT`, `ZTTPSI001_OUT` |
| `_{子表}_OUT` | 子表结构 / 子表类型 | `ZSPSI001_WBS_OUT`, `ZTTPSI001_WBS_OUT` |

**示例 — 物料写入接口 (ZFM_MMI001) 的 DDIC 创建顺序**：

```
1. 域:      ZDNUMB, ZDFSYSID, ZDSYSUUID_C32（仅标准字段不存在时创建）
2. 数据元素: ZENUMB, ZEFSYSID, ZEQUAN13, ZEDEC3, ZEDEC52
3. 结构:    ZSMMI001_MARA_IN (MARA 字段), ZSMMI001_MARC_IN (MARC 字段), ...
            └─ 字段优先使用 SAP 标准数据元素，不存在的用 Z 数据元素
4. 表类型:  ZTTMMI001_MARC_IN, ZTTMMI001_MARM_IN, ZTTMMI001_MBEW_IN, ...
5. I/O结构: ZSMMI001_IN (内层 REQ), ZSMMI001_REQ (顶层 I_REQ)
6. 函数模块: ZFM_MMI001 (IMPORTING I_REQ, EXPORTING O_RESP)
7. 函数逻辑: PERFORM frm_maintain, BAPI 调用, 提交/回滚
```

> 详细模板见 [写入接口模板](#写入接口) 和 [查询接口模板](#查询接口)。

### 函数模块源码格式（UpdateFunctionModule）

**通过 MCP `UpdateFunctionModule` 工具更新函数模块源码时，禁止包含 `*"` 签名块注释行。** 这些是 SAP GUI 自动生成的注释（`*"*"局部接口：`、`*"  IMPORTING` 等），传入 UpdateFunctionModule 会导致 "DATA is unexpected" 语法错误。

```abap
"❌ 错误 — 包含 *" 注释行，UpdateFunctionModule 报错
FUNCTION zfm_xxx.
*"----------------------------------------------------------------------
*"*"局部接口：
*"  IMPORTING
*"     VALUE(I_REQ) TYPE ZSXX_XXXXX_REQ OPTIONAL
*"  EXPORTING
*"     VALUE(O_RESP) TYPE ZSREST_OUT.
*"----------------------------------------------------------------------
  ...
ENDFUNCTION.

"✅ 正确 — 去掉 *" 注释行，直接写 FUNCTION 和参数
FUNCTION zfm_xxx.
  IMPORTING
    VALUE(I_REQ) TYPE ZSXX_XXXXX_REQ OPTIONAL
  EXPORTING
    VALUE(O_RESP) TYPE ZSREST_OUT.
  ...
ENDFUNCTION.
```

> **注意**：本文档中模板示例保留 `*"` 注释行是为了展示 SAP 标准签名格式（可读性），**实际通过 MCP 工具写入源码时必须去掉**。`IMPORTING`/`EXPORTING` 等参数行直接跟在 `FUNCTION` 语句之后，不需要缩进。

#### FUNCTION 语句语法（复盘补充）

> 复盘：ZFM_GLI001 开发中，第一次写 `FUNCTION zfm_gli001.`（函数名后加了句号），导致语法错误。

**FUNCTION 语句不能有句号**，句号在 `IMPORTING`/`EXPORTING` 参数声明结束后才出现：

```abap
"❌ 错误 — FUNCTION 后面不能有句号
FUNCTION zfm_gli001.
  IMPORTING
    VALUE(i_req) TYPE zsgli001_req OPTIONAL
  EXPORTING
    VALUE(o_resp) TYPE zsrest_out.
  ...

"✅ 正确 — FUNCTION 后面不加句号，句号在 EXPORTING 结束后
FUNCTION zfm_gli001
  IMPORTING
    VALUE(i_req) TYPE zsgli001_req OPTIONAL
  EXPORTING
    VALUE(o_resp) TYPE zsrest_out.
  ...
ENDFUNCTION.
```

---

## 写入接口

### MCP 语法检查器限制（复盘补充）

> 复盘：ZFM_GLI001 中 `i_req-uuid` 跨结构字段访问被 MCP 的 `CheckFunctionModule` 报错，但 `GetAbapSemanticAnalysis` 确认语法正确。

**MCP 的 `CheckFunctionModule` 语法检查器对跨结构字段访问（如 `i_req-uuid`、`i_req-req-znumb`）可能误报错误**，原因是 `CheckFunctionModule` 在检查时无法正确解析 `include` 结构中的字段。遇到这种情况时：

1. 先用 `GetAbapSemanticAnalysis` 确认语法是否正确
2. 如果语义分析确认正确，可以用 `MOVE-CORRESPONDING` 替代直接字段访问来绕过
3. 或者直接跳过 `CheckFunctionModule`，用 `ActivateFunctionModule` 让 SAP 系统自身做编译检查

```abap
"❌ CheckFunctionModule 可能误报
i_req-uuid = '...'        "跨 include 结构字段访问 → 可能报错

"✅ 用 MOVE-CORRESPONDING 绕过
MOVE-CORRESPONDING i_req TO o_resp.  "MCP 语法检查不会报错
```

> **注意**：这仅影响 `CheckFunctionModule` 工具，不影响 SAP 系统的实际编译和运行。激活后代码是正常可用的。

### 接口函数模块模板（写入接口）

#### 标准接口签名

对外**写入接口**函数模块（增删改 REST API 后端函数）必须遵循统一签名规范：

```abap
FUNCTION zfm_xx_xxxxx.
*"----------------------------------------------------------------------
*"*"局部接口：
*"  IMPORTING
*"     VALUE(I_REQ) TYPE ZSXX_XXXXX_REQ OPTIONAL
*"  EXPORTING
*"     VALUE(O_RESP) TYPE ZSREST_OUT.
*"----------------------------------------------------------------------

  "业务逻辑
  ...

ENDFUNCTION.
```

#### ZSREST_OUT 公共输出结构

**所有写入接口函数模块必须使用 `ZSREST_OUT` 作为输出结构**，这是公共标准（查询接口使用专用 `ZSXX_XXXXX_RESP`，见 [查询接口模板](#查询接口模板)）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `MSGTY` | MSGTY | 消息类型：S=成功, E=错误, W=警告, I=信息 |
| `MSGTX` | BAPI_MSG | 消息文本，错误时拼接所有错误消息 |
| `MSGID` | MSGID | 消息类（与 MESSAGE 语句联动） |
| `MSGNO` | MSGNO | 消息号（与 MESSAGE 语句联动） |
| `UUID` | ZESYSUUID_C32 | 唯一标识，调用方传入，原样返回（幂等） |
| `SAPNUM` | ZESAPN | SAP 单据号（物料号/订单号等） |
| `FIELD1` | CHAR20 | 预留字段1 |
| `FIELD2` | CHAR20 | 预留字段2 |
| `FIELD3` | CHAR20 | 预留字段3 |

#### 接口函数入口处理模式

**配置表维护类接口推荐使用 `MODIFY` 替代 `INSERT`/`UPDATE` 判断**：`MODIFY` 根据主键自动判断，存在则更新非主键字段，不存在则新增，无需 `SELECT` 判断记录是否存在。

```abap
FUNCTION zfm_xx_xxxxx.
  IMPORTING
    VALUE(I_REQ) TYPE ZSXX_XXXXX_REQ OPTIONAL
  EXPORTING
    VALUE(O_RESP) TYPE ZSREST_OUT.

  "1. 初始化响应
  O_RESP-MSGTY = 'S'.
  MOVE-CORRESPONDING I_REQ TO O_RESP.   "UUID 原样返回

  "2. MODIFY 写入（主键存在=更新，不存在=新增）
  MOVE-CORRESPONDING i_req-req TO ls_conf.
  MODIFY zt_xxx FROM ls_conf.
  IF sy-subrc = 0.
    o_resp-msgty = 'S'.
    o_resp-msgtx = '操作成功'.
  ELSE.
    o_resp-msgty = 'E'.
    o_resp-msgtx = '操作失败'.
  ENDIF.

ENDFUNCTION.
```

> 适用于配置表维护场景（如 ZTREST_CONF）。对于业务数据表（需要 TESTRUN 两阶段提交的场景），仍应使用 `INSERT`/`UPDATE` + `BAPI_TRANSACTION_COMMIT`。

传统写入接口（BAPI 场景）仍使用排序去重 + 两阶段提交模式：

```abap
FUNCTION zfm_xx_xxxxx.
  IMPORTING
    VALUE(I_REQ) TYPE ZSXX_XXXXX_REQ OPTIONAL
  EXPORTING
    VALUE(O_RESP) TYPE ZSREST_OUT.

  "1. 初始化响应
  O_RESP-MSGTY = 'S'.
  O_RESP-UUID  = I_REQ-UUID.   "UUID 原样返回

  "2. 排序去重（防止重复数据导致 BAPI 重复）
  SORT I_REQ-REQ-INNER_TABLE.
  DELETE ADJACENT DUPLICATES FROM I_REQ-REQ-INNER_TABLE
    COMPARING ALL FIELDS.

  "3. 调用业务 FORM
  PERFORM frm_business_maintain TABLES I_REQ-REQ-INNER_TABLE
                                USING  I_REQ-REQ-HEAD
                                       I_REQ-REQ-MAIN_DATA
                              CHANGING O_RESP.

ENDFUNCTION.
```

#### 输入结构命名规范

接口输入结构必须以 `ZSXX_XXXXX_REQ` 命名，内部嵌套 `REQ` 结构：

```abap
"顶层：ZSXX_XXXXX_REQ
"  ├── UUID      : ZESYSUUID_C32   "唯一标识
"  ├── ZNUMBER   : ZESAPN          "外部单据号
"  └── REQ       : ZSXX_XXXXX_IN   "业务数据（嵌套结构）
"        ├── HEAD : ZSXX_XXXXX_HEAD_IN  "头信息（控制字段）
"        ├── MAIN : ZSXX_XXXXX_MAIN_IN  "主数据
"        ├── ITEM1: ZTTXX_XXXXX_ITEM1   "明细表1
"        ├── ITEM2: ZTTXX_XXXXX_ITEM2   "明细表2
"        └── ...
```

**示例 - 物料接口输入结构**：

```abap
" ZSMMI001_REQ（请求结构）
"  ├── UUID  : ZESYSUUID_C32
"  └── REQ   : ZSMMI001_IN
"        ├── HEAD : ZSMMI001_HEAD_IN  "basic_view, sales_view, ...
"        ├── MARA : ZSMM_MARA_IN      "MARA 字段
"        ├── MARC[]: ZTTMM_MARC_IN    "工厂数据表
"        ├── MARM[]: ZTTMM_MARM_IN    "单位数据表
"        ├── MBEW[]: ZTTMM_MBEW_IN    "评估数据表
"        ├── MLAN[]: ZTTMM_MLAN_IN    "税分类数据表
"        ├── MVKE[]: ZTTMM_MVKE_IN    "销售数据表
"        └── AUSP[]: ZTTMM_AUSP_IN    "分类数据表
```

#### HEAD 结构（控制字段）

```abap
@EndUserText.label : '传入结构-头信息'
define structure zsxx_xxxxx_head_in {
  matnr        : matnr;       "物料号/业务主键
  basic_view   : flag;        "基本视图
  sales_view   : flag;        "销售视图
  purchase_view: flag;        "采购视图
  mrp_view     : flag;        "MRP视图
  storage_view : flag;        "存储视图
  account_view : flag;        "会计视图
  cost_view    : flag;        "成本视图
  class_view   : flag;        "分类视图
}
```

### 写入接口进阶模式

#### DEFINE 快捷错误返回

DEFINE 宏语法与命名规范见 [abap-coding.md](abap-coding.md#define-宏)。接口场景的典型用法是封装错误返回，减少 FORM 内的重复代码：

```abap
FORM frm_xxx_maintain ...
  DEFINE ret.
    o_resp-msgty = &1.
    o_resp-msgtx = &2.
    RETURN.
  END-OF-DEFINITION.

  "使用
  IF ls_head-matnr IS INITIAL.
    ret 'E' '物料号不能为空'.
  ENDIF.
  IF ls_head-werks IS INITIAL.
    ret 'E' '工厂不能为空'.
  ENDIF.
ENDFORM.
```

> **注意**：DEFINE 宏仅在当前 FORM 内有效，多个 FORM 需要各自定义。通常放在 FORM 的数据声明之后、业务逻辑之前。

#### CONVERSION_EXIT 预转换模式

调用 BAPI 前，必须将外部格式转为 SAP 内部格式。完整转换函数清单（CUNIT/MATN1/ALPHA 等）见 [abap-coding.md](abap-coding.md#单位转换)，此处只展示接口中的典型预转换用法：

```abap
"典型预转换流程
CALL FUNCTION 'CONVERSION_EXIT_MATN1_INPUT'
  EXPORTING
    input        = ls_head-matnr
  IMPORTING
    output       = ls_head-matnr
  EXCEPTIONS
    length_error = 1
    OTHERS       = 2.

"供应商/凭证号 ALPHA 转换
ls_head-lifnr = |{ ls_head-lifnr ALPHA = IN }|.
lv_ebeln = |{ ls_head-ebeln ALPHA = IN }|.

"单位转换（BDC 场景）
CALL FUNCTION 'CONVERSION_EXIT_CUNIT_OUTPUT'
  EXPORTING
    input          = ls_req-meins
  IMPORTING
    output         = lv_meins
  EXCEPTIONS
    unit_not_found = 1
    OTHERS         = 2.
```

#### 多表数据去重

输入数据可能包含重复行，处理前先 SORT + DELETE ADJACENT DUPLICATES：

```abap
"对每个输入表排序后去重
SORT i_req-req-marc.
SORT i_req-req-marm.
SORT i_req-req-mbew.
DELETE ADJACENT DUPLICATES FROM i_req-req-marc COMPARING ALL FIELDS.
DELETE ADJACENT DUPLICATES FROM i_req-req-marm COMPARING ALL FIELDS.
DELETE ADJACENT DUPLICATES FROM i_req-req-mbew COMPARING ALL FIELDS.
```

> `COMPARING ALL FIELDS` 确保完全重复的行才被删除。

#### BAPI 返回值处理模式

BAPI 调用后统一处理返回消息，收集错误信息并拼接到 MSGTX：

```abap
DATA: lv_msg  TYPE bapi_msg,
      lv_msg2 TYPE bapi_msg.

CALL FUNCTION 'BAPI_GOODSMVT_CANCEL'
  ...
  TABLES
    return = lt_return.

"收集所有 E/A/X 类型消息
LOOP AT lt_return INTO ls_return WHERE type CA 'EAX'.
  CLEAR: lv_msg2.
  CALL FUNCTION 'MESSAGE_TEXT_BUILD'
    EXPORTING
      msgid               = ls_return-id
      msgnr               = ls_return-number
      msgv1               = ls_return-message_v1
      msgv2               = ls_return-message_v2
      msgv3               = ls_return-message_v3
      msgv4               = ls_return-message_v4
    IMPORTING
      message_text_output = lv_msg2.
  lv_msg = lv_msg && '/' && lv_msg2.
ENDLOOP.

"无错误则提交，有错误则回滚
IF lv_msg IS INITIAL.
  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'
    EXPORTING
      wait = 'X'.
  o_resp-msgty = 'S'.
  o_resp-msgtx = '操作成功'.
ELSE.
  CALL FUNCTION 'BAPI_TRANSACTION_ROLLBACK'.
  o_resp-msgty = 'E'.
  o_resp-msgtx = lv_msg.
ENDIF.
```

**要点**：

| 要点 | 说明 |
|------|------|
| `WHERE type CA 'EAX'` | 只收集 Error、Abort、eXit 类消息 |
| `MESSAGE_TEXT_BUILD` | 将 BAPI 消息转为可读文本 |
| `&& '/' &&` | 多个错误用 `/` 分隔 |
| `COMMIT + WAIT = 'X'` | 同步提交，确保数据持久化 |
| `ROLLBACK` | 任何错误立即回滚，保证数据一致性 |

#### 两阶段提交（TESTRUN → 实际运行）

调用状态变更类 BAPI 时，必须分两步：先测试运行，测试通过再正式运行，最后提交或回滚。

```abap
FORM frm_bapi_call TABLES ...
                    USING VALUE(IS_HEAD) ...
                  CHANGING CV_RESP TYPE ZSREST_OUT.

  "1. 判断新增/修改
  SELECT SINGLE COUNT(*) FROM t_target WHERE key = lv_key.
  IF sy-subrc = 0.
    lv_flag = 'U'.  "修改
  ELSE.
    lv_flag = 'I'.  "新增
  ENDIF.

  "2. 构建 BAPI 参数表
  PERFORM build_bapi_tables USING ...
                       CHANGING lt_headdata[]
                                lt_clientdata[]
                                lt_clientdatax[]
                                lt_returnmessages[].

  "3. 第一阶段：测试运行 (TESTRUN = 'X')
  CALL FUNCTION 'BAPI_XXX_SAVEREPLICA'
    EXPORTING
      TESTRUN        = 'X'          "测试运行，不真正写入
    IMPORTING
      RETURN         = ls_return
    TABLES
      HEADDATA       = lt_headdata
      CLIENTDATA     = lt_clientdata
      CLIENTDATAX    = lt_clientdatax
      RETURNMESSAGES = lt_returnmessages.

  "4. 检查测试运行结果
  IF ls_return-type = 'E' OR ls_return-type = 'A'.
    cv_resp-msgty = 'E'.
    CONCATENATE cv_resp-msgtx ls_return-message
      INTO cv_resp-msgtx SEPARATED BY space.
  ENDIF.

  LOOP AT lt_returnmessages INTO ls_returnmessages
    WHERE type = 'E' OR type = 'A'.
    cv_resp-msgty = 'E'.
    CONCATENATE cv_resp-msgtx ls_returnmessages-message
      INTO cv_resp-msgtx SEPARATED BY space.
  ENDLOOP.

  "5. 测试通过 → 正式运行 (TESTRUN = '')
  IF cv_resp-msgty = 'S'.
    CALL FUNCTION 'BAPI_XXX_SAVEREPLICA'
      EXPORTING
        TESTRUN        = ''          "正式运行，真正写入
      IMPORTING
        RETURN         = ls_return
      TABLES
        HEADDATA       = lt_headdata
        CLIENTDATA     = lt_clientdata
        CLIENTDATAX    = lt_clientdatax
        RETURNMESSAGES = lt_returnmessages.

    "再次检查正式运行结果
    IF ls_return-type = 'E' OR ls_return-type = 'A'.
      cv_resp-msgty = 'E'.
      CONCATENATE cv_resp-msgtx ls_return-message
        INTO cv_resp-msgtx SEPARATED BY space.
    ENDIF.

    LOOP AT lt_returnmessages INTO ls_returnmessages
      WHERE type = 'E' OR type = 'A'.
      cv_resp-msgty = 'E'.
      CONCATENATE cv_resp-msgtx ls_returnmessages-message
        INTO cv_resp-msgtx SEPARATED BY space.
    ENDLOOP.

    "6. 提交或回滚
    IF cv_resp-msgty = 'S'.
      CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'
        EXPORTING
          wait = 'X'.
      cv_resp-sapnum = lv_key.   "返回 SAP 单据号
      cv_resp-msgtx  = '处理成功'.
    ELSE.
      CALL FUNCTION 'BAPI_TRANSACTION_ROLLBACK'.
    ENDIF.

  ENDIF.

ENDFORM.
```

**两阶段模式要点**：

| 步骤 | 说明 | 关键点 |
|------|------|--------|
| 测试运行 | `TESTRUN = 'X'` | 不写入数据库，只做校验 |
| 检查结果 | 遍历 `RETURNMESSAGES` | 检查 E/A 类型消息 |
| 正式运行 | `TESTRUN = ''` | 测试通过后才真正写入 |
| 再次检查 | 再次遍历 `RETURNMESSAGES` | 正式运行也可能有错误 |
| 提交 | `BAPI_TRANSACTION_COMMIT` | 成功时提交 |
| 回滚 | `BAPI_TRANSACTION_ROLLBACK` | 失败时回滚 |

#### # 特殊值标记（清空字段）

接口中 `#` 字符表示**清空该字段值**：

```abap
"如果字段值为 #，则清空对应 BAPI 字段
IF ls_mara-lvorm IS NOT INITIAL.
  IF ls_mara-lvorm = '#'.
    ls_clientdata-del_flag = space.  "清空
  ELSE.
    ls_clientdata-del_flag = ls_mara-lvorm.  "赋值
  ENDIF.
  ls_clientdatax-del_flag = 'X'.  "标记为修改
ENDIF.
```

#### 编号范围处理（内部/外部给号）

区分内部给号（系统自动生成）和外部给号（调用方传入）的完整流程、三步骤（`NUMBER_RANGE_ENQUEUE` → `NUMBER_GET_NEXT` → `NUMBER_RANGE_DEQUEUE`）及相关函数清单，见 [abap-coding.md](abap-coding.md#编号范围处理)。

#### BDC 录屏模式

当 BAPI 不存在或功能不完整时，使用 BDC 作为备选方案。BDC 数据结构、`CALL TRANSACTION` 的 MODE/UPDATE 参数、`BDCMSGCOLL` 错误处理、SHDB 录制规范见 [abap-batchinput.md](abap-batchinput.md)。

接口场景的要点是**按新增/修改路由到不同事务码**：

```abap
"判断是新增还是修改
IF gv_flag = 'I'.
  "BDC 录屏创建
  PERFORM bdc_dynpro USING 'SAPMM06I' '0100'.
  PERFORM bdc_field  USING 'BDC_OKCODE' '/00'.
  PERFORM bdc_field  USING 'EINA-LIFNR' ls_req-lifnr.
  PERFORM bdc_field  USING 'EINA-MATNR' ls_req-matnr.
  ...

  "调用 BDC
  CALL TRANSACTION 'ME11' USING gt_bdcdata
                           MODE 'N'
                           MESSAGES INTO gt_messtab.
ELSE.
  "BDC 录屏修改
  PERFORM bdc_dynpro USING 'SAPMM06I' '0100'.
  PERFORM bdc_field  USING 'BDC_OKCODE' '/00'.
  ...
  CALL TRANSACTION 'ME12' USING gt_bdcdata
                           MODE 'N'
                           MESSAGES INTO gt_messtab.
ENDIF.
```

> 新增/修改/删除必须使用对应的事务码（如 ME11/ME12/ME15），不能共用一个。BDC 消息需转换后写入 `O_RESP-MSGTX`。

#### 长文本分割

长文本按固定长度分割的通用模式（`DIV` 分段 + 循环填充）见 [abap-coding.md](abap-coding.md#字符串处理)。

#### 必填字段交叉校验

多个控制字段互斥时，使用组合校验：

```abap
"一次只允许处理一种业务类型
IF ls_head-calyzfp IS NOT INITIAL
   AND ls_head-delyzfp IS NOT INITIAL
   AND ls_head-offfp IS NOT INITIAL.
  o_resp-msgty = 'E'.
  o_resp-msgtx = '一次只允许处理一种业务，请检查标识'.
  EXIT.
ENDIF.

"必填校验
IF ls_head-lifnr IS INITIAL.
  o_resp-msgty = 'E'.
  o_resp-msgtx = '供应商不能为空'.
  EXIT.
ENDIF.
```

#### CASE ABAP_TRUE 条件分支

多个布尔标志选一的通用语法模式见 [abap-coding.md](abap-coding.md#case-abap_true-条件分支)。

#### 金额符号处理

借贷方向金额符号调整与校验的通用模式见 [abap-coding.md](abap-coding.md#金额符号处理)。

#### 写入接口模式汇总

| 模式 | 适用场景 | 来源函数 |
|------|----------|----------|
| DEFINE 快捷返回 | FORM 内频繁错误返回 | ZFM_MMI004, ZFM_MMI012 |
| CONVERSION_EXIT | BAPI 调用前格式转换 | 所有写入接口 |
| 多表去重 | 输入含多表数据 | ZFM_MMI001 |
| MESSAGE_TEXT_BUILD | BAPI 错误消息可读化 | ZFM_MMI006, ZFM_MMI009, ZFM_MMI011, ZFM_MMI012 |
| 两阶段提交 | 状态变更前校验 | ZFM_MMI002, ZFM_MMI003 |
| 编号范围 | 物料/供应商/凭证编号 | ZFM_MMI001, ZFM_MMI004 |
| BDC 录屏 | BAPI 不可用时的备选 | ZFM_MMI005 |
| 长文本分割 | 通用字符串处理 → [abap-coding.md](abap-coding.md#字符串处理) | ZFM_MMI003 |
| 交叉校验 | 互斥控制字段 | ZFM_MMI010 |
| CASE ABAP_TRUE | 通用现代语法 → [abap-coding.md](abap-coding.md#case-abap_true-条件分支) | ZFM_MMI010 |
| 金额符号 | 通用金额处理 → [abap-coding.md](abap-coding.md#金额符号处理) | ZFM_MMI010 |

---

## 查询接口

### 查询接口模板

查询接口（只读）用于数据检索，**不需要事务处理**，核心是将输入参数转为 RANGE 实现灵活的可选过滤。

#### 标准查询接口签名

```abap
FUNCTION zfm_xxi001.
*"----------------------------------------------------------------------
*"*"局部接口：
*"  IMPORTING
*"     VALUE(I_REQ) TYPE ZSXXI001_REQ OPTIONAL
*"  EXPORTING
*"     VALUE(O_RESP) TYPE ZSXXI001_RESP.    "输出结构用 _RESP
*"----------------------------------------------------------------------

  "1. 解析输入参数
  DATA(gs_req) = i_req-req.

  "2. 参数转 RANGE（可选过滤）
  DATA: r_kostl TYPE RANGE OF csks-kostl,
        r_bukrs TYPE RANGE OF csks-bukrs.

  IF gs_req-kostl IS NOT INITIAL.
    r_kostl = VALUE #( ( sign = 'I' option = 'EQ' low = gs_req-kostl ) ).
  ENDIF.

  IF gs_req-bukrs IS NOT INITIAL.
    r_bukrs = VALUE #( ( sign = 'I' option = 'EQ' low = gs_req-bukrs ) ).
  ENDIF.

  "3. 查询数据
  SELECT t1~kostl,
         t2~ktext,
         t1~datbi,
         t1~datab,
         t1~bukrs,
         t1~gsber,
         t1~kosar,
         t1~prctr,
         t1~bkzkp,
         t1~waers
    FROM csks AS t1
    LEFT JOIN cskt AS t2 ON t2~kokrs = t1~kokrs AND
                            t2~kostl = t1~kostl AND
                            t2~datbi = t1~datbi
   WHERE t1~kokrs = '1000'
     AND t1~bukrs IN @r_bukrs
     AND t1~kostl IN @r_kostl
    INTO TABLE @DATA(lt_resp)
    .

  "4. 设置响应
  o_resp-uuid  = i_req-uuid.        "UUID 原样返回
  o_resp-resp  = lt_resp.           "查询结果数据表（字段名 RESP）
  IF o_resp-resp IS INITIAL.
    o_resp-msgty = 'E'.
    o_resp-msgtx = '查询数据为空'.
  ELSE.
    o_resp-msgty = 'S'.
    o_resp-msgtx = '成功'.
  ENDIF.

ENDFUNCTION.
```

#### 查询输出结构 — 两种选择（按返回记录数）

查询接口的输出结构**按返回记录数分两种情况**：

| 返回类型 | 输出结构 | 说明 |
|----------|----------|------|
| **单条记录** | 直接使用 `ZSREST_OUT` | 不新建结构，`SAPNUM` 等字段承载单条结果 |
| **表格（多条记录）** | 新建 `ZSXXI001_RESP` | 复制 `ZSREST_OUT` 公共字段 + 追加 `RESP` 表 |

**表格返回时的结构定义规则**：

```abap
"输出结构：ZSPSI001_RESP
"  ├── MSGTY  : MSGTY            "消息类型：S/E
"  ├── MSGTX  : BAPI_MSG         "消息文本
"  ├── MSGID  : MSGID            "消息类
"  ├── MSGNO  : MSGNO            "消息号
"  ├── UUID   : ZESYSUUID_C32    "唯一标识，原样返回（幂等）
"  ├── SAPNUM : ZESAPN           "SAP 号码
"  ├── FIELD1 : CHAR20           "预留字段1
"  ├── FIELD2 : CHAR20           "预留字段2
"  ├── FIELD3 : CHAR20           "预留字段3
"  └── RESP   : ZTTXXI001_OUT    "查询结果数据表 ← 追加字段
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `MSGTY` | MSGTY | 消息类型：S=成功, E=错误 |
| `MSGTX` | BAPI_MSG | 消息文本 |
| `MSGID` | MSGID | 消息类（预留） |
| `MSGNO` | MSGNO | 消息号（预留） |
| `UUID` | ZESYSUUID_C32 | 唯一标识，调用方传入，原样返回（幂等） |
| `SAPNUM` | ZESAPN | SAP 号码（预留） |
| `FIELD1`~`FIELD3` | CHAR20 | 预留字段 |
| `RESP` | 内表 | 查询结果数据表 — **字段名固定为 `RESP`** |

> **关键规则**：
> 1. 表格返回时，**复制 `ZSREST_OUT` 的全部公共字段**（含 `FIELD1-3`），最后追加 `RESP` 表字段。
> 2. `RESP` 参照表类型 `ZTTXXI001_OUT`，表类型自动按返回行结构 `ZSXXI001_OUT` 定义。
> 3. **禁止在函数 `TABLES` 参数里内联定义结构** — 必须创建 DDIC 结构。反例：在 SE37 函数参数表里直接定义结构字段，不规范。

#### 查询输入结构

查询接口输入结构使用 `include ZSREST_IN` 引入公共字段，再加 `REQ` 业务数据：

```abap
"输入结构：ZSPSI001_REQ
"  ├── include ZSREST_IN   → UUID, ZNUMB, FSYSID
"  └── REQ : ZSPSI001_IN   → 业务查询条件
```

`ZSREST_IN` 公共输入结构（所有接口复用）：
| 字段 | 类型 | 说明 |
|------|------|------|
| `UUID` | ZESYSUUID_C32 | 唯一标识，调用方传入，原样返回 |
| `ZNUMB` | ZENUMB | 接口编号 |
| `FSYSID` | ZEFSYSID | 传输系统名称 |

> `include ZSREST_IN` 是推荐做法，避免在每个 REQ 结构中重复定义 UUID/ZNUMB/FSYSID。

#### 输出行结构（OUT）

查询接口的 `OUT` 结构是 RESP 表的一行，字段来自 SELECT 列。如有子表数据，通过嵌套表类型字段实现：

```abap
"ZSPSI001_OUT — RESP 表的一行
"  ├── pspid   : ps_pspid       "项目编号
"  ├── post1   : ps_post1       "项目描述
"  ├── werks   : werks_d        "工厂
"  ├── ...
"  └── wbs     : ZTTPSI001_WBS_OUT  "WBS 子表（嵌套内表）
```

**嵌套子表模式**：当查询结果的一行包含多条子记录（如一个项目下多个 WBS），OUT 结构直接包含一个表类型字段：

```abap
define structure zspsi001_out {
  pspid   : ps_pspid;
  post1   : ps_post1;
  ...
  wbs     : zttpsi001_wbs_out;  "嵌套子表 — 一主多子
}
```

**DDIC 创建顺序**（查询接口）：
```
1. 子表行结构  → ZSPSI001_WBS_OUT
2. 子表表类型  → ZTTPSI001_WBS_OUT
3. 主表行结构  → ZSPSI001_OUT（引用 ZTTPSI001_WBS_OUT）
4. 主表表类型  → ZTTPSI001_OUT
5. 查询条件    → ZSPSI001_IN
6. 输入结构    → ZSPSI001_REQ（include ZSREST_IN; req: ZSPSI001_IN）
7. 输出结构    → ZSPSI001_RESP（公共字段 + resp: ZTTPSI001_OUT）
```

> 示例来源：`ZFM_PSI001` 库存查询接口。

#### RANGE 可选过滤模式

查询接口的输入参数全部可选，通过转为 RANGE 实现：
- **有值** → RANGE 带 EQ 条件，精确过滤
- **为空** → RANGE 保持空，`IN` 操作符等效于不筛选

```abap
"参数转 RANGE 模板
DATA: r_field1 TYPE RANGE OF table-field1,
      r_field2 TYPE RANGE OF table-field2.

"仅当输入有值时填充 RANGE
IF gs_req-field1 IS NOT INITIAL.
  r_field1 = VALUE #( ( sign = 'I' option = 'EQ' low = gs_req-field1 ) ).
ENDIF.

IF gs_req-field2 IS NOT INITIAL.
  r_field2 = VALUE #( ( sign = 'I' option = 'EQ' low = gs_req-field2 ) ).
ENDIF.

"SELECT 中使用 IN 操作符（RANGE 为空时等效于全选）
SELECT ...
  FROM table
 WHERE field1 IN @r_field1
   AND field2 IN @r_field2
   .
```

**RANGE 字段说明**：

| 字段 | 值 | 说明 |
|------|-----|------|
| `SIGN` | `I` | 包含（Include） |
| `OPTION` | `EQ` | 等于（可扩展为 BT/CP/NE 等） |
| `LOW` | 输入值 | 过滤值 |

**扩展 RANGE 场景**：

```abap
"多值过滤（传入内表）
IF gs_req-kostl_tab IS NOT INITIAL.
  r_kostl = VALUE #( FOR <k> IN gs_req-kostl_tab
                     ( sign = 'I' option = 'EQ' low = <k>-kostl ) ).
ENDIF.

"区间过滤（传入起止值）
IF gs_req-date_from IS NOT INITIAL AND gs_req-date_to IS NOT INITIAL.
  r_date = VALUE #( ( sign = 'I' option = 'BT'
                      low  = gs_req-date_from
                      high = gs_req-date_to ) ).
ENDIF.
```

#### 查询接口输入结构

查询接口输入结构比写入接口更简洁，不需要 HEAD 控制字段和多表嵌套：

```abap
"输入结构：ZSPSI001_REQ
"  ├── include ZSREST_IN  → UUID, ZNUMB, FSYSID（公共字段）
"  └── REQ : ZSPSI001_IN  → 查询条件
"        ├── VBUKR  : PS_VBUKR    "公司代码（可选）
"        ├── PSPID  : PS_PSPID    "项目编号（可选）
"        ├── ERDAT_B : ERDAT      "开始日期（可选）
"        └── ERDAT_E : ERDAT      "结束日期（可选）
```

#### 查询接口入口处理模式

查询接口的入口处理只做参数解析，不排序去重，不调用 FORM（逻辑简单时直接写在函数中）：

```abap
FUNCTION zfm_xxi001.
  IMPORTING
    VALUE(I_REQ) TYPE ZSXXI001_REQ OPTIONAL
  EXPORTING
    VALUE(O_RESP) TYPE ZSXXI001_RESP.      "输出结构 _RESP

  "1. 解析参数
  DATA(gs_req) = i_req-req.

  "2. 输入转 RANGE（可选过滤）
  ...（见上方 RANGE 模板）

  "3. 查询数据
  SELECT ... INTO TABLE @DATA(lt_resp) ...

  "4. 设置响应
  o_resp-uuid  = i_req-uuid.
  o_resp-resp  = lt_resp.                  "字段名 RESP
  o_resp-msgty = COND #( WHEN lt_resp IS INITIAL THEN 'E' ELSE 'S' ).
  o_resp-msgtx = COND #( WHEN lt_resp IS INITIAL THEN '查询数据为空' ELSE '成功' ).

ENDFUNCTION.
```

### 查询接口进阶模式

#### 动态 SQL 拼接

当查询条件较多且需要灵活组合时，可以使用动态 SQL 字符串拼接替代 RANGE 模式：

```abap
DATA: lv_sql TYPE string.

"按需拼接 WHERE 条件
IF gs_req-matnr IS NOT INITIAL.
  lv_sql = 'a~matnr = @gs_req-matnr AND'.
ENDIF.
IF gs_req-lgort IS NOT INITIAL.
  lv_sql = lv_sql && ` ` && 'a~lgort = @gs_req-lgort AND'.
ENDIF.
IF gs_req-charg IS NOT INITIAL.
  lv_sql = lv_sql && ` ` && 'a~charg = @gs_req-charg AND'.
ENDIF.

"兜底条件，确保 SQL 语法正确
lv_sql = lv_sql && ` ` && '1 = 1'.

SELECT ...
  FROM table AS a
 WHERE fixed_condition = @lv_value
   AND (lv_sql)
  INTO TABLE @DATA(lt_result)
  .
```

| RANGE 模式 | 动态 SQL 模式 |
|------------|---------------|
| 适合简单可选过滤（≤ 3 个条件） | 适合复杂条件组合（多条件、多表） |
| 需提前声明 RANGE 变量 | 只需一个 `lv_sql` 字符串 |
| 条件固定为 `EQ` | 可灵活拼接任意条件（`LIKE`、`BETWEEN` 等） |
| 语法更简洁 | 更灵活，但需注意拼接空格和 `AND` |

> **注意**：动态 SQL 最后必须拼接 `1 = 1` 兜底，防止前面的 `AND` 导致 SQL 语法错误。

#### 条件分支查询

使用控制标志（如 `zzsmx`）路由到不同的查询分支，每个分支查询不同的数据源，最终统一输出：

```abap
"控制标志决定查询路径
IF gs_req-zzsmx = 'X'.
  "分支1：查询非限制库存 (MARD)
  SELECT ... FROM mard AS a
    WHERE a~werks = @gs_req-werks
      AND (lv_sql)
    INTO TABLE @lt_out.
  SORT lt_out BY matnr lgort.

ELSEIF gs_req-zzsmx IS INITIAL.
  "分支2：查询批次库存 (MCHB)
  SELECT ... FROM mchb AS a
    WHERE werks = @gs_req-werks
      AND a~clabs IS NOT INITIAL
      AND (lv_sql)
    INTO TABLE @lt_out.
  SORT lt_out BY matnr werks lgort.
  DELETE ADJACENT DUPLICATES FROM lt_out COMPARING matnr werks lgort.

  "分支2.1：补充设备库存 (EQUI)
  SELECT ... FROM equi AS a
    JOIN eqbs AS b ON a~equnr = b~equnr
    WHERE b~b_werk = @gs_req-werks
      AND (lv_sql_equi)
    INTO TABLE @DATA(lt_equi).
  SORT lt_equi BY matnr.
  DELETE ADJACENT DUPLICATES FROM lt_equi COMPARING ALL FIELDS.

  "补充物料描述 (FOR ALL ENTRIES)
  IF lt_equi IS NOT INITIAL.
    SELECT ... FROM mara AS a
      FOR ALL ENTRIES IN @lt_equi
      WHERE a~matnr = @lt_equi-matnr
      INTO TABLE @DATA(lt_mara).
    SORT lt_mara BY matnr.
  ENDIF.

  "合并 EQUI 数据到 lt_out
  LOOP AT lt_equi INTO DATA(ls_equi).
    CLEAR ls_out.
    MOVE-CORRESPONDING ls_equi TO ls_out.
    ls_out-labst = 1.  "设备库存固定为 1

    READ TABLE lt_mara INTO DATA(ls_mara) WITH KEY matnr = ls_equi-matnr BINARY SEARCH.
    IF sy-subrc = 0.
      ls_out-meins = ls_mara-meins.
      ls_out-msehl = ls_mara-msehl.
    ENDIF.
    APPEND ls_out TO lt_out.
  ENDLOOP.

ENDIF.
```

**分支模式要点**：

| 要点 | 说明 |
|------|------|
| 控制标志 | 用 `zzsmx` 等字段区分查询类型，命名清晰见名知意 |
| 分支隔离 | 每个分支独立完成 SELECT + SORT + 去重 |
| 统一输出 | 各分支结果写入同一个 `lt_out` 内表 |
| 补充查询 | 用 `FOR ALL ENTRIES` 补充关联数据（如物料描述） |
| 合并时注意 | 使用 `MOVE-CORRESPONDING` 对齐字段，特殊字段单独赋值 |

#### 必填参数校验 + 提前 RETURN

查询接口中部分参数可能为必填，应在函数开头校验并立即返回：

```abap
"必填参数校验
IF i_req-req-werks IS INITIAL.
  o_resp-msgty = 'E'.
  o_resp-msgtx = '工厂字段必输！'.
  RETURN.
ENDIF.
```

> 在 `RETURN` 之前必须设置 `MSGTY` 和 `MSGTX`，调用方才能获知失败原因。

#### 多数据源合并模式

当数据来自多个数据源（不同表、不同查询），需要合并到统一输出：

```abap
"1. 主数据源查询
SELECT ... FROM mchb INTO TABLE @lt_out ...

"2. 辅助数据源查询
SELECT ... FROM equi INTO TABLE @lt_equi ...

"3. 补充关联数据（FOR ALL ENTRIES）
IF lt_equi IS NOT INITIAL.
  SELECT ... FROM mara
    FOR ALL ENTRIES IN @lt_equi
    WHERE matnr = @lt_equi-matnr
    INTO TABLE @lt_mara.
  SORT lt_mara BY matnr.  "BINARY SEARCH 前必须排序
ENDIF.

"4. LOOP + READ TABLE 合并
LOOP AT lt_equi INTO DATA(ls_equi).
  CLEAR ls_out.
  MOVE-CORRESPONDING ls_equi TO ls_out.

  READ TABLE lt_mara INTO DATA(ls_mara) WITH KEY matnr = ls_equi-matnr BINARY SEARCH.
  IF sy-subrc = 0.
    ls_out-meins = ls_mara-meins.
  ENDIF.

  APPEND ls_out TO lt_out.
ENDLOOP.
```

**合并要点**：

| 要点 | 说明 |
|------|------|
| `BINARY SEARCH` | 使用前必须 `SORT` 辅助表 |
| `FOR ALL ENTRIES` 检查 | 必须先检查驱动表非空 |
| `MOVE-CORRESPONDING` | 对齐同名字段，特殊字段后单独赋值 |
| 去重 | 合并后可能需要 `DELETE ADJACENT DUPLICATES` |

#### 后置过滤 (DELETE)

当数据合并后需要进一步筛选，使用 DELETE 语句后置过滤：

```abap
"按批次号过滤
IF gs_req-charg IS NOT INITIAL.
  DELETE lt_out WHERE charg <> gs_req-charg.
ENDIF.

"按序列号过滤
IF gs_req-serge IS NOT INITIAL.
  DELETE lt_out WHERE serge <> gs_req-serge.

  "过滤后如果指定了序列号但无库存位置，视为无数据
  IF lt_out IS NOT INITIAL.
    DELETE lt_out WHERE lgort IS INITIAL.
    IF lt_out IS INITIAL.
      o_resp-msgty = 'S'.
      o_resp-msgtx = '无库存数据！'.
    ENDIF.
  ENDIF.
ENDIF.
```

#### 日期 RANGE 区间模式

日期字段支持单值和区间两种输入，按条件动态设置 RANGE：

```abap
"仅开始日期 → EQ 单值过滤
IF i_req-req-erdat_b IS NOT INITIAL AND i_req-req-erdat_e IS INITIAL.
  r_erdat-option = 'EQ'.
  r_erdat-sign = 'I'.
  r_erdat-low = i_req-req-erdat_b.
  APPEND r_erdat.
ENDIF.

"开始+结束日期 → BT 区间过滤
IF i_req-req-erdat_b IS NOT INITIAL AND i_req-req-erdat_e IS NOT INITIAL.
  r_erdat-option = 'BT'.
  r_erdat-sign = 'I'.
  r_erdat-low = i_req-req-erdat_b.
  r_erdat-high = i_req-req-erdat_e.
  APPEND r_erdat.
ENDIF.
```

**要点**：只传开始日期用 `EQ`，同时传开始+结束用 `BT`。不要混用。

#### SELECT JOIN 内表模式

当第二个查询需要引用第一个查询结果时，直接用 `JOIN` 内表，避免 `FOR ALL ENTRIES` 的局限性：

```abap
"第一个查询
SELECT pspnr, pspid, post1, ...
  FROM proj
  INTO TABLE @DATA(lt_proj)
 WHERE ...
  .
SORT lt_proj BY pspnr.

"第二个查询 — JOIN 内表，直接过滤关联数据
SELECT prps~psphi,
       prps~pspnr,
       prps~posid,
       ...
  FROM prps
  JOIN @lt_proj AS a ON prps~psphi = a~pspnr
  LEFT JOIN prte ON prps~pspnr = prte~posnr
  LEFT JOIN aufk ON prps~pspnr = aufk~pspel
  INTO TABLE @DATA(lt_prps)
  .
SORT lt_prps BY psphi.
```

| 对比 | `FOR ALL ENTRIES` | `JOIN @itab` |
|------|-------------------|--------------|
| 需要去重 | 是 | 否 |
| 需要判空 | 是（否则全量查询） | 否（空表 = 无结果） |
| 需要排序 | 需要（辅助 READ TABLE） | 需要（后续 BINARY SEARCH） |
| 适合场景 | 关联字段少、跨多表补充 | 一对多关联、JOIN 多表 |

> **优先使用 `JOIN @itab`**，省去去重和判空的步骤。

#### 主表 + 子表整合模式（LOOP + READ TABLE BINARY SEARCH + LOOP FROM sy-tabix）

查询接口典型的数据整合模式：主表 LOOP，子表 READ TABLE BINARY SEARCH 定位，然后 LOOP FROM sy-tabix 处理同 key 的多条记录。

```abap
"lt_proj: 主表（项目）
"lt_prps: 子表（WBS），已按 psphi SORT
LOOP AT lt_proj INTO DATA(ls_proj).
  CLEAR ls_out.
  MOVE-CORRESPONDING ls_proj TO ls_out.    "主表字段

  "BINARY SEARCH 定位子表第一条匹配记录
  READ TABLE lt_prps INTO DATA(ls_prps_tmp)
    WITH KEY psphi = ls_proj-pspnr BINARY SEARCH.
  IF sy-subrc = 0.
    "从 sy-tabix 开始循环，同 key 的记录连续存放
    LOOP AT lt_prps INTO DATA(ls_prps) FROM sy-tabix.
      IF ls_prps-psphi <> ls_proj-pspnr.
        EXIT.  "key 变化，退出
      ENDIF.
      CLEAR ls_wbs.
      MOVE-CORRESPONDING ls_prps TO ls_wbs.
      APPEND ls_wbs TO ls_out-wbs.          "子表嵌套
    ENDLOOP.
  ENDIF.

  APPEND ls_out TO o_resp-res.
ENDLOOP.
```

**模式要点**：

| 步骤 | 关键点 |
|------|--------|
| 前置条件 | 子表必须按关联 key `SORT` |
| 定位 | `READ TABLE ... BINARY SEARCH` 定位到第一条匹配记录 |
| 遍历 | `LOOP AT ... FROM sy-tabix` 从定位位置开始 |
| 退出 | `IF key <> ... EXIT.` — 同 key 记录连续，key 变化即退出 |
| 嵌套 | 子表数据 `APPEND` 到主行内表字段（如 `ls_out-wbs`） |

> 来源：`ZFM_PSI001` 库存查询接口 — 项目(WBS)查询场景。

#### CHECK 跳过模式

当分支内已设置错误状态后，使用 `CHECK` 跳过最终响应设置：

```abap
"分支内已设置 MSGTY/MSGTX
IF some_error_condition.
  o_resp-msgty = 'E'.
  o_resp-msgtx = 'xxx错误'.
  RETURN.
ENDIF.

"最终响应设置
CHECK o_resp-msgty IS INITIAL.  "如果分支已设置错误，跳过

IF lt_out IS INITIAL.
  o_resp-msgty = 'E'.
  o_resp-msgtx = '查询无数据！'.
ELSE.
  o_resp-msgty = 'S'.
  o_resp-msgtx = '查询成功！'.
  o_resp-resp = lt_out.
ENDIF.
```

> `CHECK o_resp-msgty IS INITIAL` 确保只在尚未设置错误时才设置最终响应，避免覆盖分支内的错误信息。

---

## 通用规范

### 命名规范

> 函数组与函数模块的命名约定见 [核心要求 → 命名约定](#命名约定)，此处不再重复。

#### BAPI 函数模块

```
ZBAPI_<模块>_<描述>
```

| 示例 | 说明 |
|------|------|
| `ZBAPI_MM_CREATE_PO` | 创建采购订单 |
| `ZBAPI_FI_GET_BALANCE` | 获取科目余额 |

### 函数结构

#### 标准函数模块

```abap
FUNCTION zfm_xx_get_data.
*"----------------------------------------------------------------------
*"*"局部接口：
*"  IMPORTING
*"     VALUE(IV_MATNR) TYPE MATNR
*"     VALUE(IV_WERKS) TYPE WERKS_D OPTIONAL
*"  EXPORTING
*"     VALUE(EV_COUNT) TYPE I
*"     VALUE(ET_RESULT) TYPE ZT_XX_RESULT
*"  TABLES
*"     ET_DATA STRUCTURE ZST_XX_DATA OPTIONAL
*"  EXCEPTIONS
*"      NO_DATA_FOUND
*"      INVALID_INPUT
*"----------------------------------------------------------------------

  DATA: lv_error TYPE flag.

  "1. 参数校验
  IF iv_matnr IS INITIAL.
    RAISE invalid_input.
  ENDIF.

  "2. 业务逻辑
  SELECT matnr, maktx, meins
    FROM mara AS t00
    INTO TABLE @et_result
   WHERE matnr = @iv_matnr
     .

  "3. 结果处理
  IF sy-subrc <> 0.
    RAISE no_data_found.
  ENDIF.

  ev_count = lines( et_result ).

ENDFUNCTION.
```

### 参数规范

#### 参数方向

| 方向 | 前缀 | 说明 | 示例 |
|------|------|------|------|
| `IMPORTING` | `IV_` / `I_` | 输入参数 | `IV_MATNR`, `I_BUKRS` |
| `EXPORTING` | `EV_` / `E_` | 输出参数 | `EV_COUNT`, `E_MESSAGE` |
| `CHANGING` | `CV_` / `C_` | 修改参数 | `CV_STATUS`, `C_DATA` |
| `TABLES` | `ET_` / `IT_` / `CT_` | 内表参数 | `ET_DATA`, `IT_KEYS`, `CT_RESULT` |

#### 参数设计原则

```abap
"❌ 错误 — 必填参数过多，没有默认值
FUNCTION zmf_create_order.
*"  IMPORTING
*"     VALUE(IV_KUNNR) TYPE KUNNR
*"     VALUE(IV_VKORG) TYPE VKORG
*"     VALUE(IV_VTWEG) TYPE VTWEG
*"     VALUE(IV_SPART) TYPE SPART

"✅ 正确 — 必填参数精简，选填参数有 OPTIONAL
FUNCTION zfm_create_order.
*"  IMPORTING
*"     VALUE(IV_KUNNR) TYPE KUNNR
*"     VALUE(IV_VKORG) TYPE VKORG OPTIONAL
*"     VALUE(IV_VTWEG) TYPE VTWEG OPTIONAL
*"     VALUE(IV_SPART) TYPE SPART DEFAULT '00'
```

**原则**：
- 入参用 `VALUE()` 传递
- 选填参数标注 `OPTIONAL` 或 `DEFAULT`
- 内表参数优先用 `TABLES`（历史兼容）或 `CHANGING`
- 避免使用 `TABLES` 参数构造函数，新代码优先用 IMPORT/EXPORT 结构体

### 异常处理

#### 声明异常

```abap
FUNCTION zfm_validate_data.
*"  EXCEPTIONS
*"      INVALID_PARAMETER
*"      NO_AUTHORIZATION
*"      DATA_NOT_FOUND
*"      SYSTEM_ERROR
```

#### 抛出异常

```abap
"使用 RAISE <exception>
IF iv_matnr IS INITIAL.
  RAISE invalid_parameter.
ENDIF.

"使用 MESSAGE ... RAISING（带消息）
IF sy-subrc <> 0.
  MESSAGE e001(zmm) RAISING data_not_found.
ENDIF.
```

#### 调用方异常处理

```abap
CALL FUNCTION 'ZFM_VALIDATE_DATA'
  EXPORTING
    iv_matnr = lv_matnr
  EXCEPTIONS
    invalid_parameter = 1
    no_authorization  = 2
    data_not_found    = 3
    system_error      = 4
    OTHERS            = 99.

CASE sy-subrc.
  WHEN 0.
    "正常处理
  WHEN 1.
    MESSAGE '参数无效' TYPE 'E'.
  WHEN 2.
    MESSAGE '无权限' TYPE 'E'.
  WHEN 3.
    MESSAGE '数据未找到' TYPE 'E'.
  WHEN OTHERS.
    MESSAGE '系统错误' TYPE 'E'.
ENDCASE.
```

**原则**：
- 每个函数模块至少声明基本的异常
- 调用方必须检查 `sy-subrc`，处理所有声明的异常
- `OTHERS` 必须设置，用于兜底未预期的异常
- 命名使用 `snake_case`，与 SAP 标准风格一致

### RFC 函数模块

#### 命名与标记

RFC 函数模块必须在函数属性中勾选 **"Remote-Enabled Module"**。

```abap
"RFC 函数定义示例
FUNCTION zfm_rfc_get_data.
*"----------------------------------------------------------------------
*"*"远程调用函数模块
*"----------------------------------------------------------------------
*"  IMPORTING
*"     VALUE(IV_MATNR) TYPE MATNR
*"  EXPORTING
*"     VALUE(ES_RESULT) TYPE ZST_XX_RESULT
*"  EXCEPTIONS
*"      NO_DATA_FOUND
*"----------------------------------------------------------------------

  "实现
ENDFUNCTION.
```

#### RFC 注意事项

| 规则 | 原因 |
|------|------|
| 不使用 `TABLES` 参数 | RFC 传大内表效率低，用 `IMPORTING`/`EXPORTING` 结构体 |
| 参数尽量扁平 | 避免深层嵌套结构，减少序列化开销 |
| 不返回 `TABLE` 参数 | 内表大数据通过 `EXPORTING` 只传必要的行 |
| 不调用 `COMMIT WORK` | 由调用方控制事务边界 |
| 不在 RFC 中做 UI 操作 | SAP GUI 不存在于 RFC 上下文 |

#### BAPI 规范

BAPI 函数模块遵循 SAP 标准 BAPI 规范：

```abap
FUNCTION zbapi_mm_create_po.
*"----------------------------------------------------------------------
*"  IMPORTING
*"     VALUE(IS_HEADER) TYPE ZBAPI_MM_PO_HEADER
*"     VALUE(IT_ITEMS)  TYPE ZBAPI_MM_PO_ITEMS_T
*"  EXPORTING
*"     VALUE(ES_RETURN) TYPE BAPIRET2
*"  TABLES
*"     ET_RETURN       TYPE BAPIRET2 "返回多条消息
*"----------------------------------------------------------------------

  "业务逻辑
  TRY.
      "创建订单
      CALL FUNCTION 'BAPI_PO_CREATE'
        EXPORTING
          poheader = ls_header
        IMPORTING
          return   = ls_return.

    CATCH cx_root INTO DATA(lx_error).
      "失败时填充 BAPIRET2
      es_return-type   = 'E'.
      es_return-message = lx_error->get_text( ).
      RETURN.
  ENDTRY.

  "成功时填充 BAPIRET2
  es_return-type = 'S'.
  es_return-message = '创建成功'.

ENDFUNCTION.
```

**BAPIRET2 返回结构**：

| 字段 | 说明 |
|------|------|
| `TYPE` | `S`=成功, `E`=错误, `W`=警告, `I`=信息 |
| `ID` | 消息类 |
| `NUMBER` | 消息号 |
| `MESSAGE` | 消息文本 |
| `MESSAGE_V1`~`V4` | 消息变量 |

### 函数模块文档

#### 注释规范

```abap
FUNCTION zfm_xx_get_data.
*"----------------------------------------------------------------------
*"*"局部接口：
*"  IMPORTING
*"     VALUE(IV_MATNR) TYPE MATNR
*"  EXPORTING
*"     VALUE(ET_RESULT) TYPE ZT_XX_RESULT
*"  EXCEPTIONS
*"      NO_DATA_FOUND
*"----------------------------------------------------------------------
*" 函数说明：
*"   根据物料号获取物料主数据
*" 调用前提：
*"   需要 MM 模块权限
*" 调用示例：
*"   CALL FUNCTION 'ZFM_XX_GET_DATA'
*"     EXPORTING
*"       IV_MATNR     = 'MAT001'
*"     IMPORTING
*"       ET_RESULT    = DATA(lt_result)
*"     EXCEPTIONS
*"       NO_DATA_FOUND = 1.
*" 变更记录：
*"   2026-01-01  HANDAI  创建
*"   2026-03-15  HANDAI  增加 IV_WERKS 参数
*"----------------------------------------------------------------------

  "实现...

ENDFUNCTION.
```

#### 文档要求

| 内容 | 必填 | 说明 |
|------|------|------|
| 接口参数注释 | 是 | SAP 自动生成，保留不删 |
| 函数说明 | 是 | 一句话描述函数做什么 |
| 调用前提 | 否 | 权限、系统状态等前置条件 |
| 调用示例 | 推荐 | 帮助其他开发者快速理解用法 |
| 变更记录 | 推荐 | 记录修改历史 |

#### 接口文档模板（REST API 场景）

开发 REST API 接口时，应输出一份接口说明文档，包含以下标准结构。参考来源：HAND SAP CDC 标准化接口文档 V1.0（35 个接口统一模板）。

**文档模板结构**：

```text
1. 返回目录          ← 链接到目录表
2. 接口名称          ← 中文名称，如"物料主数据维护接口"
3. 接口说明          ← 功能描述、注意事项
4. 字段定义表        ← 表头：字段 | 类型 | 最大长度 | 是否必填 | 名称 | 说明
   ├── 请求头        ← UUID / FSYSID / ZNUMB（通用字段，所有接口共用）
   ├── 请求体        ← 按业务结构分段，每段用"结构名-xxx"标记
   │   ├── 结构-head     ← 抬头/控制字段
   │   ├── 结构-item     ← 行项目表
   │   ├── 结构-schedule ← 计划行（SD 场景）
   │   └── 结构-cond     ← 定价条件
   └── 响应体        ← MSGTY / MSGTX / UUID / SAPNUM 等
5. 请求示例          ← 完整 JSON 示例（含 UUID / ZNUMB / FSYSID / REQ）
6. 响应示例-成功     ← msgty=S 的返回 JSON
7. 响应示例-失败     ← msgty=E 的返回 JSON
```

**字段定义表格式**：

每行一条字段，六列标准：

| 字段 | 类型 | 最大长度 | 是否必填 | 名称 | 说明 |
|------|------|----------|----------|------|------|
| `MATNR` | CHAR | 40 | 是 | 物料编号 | 18 位，带前导零 |
| `WERKS` | CHAR | 4 | 是 | 工厂 | |
| `LGORT` | CHAR | 4 | 否 | 库存地点 | |
| `MAKTX` | CHAR | 40 | 是 | 物料描述 | |

**分段规则**：

请求体字段按业务子结构分组，每组用一行标记开头：

| 标记 | 说明 |
|------|------|
| `结构-head` | 抬头数据（如订单抬头、请求头控制字段） |
| `结构-item` | 行项目表（一对多关系） |
| `结构-xxx` | 其他子结构，xxx 为表/结构名 |

**JSON 示例要求**：

```json
{
  "ZNUMB": "MMI001",              // ← 接口编号
  "UUID": "{{$guid}}",            // ← 自动生成标识
  "FSYSID": "BEATBOT",            // ← 调用系统标识
  "REQ": {
    "head": {
      "matnr": "1000000043",
      "basicView": "X"
    },
    "item": [
      {
        "matnr": "1000000043",
        "werks": "1000",
        "menge": 10
      }
    ]
  }
}
```

- 请求示例必须是完整可用的 JSON（含 UUID / ZNUMB / FSYSID）
- 字段名使用 camelCase（DDIC snake_case 转换）
- 响应示例分成功/失败两种场景
- 包含必要的注释说明固定值

### JSON 处理与 REST 接口

> 基础 JSON 序列化/反序列化（`/ui2/cl_json`）与 JSON 格式判断见 [abap-coding.md](abap-coding.md#json-处理)，此处只保留接口 REST 场景的完整动态调用流程。

#### 动态调用函数模块

根据配置表动态决定调用哪个函数模块：

```abap
"1. 查找配置
SELECT SINGLE * FROM ztrest_conf
  INTO @DATA(gs_config)
 WHERE znumb = @iv_znumb
   AND zisst = 'X'.

IF gs_config IS INITIAL.
  "接口未配置
  ev_msgty = 'E'.
  MESSAGE s006(zgl01) INTO ev_msgtx.
  RETURN.
ENDIF.

"2. 动态创建参数结构
CREATE DATA lv_req TYPE (gs_config-zipara).
ASSIGN lv_req->* TO FIELD-SYMBOL(<fs_req>).

CREATE DATA lv_resp TYPE (gs_config-zopara).
ASSIGN lv_resp->* TO FIELD-SYMBOL(<fs_resp>).

"3. JSON → 动态请求结构
/ui2/cl_json=>deserialize(
  EXPORTING json        = iv_request
            pretty_name = /ui2/cl_json=>pretty_mode-camel_case
  CHANGING  data        = <fs_req> ).

"4. 动态调用函数
TRY.
    CALL FUNCTION gs_config-zfname
      EXPORTING
        i_req  = <fs_req>
      IMPORTING
        o_resp = <fs_resp>.
  CATCH cx_root INTO DATA(lx_error).
    ev_msgty = 'E'.
    ev_msgtx = lx_error->get_text( ).
    RETURN.
ENDTRY.

"5. 响应 → JSON
ev_response = /ui2/cl_json=>serialize(
  data        = <fs_resp>
  pretty_name = /ui2/cl_json=>pretty_mode-camel_case ).
```

#### ZTREST_CONF 接口配置表

| 字段 | 类型 | 说明 |
|------|------|------|
| `ZNUMB` | CHAR30 | 接口编号（主键），如 `SDI008` |
| `ZNAME` | CHAR | 接口名称 |
| `ZIFTY` | CHAR | 接口类型 |
| `ZISST` | CHAR | 接口状态（`X`=启用） |
| `ZFNAME` | CHAR30 | 函数模块名 |
| `ZIPARA` | CHAR | 导入参数结构名 |
| `ZOPARA` | CHAR | 导出参数结构名 |
| `TSYSID` | CHAR | 目标系统 |

---

## 禁止事项

| 禁止 | 原因 | 替代方案 |
|------|------|----------|
| 函数模块中 `COMMIT WORK` | 由调用方控制事务 | 只做业务逻辑，提交由调用方决定 |
| 函数模块中 `CALL SCREEN` | 函数模块应该是无 UI 的 | 在调用方做 UI 交互 |
| 函数模块中 `SUBMIT` 调用 | 绕过函数模块的封装 | 提取公共逻辑到独立的函数模块 |
| 函数模块中直接修改全局变量 | 破坏封装性 | 通过参数传递 |
| 函数模块中写死消息文本 | 不支持国际化 | 使用消息类 (MESSAGE ID) |
| 查询接口中调用 `COMMIT WORK` | 查询不修改数据，不需要提交 | 直接返回数据 |
| 查询接口表格返回时用 `ZSREST_OUT` | 表格返回需追加 `RESP` 表字段 | 新建 `ZSXXI001_RESP`，复制公共字段 + `RESP` |
| 函数 `TABLES` 参数里内联定义结构 | 结构应可复用、可追溯 | 创建 DDIC 结构（`ZSXXI001_OUT`）+ 表类型（`ZTTXXI001_OUT`） |
| 写入接口忽略 TESTRUN 模式 | 可能直接写入错误数据 | 先测试运行再正式运行 |
