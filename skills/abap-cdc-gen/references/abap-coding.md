---
name: abap-coding
description: ABAP 编码规范 — HAND SAP ABAP开发规范 V2.0，命名、格式化、SELECT、注释、错误处理、ALV、DEFINE宏、动态编程、JSON处理、现代语法
---

# ABAP 编码规范

## 核心要求

**所有 ABAP 代码必须遵循以下规范。不遵守的代码在 Code Review 中必须修正。**

**边界条件** — 以下情况不要自作主张：
- 项目已有不同编码规范 → 以项目规范为准
- SAP 标准对象（非 Z/Y 开头）→ 不修改，除非用户明确要求
- 不确定用什么命名前缀 → 查上表，不要造新的
- 不确定的字段名、表名、程序名、函数名、类名 → **必须停止，向用户确认**，禁止 AI 自己发挥
- 不确定的需求 → **必须停止，向用户确认**，不猜测、不假设、不编造

### 数据安全红线

| 禁止 | 原因 | 替代方案 |
|------|------|----------|
| 直接 INSERT/UPDATE/DELETE/MODIFY 标准表 | 绕过 SAP 校验，破坏数据一致性 | 使用 BAPI/BDC/IDoc 等标准接口 |
| 直接修改 SAP 标准程序/函数/类 | 升级时被覆盖，且无法追溯 | 使用增强 (BAdI/User Exit/隐式增强) |

### MODIFY 使用规范

`MODIFY` 是 ABAP 中用于向内表或数据库表写入数据的语句，根据主键自动判断：**存在则更新非主键字段，不存在则新增**。

#### 适用场景

| 场景 | 推荐 | 说明 |
|------|------|------|
| 配置表单条维护（如 ZTREST_CONF） | `MODIFY` 结构体 | 无需 `SELECT` 判断记录是否存在，一条语句完成新增/更新 |
| 配置表批量维护（多条记录） | 先处理内表，再 `MODIFY` 内表到数据库 | 避免逐条操作数据库，提升性能 |
| 业务数据表（含 BAPI 调用） | `INSERT`/`UPDATE` + `BAPI_TRANSACTION_COMMIT` | 需要 TESTRUN 两阶段提交，事务控制 |
| 内表修改 | `MODIFY` | 按主键或索引修改内表行 |

#### 单条记录 MODIFY

```abap
"✅ 推荐 — MODIFY 一条语句完成新增/更新
DATA: ls_conf TYPE ztrest_conf.

MOVE-CORRESPONDING i_req-req TO ls_conf.
IF ls_conf-zisst IS INITIAL.
  ls_conf-zisst = 'X'.
ENDIF.

MODIFY ztrest_conf FROM ls_conf.
IF sy-subrc = 0.
  o_resp-msgty = 'S'.
  o_resp-msgtx = '操作成功'.
ELSE.
  o_resp-msgty = 'E'.
  o_resp-msgtx = '操作失败'.
ENDIF.
```

```abap
"❌ 不推荐 — 手动 SELECT + INSERT/UPDATE 判断
SELECT SINGLE * FROM ztrest_conf INTO ls_conf WHERE znumb = lv_znumb.
IF sy-subrc = 0.
  "更新
  ...
  UPDATE ztrest_conf FROM ls_conf.
ELSE.
  "新增
  ...
  INSERT ztrest_conf FROM ls_conf.
ENDIF.
```

#### 多条记录批量 MODIFY

多条记录时，**先在内表中处理好所有数据，再一次性 `MODIFY` 到数据库**，避免逐条操作数据库：

```abap
"✅ 推荐 — 先处理内表，再批量 MODIFY 到数据库
DATA: lt_conf TYPE STANDARD TABLE OF ztrest_conf.

"从输入中构建内表
LOOP AT i_req-req-items INTO DATA(ls_item).
  DATA(ls_conf) = CORRESPONDING #( ls_item ).
  IF ls_conf-zisst IS INITIAL.
    ls_conf-zisst = 'X'.
  ENDIF.
  APPEND ls_conf TO lt_conf.
ENDLOOP.

"一次性 MODIFY 到数据库
MODIFY ztrest_conf FROM TABLE lt_conf.
IF sy-subrc = 0.
  o_resp-msgty = 'S'.
  o_resp-msgtx = '批量操作成功'.
ELSE.
  o_resp-msgty = 'E'.
  o_resp-msgtx = '批量操作失败'.
ENDIF.
```

```abap
"❌ 不推荐 — 逐条 MODIFY 数据库，性能差
LOOP AT i_req-req-items INTO DATA(ls_item).
  DATA(ls_conf) = CORRESPONDING #( ls_item ).
  MODIFY ztrest_conf FROM ls_conf.
ENDLOOP.
```

---

## 目录

- [核心要求](#核心要求)
  - [数据安全红线](#数据安全红线)
  - [基本规则](#基本规则)
  - [变量声明](#变量声明)
  - [操作符间距](#操作符间距)
- [程序头注释模板](#程序头注释模板)
- [代码段注释格式](#代码段注释格式)
- [命名规范](#命名规范)
  - [DDIC 对象命名](#ddic-对象命名)
- [选择屏幕设计规范](#选择屏幕设计规范)
- [SELECT 语句](#select-语句)
- [注释](#注释)
- [错误处理](#错误处理)
- [ALV 规范](#alv-规范)
- [现代 ABAP 语法](#现代-abap-语法)
- [DEFINE 宏](#define-宏)
- [动态编程](#动态编程)
- [字符串处理](#字符串处理)
- [金额符号处理](#金额符号处理)
- [单位转换](#单位转换)
- [编号范围处理](#编号范围处理)
- [分类视图处理](#分类视图处理)
- [JSON 处理](#json-处理)
- [相关规范文件](#相关规范文件)

---

### 基本规则

**关键字 UPPERCASE**，**2 空格缩进**，**每行 ≤ 72 字符**。

```abap
"❌ 错误
data lv_matnr like mara-matnr.
if sy-subrc = 0.
    write 'success'.

"✅ 正确
DATA lv_matnr TYPE matnr.
IF sy-subrc = 0.
  WRITE 'success'.
```

### 变量声明

禁止 `LIKE`，使用 `TYPE`。内联声明优先。

```abap
"❌ 错误
DATA lv_matnr LIKE mara-matnr.
DATA lt_mara TYPE STANDARD TABLE OF mara.
lt_mara = VALUE #( ... ).

"✅ 正确
DATA lv_matnr TYPE matnr.
SELECT * FROM mara INTO TABLE @DATA(lt_mara).
```

### 操作符间距

操作符两侧各一个空格。

```abap
"❌ 错误
lv_result = lv_a+lv_b.

"✅ 正确
lv_result = lv_a + lv_b.
```

---

## 程序头注释模板

每个程序文件必须包含标准头注释。AI 生成代码时，根据代码生成前确认清单的信息自动填入真实数据。

### 标准模板（AI 生成代码）

```abap
*&---------------------------------------------------------------------*
*& 单位/APPLICANT                  : HAND SAP
*& 程序名称/PROGRAM NAME.          : {program_name}
*& 程序描述/PROGRAM DES.           : {description}
*& 开发编号/FS NO.                 : {req_no}
*& 功能顾问/FUNCTION CONST.        : {applicant}
*& 申请日期/APPLICATION DATE       : {app_date}
*& 技术顾问/DEVELOP CONST.         : HANDAI
*& 开发日期/DEVELOP DATE.          : {finish_date}
*&---------------------------------------------------------------------*
*&摘要：
*&   一. 业务背景
*&      {remark}
*&   二. 使用场景
*&      通过 TCODE: {program_name} 运行
*&   三. 程序使用：
*&       运行TCODE:{program_name}
*&注意：
*&   一. 代码规范
*&       遵循 《汉得SAP标准化程序开发规范 V1.0》；
*&   二. 代码更改（标准化代码使用标准化发布的模板代码）
*&---------------------------------------------------------------------*
*&变更记录：                                                           *
*&DATE         DEVELOPER           REQNO       DESCRIPTIONS            *
*& ==========  ==================  ==========  ======================== *
*& {change_date} HANDAI              {req_no}     Create                 *
*&---------------------------------------------------------------------*
```

### 模板变量说明

| 变量 | 来源 | 示例值 |
|------|------|--------|
| `{program_name}` | 代码生成前确认清单 — 对象名称 | `ZMMR001` |
| `{description}` | 程序功能描述，一句话说清楚 | `物料库龄报表` |
| `{applicant}` | 功能顾问姓名（无输入则留空） | `张三` |
| `{app_date}` | 当前日期 | `2026.08.21` |
| `{finish_date}` | 当前日期 | `2026.08.21` |
| `{remark}` | 业务背景概要（1,2,3...） | `1). Excel 模板上传; 2). 数据校验;` |
| `{change_date}` | 当前日期 | `2026.08.21` |
| `{req_no}` | 代码生成前确认清单 — 请求号（`$TMP` 时留空） | `ED1K900001` |

### 头注释字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| 单位/APPLICANT | 是 | 固定值 `HAND SAP` |
| 程序名称/PROGRAM NAME. | 是 | 程序名，与 REPORT 语句一致 |
| 程序描述/PROGRAM DES. | 是 | 程序功能描述，一句话说清楚 |
| 开发编号/FS NO. | 否 | 请求号/传输号 |
| 功能顾问/FUNCTION CONST. | 否 | 功能顾问姓名 |
| 申请日期/APPLICATION DATE | 否 | 需求提出日期 |
| 技术顾问/DEVELOP CONST. | 是 | 技术顾问，AI 生成代码署名 `HANDAI` |
| 开发日期/DEVELOP DATE. | 是 | 完成日期 |
| 摘要 | 推荐 | 业务背景（一）使用场景（二）程序使用（三） |
| 注意 | 推荐 | 代码规范声明 + 代码更改约束 |
| 变更记录 | 是 | 每次修改必须登记 |

### 变更记录格式

```
*&DATE         DEVELOPER           REQNO       DESCRIPTIONS
*& ==========  ==================  ==========  ========================
*& YYYYMMDD     HANDAI               Transport    修改说明
```

### 注释分隔线规范

**注释分隔线统一使用单横杠 `-`，禁止双等号 `=`。**

```abap
"❌ 错误 — 双等号分隔线
*&=====================================================================*
*& Report ZMMR001
*&=====================================================================*

"✅ 正确 — 单横杠分隔线
*&---------------------------------------------------------------------*
*& Report ZMMR001
*&---------------------------------------------------------------------*
```

变更记录中的表格分隔线除外（`==========` 用于对齐）。

---

## 代码段注释格式

### 数据定义区

```abap
*----------------------------------------------------------------------*
*   type-pools define（定义使用到的类型池）
*----------------------------------------------------------------------*
TYPE-POOLS: slis.

*----------------------------------------------------------------------*
*   tables define（定义选择屏幕所要参照的表名）
*----------------------------------------------------------------------*
TABLES: mara, makt.

*----------------------------------------------------------------------*
*   define internal types (定义类型结构)
*----------------------------------------------------------------------*
TYPES: BEGIN OF ty_data,
         matnr TYPE matnr,
         maktx TYPE maktx,
       END OF ty_data.

*----------------------------------------------------------------------*
*   define internal tables (定义内表结构)
*----------------------------------------------------------------------*
DATA: gt_data TYPE TABLE OF ty_data,
      gs_data TYPE ty_data.

*----------------------------------------------------------------------*
*   define global variable（定义全局变量）
*----------------------------------------------------------------------*
DATA: gv_count TYPE i,
      gv_flag  TYPE flag.
```

**关于 `TABLES` 语句**：

`TABLES` 语句在现代 ABAP 中已过时（不应用于数据访问），但在报表程序中**仍然需要**声明，用于 `SELECT-OPTIONS` 和 `PARAMETERS` 参照 DDIC 表字段：

```abap
TABLES: mara.                      " 必须声明，否则下面语句报错
SELECT-OPTIONS: s_matnr FOR mara-matnr.  " 参照 DDIC 表字段
PARAMETERS:     p_mtart TYPE mara-mtart. " 参照 DDIC 表字段类型
```

**关于 `TYPE-POOLS: slis.`**：

ALV 报表程序需要 `TYPE-POOLS: slis.` 声明，用于 ALV 回调类型和工具函数：

```abap
TYPE-POOLS: slis.
DATA: gt_exclude TYPE slis_t_extab,      " ALV 工具栏排除表
      gs_layout  TYPE lvc_s_layo,        " ALV 布局
      gs_selfield TYPE slis_selfield.    " ALV 双击/单击事件
```

**注意**：`TYPE-POOLS: slis.` 在现代 ABAP 中保留，仅为兼容 ALV 回调类型。`LVC` 布局和字段目录类型 (`lvc_s_layo`, `lvc_s_fcat`) 不需要 TYPE-POOLS 声明。

### 选择屏幕

```abap
*&---------------------------------------------------------------------*
*& selection-screen (选择屏幕)                                          *
*&---------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK bl1 WITH FRAME TITLE TEXT-001.
  SELECT-OPTIONS: s_matnr FOR mara-matnr,
                  s_mtart FOR mara-mtart.
  PARAMETERS:     p_date  TYPE sy-datum DEFAULT sy-datum.
SELECTION-SCREEN END OF BLOCK bl1.
```

### 事件处理

```abap
*&---------------------------------------------------------------------*
*& initialzation (选择屏幕前初始化)                                     *
*&---------------------------------------------------------------------*
INITIALIZATION.

*----------------------------------------------------------------------*
*  at selection-screen（选择屏幕输入后检查）                             *
*----------------------------------------------------------------------*
AT SELECTION-SCREEN.

*----------------------------------------------------------------------*
*  at selection-screen output（选择屏幕PBO事件）                         *
*----------------------------------------------------------------------*
AT SELECTION-SCREEN OUTPUT.

*&---------------------------------------------------------------------*
*& Start-of-selection (开始选择屏幕)                                     *
*&---------------------------------------------------------------------*
START-OF-SELECTION.
  PERFORM frm_get_data.
  PERFORM frm_display_alv.

END-OF-SELECTION.
```

### FORM 子程序注释

```abap
*&---------------------------------------------------------------------*
*&      Form  FRM_CHECK_AUTHORITY
*&---------------------------------------------------------------------*
*       权限检查
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM frm_check_authority .
  AUTHORITY-CHECK OBJECT 'Z_AUTH_OBJ'
    ID 'ACTVT' FIELD '03'.
  IF sy-subrc <> 0.
    MESSAGE s000(00) WITH '无权限' DISPLAY LIKE 'E'.
    LEAVE LIST-PROCESSING.
  ENDIF.
ENDFORM.
```

**FORM 注释要求**：
- 第一行 `*&` 分隔线
- 第二行：`*&      Form  FORM_NAME`
- 第三行 `*&` 分隔线
- 第四行：`*       功能描述（中文）`
- 第五行 `*` 分隔线
- 第六行：`*  --> p1` 输入参数说明
- 第七行：`*  <-- p2` 输出参数说明
- 第八行 `*` 分隔线
- 实际参数在代码中通过 `USING`/`CHANGING` 声明

**FORM 命名规范**：所有子程序前缀 `frm_`，如 `frm_get_data`、`frm_display_alv`、`frm_set_screen`。

---

## 命名规范

### 前缀速查表

| 作用域 | 前缀 | 示例 |
|--------|------|------|
| 全局变量 | `GV_` | `GV_COUNT`, `GV_NAME` |
| 局部变量 | `LV_` | `LV_INDEX`, `LV_MATNR` |
| 常量 | `GC_` | `GC_FLAG_X`, `GC_MAX_ROWS` |
| 全局内表 | `GT_` | `GT_DATA`, `GT_ITEMS` |
| 局部内表 | `LT_` | `LT_ITEMS`, `LT_RESULT` |
| 工作区 | `GS_` / `LS_` | `GS_ROW`, `LS_MARA` |
| 字段符号 | `<FS_>` | `<FS_DATA>`, `<FS_LINE>` |
| 函数 IMPORT | `I_` | `I_MATNR`, `I_BUKRS` |
| 函数 EXPORT | `E_` | `E_RESULT`, `E_MESSAGE` |
| 选择屏幕 | `P_` | `P_DATE`, `P_BUKRS` |
| SELECT-OPTIONS | `S_` | `S_MATNR`, `S_ERDAT` |

### 命名模式

```abap
"❌ 错误 — 无意义缩写、无前缀
DATA: a TYPE i, b TYPE string.

"✅ 正确 — 前缀 + 描述性名称
DATA: lv_counter TYPE i,
      lv_message TYPE string.
```

### DDIC 对象命名

DDIC 对象按以下前缀命名。**接口函数模块的结构/表类型命名（`_REQ`/`_IN`/`_RESP`/`_OUT` 等后缀）见 [abap-interface.md](abap-interface.md#ddic-先行开发流程)**。

| 对象类型 | 前缀 | 模式 | 示例 |
|----------|------|------|------|
| 域 | `ZD` | `ZD{描述}` | `ZDNUMB`, `ZDFSYSID`, `ZDSYSUUID_C32` |
| 数据元素 | `ZE` | `ZE{描述}` | `ZEQUAN13`, `ZEDEC3`, `ZENUMB`, `ZEFSYSID` |
| 结构 | `ZS` | `ZS` + 描述 | `ZSMM_MARA`, `ZSPSI001_OUT` |
| 表类型 | `ZTT` | `ZTT` + 描述 | `ZTTMM_MARC`, `ZTTPSI001_OUT` |
| 函数模块 | `ZFM` | `ZFM_{模块}I{序号}` | `ZFM_MMI001`, `ZFM_PSI001` |
| 函数组 | `ZFG` | `ZFG_{模块}` | `ZFG_MM`, `ZFG_PS` |

**字段命名原则**：

1. **优先使用 SAP 标准数据元素** — 如 `MTART`, `MBRSH`, `LVORM`, `WERKS_D`, `MAKTX`, `MEINS` 等
2. **标准字段不存在时创建 Z 字段** — 如 `ZEQUAN13` (QUAN 13 3), `ZEDEC3` (DEC 3), `ZEDEC52` (DEC 5 2)
3. **Z 数据元素命名** — `ZE` + 简短描述（全大写），如 `ZE` + `QUAN13` = `ZEQUAN13`
4. **Z 域名命名** — `ZD` + 简短描述（全大写），如 `ZD` + `NUMB` = `ZDNUMB`

```abap
"✅ 标准字段优先 — 直接使用 SAP 标准数据元素
define structure zsmm_mara {
  mtart  : mtart;    "SAP 标准数据元素
  mbrsh  : mbrsh;    "SAP 标准数据元素
  meins  : meins;    "SAP 标准数据元素
  ntgew  : zequan13; "Z 数据元素（QUAN 13 3 无标准对应）
  brgew  : zequan13; "Z 数据元素（同上，复用）
}
```

---

## 选择屏幕设计规范

### 基本结构

选择屏幕使用 `SELECTION-SCREEN BEGIN OF BLOCK` 包裹，带 `FRAME` 边框和 `TITLE` 标题。标签文本使用 `TEXT-xxx` 维护，便于多语言翻译。

```abap
*&---------------------------------------------------------------------*
*& selection-screen (选择屏幕)
*&---------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK bl1 WITH FRAME TITLE TEXT-001.
  SELECT-OPTIONS: s_matnr FOR mara-matnr,
                  s_mtart FOR mara-mtart,
                  s_ersda FOR mara-ersda.
  PARAMETERS:     p_werks TYPE werks_d DEFAULT '1000'.
SELECTION-SCREEN END OF BLOCK bl1.
```

### 选择屏幕文本（MCP 生成程序的约定）

MCP 工具链没有维护文本池的接口，无法替开发者写入文本符号与选择文本。生成程序时**不在代码里硬编码标签**，文本一律留空并注释提示开发者补充：

- 框架标题：`TITLE` 直接引用文本符号（如 `TEXT-001`），不声明 `gv_blk1` 类标题变量、不在 `INITIALIZATION` 里硬编码中文（也顺带规避了标题变量被 DATA 重复声明的陷阱——标题/注释变量由语句隐式声明）；
- 字段标签：不写 `SELECTION-SCREEN COMMENT` 行充当字段标签，标签一律由**选择文本**（SE38 → 转到 → 文本元素 → 选择文本）提供；块内确需固定说明文字时，`COMMENT` 直接引用 `TEXT-xxx` 同样有效；
- 在选择屏幕块上方写醒目 `TODO` 注释，列出开发者需补充的文本清单（文本符号 + 各字段建议选择文本）；
- 文本未维护时的表现：框架标题为空、字段旁显示技术名（如 `S_MATNR`），**不影响编译激活与运行**，开发者交付前补齐即可。

```abap
* TODO 文本元素：请在 SE38 → 转到 → 文本元素 补充
*   文本符号 001 = 基本数据（框架标题）
*   选择文本 S_MATNR = 物料号、S_ERSDA = 创建日期、P_WERKS = 工厂
SELECTION-SCREEN BEGIN OF BLOCK bl1 WITH FRAME TITLE TEXT-001.
  SELECT-OPTIONS: s_matnr FOR mara-matnr,
                  s_ersda FOR mara-ersda.
  PARAMETERS:     p_werks TYPE werks_d DEFAULT '1000'.
SELECTION-SCREEN END OF BLOCK bl1.
```

### 单选按钮组

用于切换报表模式（如汇总/明细），使用 `RADIOBUTTON GROUP` + `USER-COMMAND` 触发 AT SELECTION-SCREEN OUTPUT 事件。

```abap
SELECTION-SCREEN BEGIN OF BLOCK bl2 WITH FRAME TITLE TEXT-002.
  PARAMETERS: p_sum   RADIOBUTTON GROUP rg1 DEFAULT 'X' USER-COMMAND uc1,
              p_det   RADIOBUTTON GROUP rg1.
SELECTION-SCREEN END OF BLOCK bl2.
```

### 动态屏幕控制

通过 `AT SELECTION-SCREEN OUTPUT` 事件 + `LOOP AT SCREEN` 实现选择屏幕字段的显示/隐藏和输入控制。

```abap
AT SELECTION-SCREEN OUTPUT.
  PERFORM frm_set_screen.

*&---------------------------------------------------------------------*
*&      Form  FRM_SET_SCREEN
*&---------------------------------------------------------------------*
*       动态控制选择屏幕字段显示
*----------------------------------------------------------------------*
FORM frm_set_screen .
  LOOP AT SCREEN.
    " 汇总模式：隐藏明细相关字段
    IF p_sum = 'X' AND screen-group1 = 'DET'.
      screen-invisible = 1.
      screen-input     = 0.
      MODIFY SCREEN.
    ENDIF.
    " 必填字段高亮
    IF screen-name = 'P_WERKS' AND p_werks IS INITIAL.
      screen-required = 2.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP.
ENDFORM.
```

**`screen-group1` 使用约定**：

| group1 值 | 用途 | 说明 |
|-----------|------|------|
| `DET` | 明细模式字段 | 仅在 `p_det = 'X'` 时显示 |
| `SUM` | 汇总模式字段 | 仅在 `p_sum = 'X'` 时显示 |
| `OPT` | 可选字段 | 可动态隐藏的高级选项 |

### F4 搜索帮助

通过 `AT SELECTION-SCREEN ON VALUE-REQUEST` 事件实现自定义搜索帮助。

```abap
AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_werks.
  PERFORM frm_f4_werks USING p_werks.

*&---------------------------------------------------------------------*
*&      Form  FRM_F4_WERKS
*&---------------------------------------------------------------------*
*       工厂 F4 搜索帮助
*----------------------------------------------------------------------*
FORM frm_f4_werks CHANGING cv_werks TYPE werks_d.
  DATA: lt_return TYPE TABLE OF ddshretval,
        ls_return TYPE ddshretval.

  SELECT werks AS retfield, name1 FROM t001w
    INTO TABLE @DATA(lt_values).

  CALL FUNCTION 'F4IF_INT_TABLE_VALUE_REQUEST'
    EXPORTING
      retfield    = 'WERKS'
      dynpprog    = sy-repid
      dynpnr      = sy-dynnr
      dynprofield = 'P_WERKS'
      value_org   = 'S'
    TABLES
      values      = lt_values
      return_tab  = lt_return.

  IF lt_return IS NOT INITIAL.
    READ TABLE lt_return INDEX 1 INTO ls_return.
    cv_werks = ls_return-fieldval.
  ENDIF.
ENDFORM.
```

### 禁止事项

| 禁止 | 说明 |
|------|------|
| 选择屏幕中写业务逻辑 | 仅做校验，业务逻辑放 START-OF-SELECTION |
| `AT SELECTION-SCREEN` 中直接 `MESSAGE 'E'` | 使用 `MESSAGE exxx(00) DISPLAY LIKE 'E'` + `STOP`，避免 dump |
| 硬编码标签文本 | 使用 `TEXT-xxx` 文本元素 |
| 忘记 `USER-COMMAND` | 单选按钮组切换显示时必须加 `USER-COMMAND` |

---

## SELECT 语句

### 格式规则

- 禁止 `SELECT *`，只取需要的字段
- 字段分行对齐，每行一个字段
- 使用 `AS t00` 别名（t00, t01, t02...）
- WHERE 条件对齐，`AND` 在行首
- 句号 `.` 单独一行

```abap
"❌ 错误
SELECT * FROM mara INTO TABLE @DATA(lt_mara) WHERE matnr = 'MAT001'.

"✅ 正确
SELECT matnr,        "t00
       mtart,        "t00
       meins,        "t00
       maktx         "t00
  FROM mara AS t00
  INTO TABLE @DATA(lt_mara)
 WHERE matnr IN @s_matnr
   AND mtart IN @s_mtart
   .
```

### 多表 JOIN

```abap
SELECT t00~matnr,
       t00~mtart,
       t01~maktx
  FROM mara  AS t00
  LEFT JOIN makt AS t01
    ON t00~matnr = t01~matnr
  INTO TABLE @DATA(lt_result)
 WHERE t00~mtart IN @s_mtart
   AND t01~spras = @sy-langu
   .
```

### FOR ALL ENTRIES 检查

使用 `FOR ALL ENTRIES` 前**必须**检查内表非空，否则会全量查询。

```abap
"❌ 错误 — 内表为空时全量查询
SELECT * FROM mara
  INTO TABLE lt_mara
  FOR ALL ENTRIES IN lt_keys
  WHERE matnr = lt_keys-matnr.

"✅ 正确 — 先检查非空
IF lt_keys IS NOT INITIAL.
  SELECT * FROM mara
    INTO TABLE lt_mara
    FOR ALL ENTRIES IN lt_keys
    WHERE matnr = lt_keys-matnr.
ENDIF.
```

---

## ⛔ 性能强制规则

**以下规则为性能红线，违反即拒绝 Code Review。**

### 1. 禁止 LOOP 中嵌套 LOOP

内表循环嵌套导致 O(n²) 复杂度，必须用其他方式替代。

```abap
"❌ 错误 — LOOP 嵌套 LOOP，数据量大时性能灾难
LOOP AT lt_head INTO DATA(ls_head).
  LOOP AT lt_item INTO DATA(ls_item)
    WHERE vbeln = ls_head-vbeln.
    "处理逻辑
  ENDLOOP.
ENDLOOP.

"✅ 正确 — 方案1：先按 key 排序 + READ TABLE BINARY SEARCH
SORT lt_item BY vbeln.
LOOP AT lt_head INTO DATA(ls_head).
  READ TABLE lt_item INTO DATA(ls_item)
    WITH KEY vbeln = ls_head-vbeln BINARY SEARCH.
  IF sy-subrc = 0.
    LOOP AT lt_item FROM sy-tabix INTO ls_item
      WHERE vbeln = ls_head-vbeln.
      "处理逻辑
    ENDLOOP.
  ENDIF.
ENDLOOP.

"✅ 正确 — 方案2：用 HASHED TABLE 或内表分组
LOOP AT lt_item INTO DATA(ls_item)
  GROUP BY ls_item-vbeln INTO DATA(lv_group).
  READ TABLE lt_head INTO DATA(ls_head)
    WITH KEY vbeln = lv_group BINARY SEARCH.
  "处理逻辑
ENDLOOP.
```

### 2. 禁止 LOOP 中写 SELECT

每次循环查数据库 = 数据库往返次数 × 内表行数，严重影响性能。

```abap
"❌ 错误 — LOOP 中 SELECT，每次循环都访问数据库
LOOP AT lt_data INTO DATA(ls_data).
  SELECT SINGLE maktx FROM makt
    INTO ls_data-maktx
    WHERE matnr = ls_data-matnr
      AND spras = sy-langu.
  MODIFY lt_data FROM ls_data.
ENDLOOP.

"✅ 正确 — 先一次性取出所有需要的数据到内表
IF lt_data IS NOT INITIAL.
  SELECT matnr, maktx
    FROM makt
    INTO TABLE @DATA(lt_makt)
    FOR ALL ENTRIES IN @lt_data
   WHERE matnr = @lt_data-matnr
     AND spras = @sy-langu
     .
ENDIF.

"再用 READ TABLE 或 LOOP ... GROUP BY 关联
SORT lt_makt BY matnr.
LOOP AT lt_data ASSIGNING FIELD-SYMBOL(<fs_data>).
  READ TABLE lt_makt INTO DATA(ls_makt)
    WITH KEY matnr = <fs_data>-matnr BINARY SEARCH.
  IF sy-subrc = 0.
    <fs_data>-maktx = ls_makt-maktx.
  ENDIF.
ENDLOOP.
```

### 3. READ TABLE 必须使用 BINARY SEARCH

标准 READ TABLE 是线性查找 O(n)，加 `BINARY SEARCH` 变二分查找 O(log n)。**前提：内表必须按查找 key 排序。**

```abap
"❌ 错误 — 不带 BINARY SEARCH，线性查找
READ TABLE lt_data INTO ls_data
  WITH KEY matnr = lv_matnr.

"❌ 错误 — 带了 BINARY SEARCH 但内表未排序，结果不可预测
READ TABLE lt_data INTO ls_data
  WITH KEY matnr = lv_matnr BINARY SEARCH.

"✅ 正确 — 先排序，再 BINARY SEARCH
SORT lt_data BY matnr.
READ TABLE lt_data INTO ls_data
  WITH KEY matnr = lv_matnr BINARY SEARCH.
IF sy-subrc = 0.
  "使用 ls_data
ENDIF.
```

**排序规则**：
- `SORT` 的字段必须与 `READ TABLE` 的 `WITH KEY` 字段完全一致
- 如果按多个字段查找，排序也必须按相同顺序：
  ```abap
  SORT lt_data BY vbeln posnr.
  READ TABLE lt_data INTO ls_data
    WITH KEY vbeln = lv_vbeln posnr = lv_posnr BINARY SEARCH.
  ```

### 4. FOR ALL ENTRIES 前必须判断内表非空

`FOR ALL ENTRIES IN` 的内表如果为空，WHERE 条件被忽略，会**全量查询数据库**。

```abap
"❌ 错误 — 不判断空，内表为空时全量查询
SELECT * FROM mara
  INTO TABLE lt_mara
  FOR ALL ENTRIES IN lt_keys
  WHERE matnr = lt_keys-matnr.

"✅ 正确 — 先检查非空
IF lt_keys IS NOT INITIAL.
  SELECT * FROM mara
    INTO TABLE lt_mara
    FOR ALL ENTRIES IN lt_keys
    WHERE matnr = lt_keys-matnr.
ELSE.
  "内表为空时，目标表也应为空，或跳过后续逻辑
  CLEAR lt_mara.
ENDIF.
```

**额外要求**：`FOR ALL ENTRIES` 之前必须对驱动表去重，避免重复查询：
```abap
SORT lt_keys BY matnr.
DELETE ADJACENT DUPLICATES FROM lt_keys COMPARING matnr.
```

### 5. 尽量减少 LOOP 次数 — 同一内表只循环一次

报表中多次对同一内表 LOOP 是常见浪费。**数据处理逻辑应合并到一次 LOOP 中完成**，而不是分多次循环。

```abap
"❌ 错误 — 同一内表循环三次
LOOP AT lt_main INTO ls_main.
  "第一次：计算金额
  ls_main-amount = ls_main-price * ls_main-quantity.
  MODIFY lt_main FROM ls_main.
ENDLOOP.

LOOP AT lt_main INTO ls_main.
  "第二次：设置状态
  IF ls_main-amount > 1000.
    ls_main-status = 'H'.
  ENDIF.
  MODIFY lt_main FROM ls_main.
ENDLOOP.

LOOP AT lt_main INTO ls_main.
  "第三次：输出ALV
  ...
ENDLOOP.

"✅ 正确 — 合并为一次 LOOP
LOOP AT lt_main ASSIGNING FIELD-SYMBOL(<fs_main>).
  "数据处理：金额 + 状态 一次性完成
  <fs_main>-amount = <fs_main>-price * <fs_main>-quantity.
  IF <fs_main>-amount > 1000.
    <fs_main>-status = 'H'.
  ENDIF.
ENDLOOP.

"之后 ALV 输出用引用传递，无需再次 LOOP
```

**典型场景**：如 `ZAI_DEMO001`，`LOOP AT lt_main INTO ls_main` 被调用了多次 — 应该合并到最后一处统一处理。原则：**同一内表的数据处理，能一次循环完成的不分两次。**

### 6. SELECT 后必须 SORT 内表

SELECT 读取数据到内表后，**必须立即按后续查询条件或主键字段 SORT**，为后续 `READ TABLE ... BINARY SEARCH` 和 `LOOP ... WHERE` 做准备。

```abap
"❌ 错误 — SELECT 后不排序，后面 READ TABLE 加 BINARY SEARCH 结果不可预测
SELECT matnr, mtart, meins, maktx
  FROM mara
  INTO TABLE @DATA(lt_mara)
 WHERE mtart IN @s_mtart
   .
"...
READ TABLE lt_mara INTO DATA(ls_mara)
  WITH KEY matnr = lv_matnr BINARY SEARCH.  "未排序，结果不可预测！

"✅ 正确 — SELECT 后立即排序
SELECT matnr, mtart, meins, maktx
  FROM mara
  INTO TABLE @DATA(lt_mara)
 WHERE mtart IN @s_mtart
   .

SORT lt_mara BY matnr.  "按后续查询条件排序

"后续 READ TABLE BINARY SEARCH 安全
READ TABLE lt_mara INTO DATA(ls_mara)
  WITH KEY matnr = lv_matnr BINARY SEARCH.
```

**排序字段选择原则**：
1. 如果后续要用 `READ TABLE ... BINARY SEARCH`，按 READ 的 key 字段排序
2. 如果没有后续查询，按主键排序（保证数据一致性）
3. 多字段排序顺序与后续查询条件一致

```abap
"示例：后续按 vbeln + posnr 查询，则按这两个字段排序
SELECT vbeln, posnr, matnr, menge
  FROM vbap
  INTO TABLE @DATA(lt_vbap)
  FOR ALL ENTRIES IN @lt_head
 WHERE vbeln = @lt_head-vbeln
   .
SORT lt_vbap BY vbeln posnr.  "按后续查询条件排序
```

---

## 注释

### 注释规范

- 注释行用 `"` 开头，一个空格后写内容
- 行内注释用 `"` 开头，前置一个空格
- 注释解释"为什么"，不是"做了什么"（代码本身就说明做了什么）

```abap
"❌ 错误 — 复述代码
lv_count = lv_count + 1. "计数器加1

"✅ 正确 — 解释原因
lv_count = lv_count + 1. "排除header行，从第2条开始统计
```

### 注释掉的代码

**规则**：已废弃的代码直接删除，不保留注释掉的死代码。变更记录已登记在程序头注释中，无需保留旧代码。

```abap
"❌ 错误 — 保留注释掉的旧代码
"lv_count = lv_count + 1.
"PERFORM frm_old_logic.
"    USING lv_data.

"✅ 正确 — 直接删除，变更记录在头注释中
"（代码已删除，变更记录已登记）
```

**例外**：如果注释掉的代码用于说明"为什么不能这样写"，则保留并加说明：

```abap
"注意：此处不能使用 FOR ALL ENTRIES，因为 MARD 表可能没有索引
"以下写法会导致全表扫描：
"SELECT * FROM mard FOR ALL ENTRIES IN @lt_mara WHERE matnr = @lt_mara-matnr.
```

### 注释语言

- **代码注释**：使用中文，便于团队维护
- **数据字典对象描述**：使用中文
- **变量名、函数名**：使用英文
- **消息文本**：使用中文

### 禁止事项

| 禁止 | 说明 |
|------|------|
| 注释掉的代码块 | 直接删除，变更记录在头注释中 |
| 无意义的注释 | 不写 `" 变量声明` 这类废话 |
| 纯英文注释 | 中文团队统一使用中文注释 |
| 注释与代码不一致 | 修改代码时同步更新注释 |
| 乱码注释 | 编码统一 UTF-8，避免 GBK/BIG5 混用 |

---

## 错误处理

### 检查 sy-subrc

```abap
"❌ 错误 — 不检查返回值
SELECT SINGLE * FROM mara INTO @ls_mara WHERE matnr = @lv_matnr.
WRITE ls_mara-maktx. " 可能为空

"✅ 正确 — 检查后使用
SELECT SINGLE * FROM mara INTO @ls_mara WHERE matnr = @lv_matnr.
IF sy-subrc = 0.
  WRITE ls_mara-maktx.
ELSE.
  MESSAGE s000(00) WITH '物料不存在' DISPLAY LIKE 'E'.
  LEAVE LIST-PROCESSING.
ENDIF.
```

### 输入校验 — DISPLAY LIKE 'E' + LEAVE LIST-PROCESSING

**所有报表程序统一使用 `MESSAGE ... DISPLAY LIKE 'E'` + `LEAVE LIST-PROCESSING` 进行输入校验，禁止直接使用 `MESSAGE 'E'`。**

```abap
"❌ 错误 — 直接使用 MESSAGE 'E' 会导致 dump
MESSAGE '请输入物料号' TYPE 'E'.

"✅ 正确 — DISPLAY LIKE 'E' + LEAVE LIST-PROCESSING
MESSAGE s000(00) WITH '请输入物料号' DISPLAY LIKE 'E'.
LEAVE LIST-PROCESSING.
```

**输入校验模板**：

```abap
AT SELECTION-SCREEN.
  " 必填参数校验
  IF s_matnr[] IS INITIAL.
    MESSAGE s000(00) WITH '请输入物料' DISPLAY LIKE 'E'.
    LEAVE LIST-PROCESSING.
  ENDIF.

  IF p_werks IS INITIAL.
    MESSAGE s000(00) WITH '请输入工厂' DISPLAY LIKE 'E'.
    LEAVE LIST-PROCESSING.
  ENDIF.

  " 日期范围校验
  IF p_datumf > p_datumt.
    MESSAGE s000(00) WITH '开始日期不能大于结束日期' DISPLAY LIKE 'E'.
    LEAVE LIST-PROCESSING.
  ENDIF.
```

**为什么使用 `DISPLAY LIKE 'E'`**：
- `MESSAGE 'E'` 直接抛出异常，在 AT SELECTION-SCREEN 中可能产生 dump
- `DISPLAY LIKE 'E'` 显示 E 类型消息的样式，但程序可以继续执行
- `LEAVE LIST-PROCESSING` 退出当前 LIST，回到选择屏幕

### TRY/CATCH

```abap
"❌ 错误 — 不处理异常
lv_result = lo_obj->calculate( lv_value ).

"✅ 正确 — 捕获异常
TRY.
    lv_result = lo_obj->calculate( lv_value ).
  CATCH cx_sy_arithmetic_error INTO DATA(lx_error).
    MESSAGE lx_error->get_text( ) TYPE 'E'.
ENDTRY.
```

---

## ALV 规范

### 选型指南

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 报表（`ZMMR*`, `ZFIR*`, `ZPPR*`, `ZSDR*`） | `REUSE_ALV_GRID_DISPLAY_LVC` | 需要自定义 GUI 状态、双击跳转、变式保存、`box_fname` 等 |
| 批导（`ZMMB*`, `ZFIB*`, `ZPPB*`, `ZSDB*`） | `REUSE_ALV_GRID_DISPLAY_LVC` | 需要 `box_fname`（复选框列）和自定义工具栏按钮 |
| 简单列表展示 | `CL_SALV_TABLE` | 轻量级，无需额外回调 |

> **实际统计**: 所有已分析的报表程序（ZMMR001, ZMMR004, ZFIR001, ZFIR002, ZPPR001, ZSDR001）均使用 `REUSE_ALV_GRID_DISPLAY_LVC`。这是当前项目的事实标准。

### 标准配置

```abap
"布局
CLEAR gs_layout.
gs_layout-zebra      = 'X'.
gs_layout-cwidth_opt = 'X'.
gs_layout-sel_mode   = 'A'.

"字段目录手动构建（不使用 REUSE_ALV_FIELDCAT_MERGE）
APPEND VALUE #( fieldname = 'MATNR' scrtext_l = '物料号'
                ref_table = 'MARA' ref_field = 'MATNR' )
  TO gt_fieldcat.

"ALV 显示
CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY_LVC'
  EXPORTING
    i_callback_program       = sy-repid
    i_callback_pf_status_set = 'FRM_STATUS_SET'
    i_callback_user_command  = 'FRM_USER_COMMAND'
    is_layout_lvc            = gs_layout
    it_fieldcat_lvc          = gt_fieldcat
    i_save                   = 'A'
  TABLES
    t_outtab                 = gt_output
  EXCEPTIONS
    program_error            = 1
    OTHERS                   = 2.
```

### 回调与刷新

```abap
"GUI 状态
FORM frm_status_set USING pt_extab TYPE slis_t_extab.
  SET PF-STATUS 'STANDARD' EXCLUDING pt_extab.
ENDFORM.

"用户命令（双击跳转、按钮等）
FORM frm_user_command USING pv_ucomm    TYPE syucomm
                            ps_selfield TYPE slis_selfield.
  DATA: lv_grid TYPE REF TO cl_gui_alv_grid.

  CALL FUNCTION 'GET_GLOBALS_FROM_SLVC_FULLSCR'
    IMPORTING e_grid = lv_grid.
  CALL METHOD lv_grid->check_changed_data.
  ps_selfield-refresh = 'X'.

  CASE pv_ucomm.
    WHEN '&IC1'.  "双击
      READ TABLE gt_output INTO gs_output INDEX ps_selfield-tabindex.
      IF sy-subrc = 0.
        SET PARAMETER ID 'MAT' FIELD gs_output-matnr.
        CALL TRANSACTION 'MM03' AND SKIP FIRST SCREEN.
      ENDIF.
  ENDCASE.

  CALL METHOD lv_grid->refresh_table_display
    EXPORTING is_stable = VALUE lvc_s_stbl( row = 'X' col = 'X' ).
ENDFORM.
```

### 禁止事项

| 禁止 | 原因 |
|------|------|
| 使用 `REUSE_ALV_FIELDCAT_MERGE` 自动生成字段目录 | 字段顺序不可控，列名不可自定义 |
| 在 ALV 回调中直接 `LEAVE PROGRAM` | 改用 `LEAVE TO SCREEN 0` 或 `EXIT` |
| 字段目录 fieldname 与内表字段名不一致 | ALV 显示空白列 |

---

## 现代 ABAP 语法

### 推荐使用的语法

| 旧语法 | 新语法 |
|--------|--------|
| `MOVE a TO b` | `b = a` |
| `APPEND wa TO itab` | `APPEND VALUE #( ... ) TO itab` |
| `READ TABLE itab INDEX 1 INTO wa` | `wa = itab[ 1 ]` |
| `CREATE OBJECT lo` | `NEW #( ... )` |
| `CONCATENATE a b INTO c` | `c = a && b` |
| `DATA lv_x TYPE c LENGTH 1` | `DATA(lv_x) = abap_true` |

### 内联声明

```abap
"❌ 错误 — 冗余的变量声明
DATA lv_count TYPE i.
lv_count = lines( lt_data ).

"✅ 正确 — 内联声明
DATA(lv_count) = lines( lt_data ).
```

### 构造表达式

```abap
"❌ 错误 — 逐行填充
DATA lt_data TYPE TABLE OF t_data.
DATA ls_data TYPE t_data.
ls_data-field1 = 'A'.
ls_data-field2 = 'B'.
APPEND ls_data TO lt_data.

"✅ 正确 — 使用 VALUE
DATA(lt_data) = VALUE t_data_table(
  ( field1 = 'A' field2 = 'B' )
  ( field1 = 'C' field2 = 'D' )
).
```

### CASE ABAP_TRUE 条件分支

多个布尔标志选一时，使用 `CASE ABAP_TRUE` 简洁表达，消除多层 `IF ... ELSEIF`：

```abap
"❌ 错误 — 多层 IF/ELSEIF 嵌套
IF ls_flag-cancel = abap_true.
  lv_action = 'C'.
ELSEIF ls_flag-delete = abap_true.
  lv_action = 'D'.
ELSEIF ls_flag-reverse = abap_true.
  lv_action = 'O'.
ENDIF.

"✅ 正确 — CASE ABAP_TRUE 扁平化
CASE ABAP_TRUE.
  WHEN ls_flag-cancel.  lv_action = 'C'.  "取消
  WHEN ls_flag-delete.  lv_action = 'D'.  "删除
  WHEN ls_flag-reverse. lv_action = 'O'.  "冲销
ENDCASE.
```

### 报表程序中的兼容性说明

**虽然推荐使用现代 ABAP 语法，但报表程序（`ZMMR*`, `ZFIR*`, `ZPPR*`, `ZSDR*`）中以下遗留模式仍被广泛使用，属于事实标准：**

| 遗留模式 | 原因 | 替代方案 |
|----------|------|----------|
| `TABLES: mara.` | 选择屏幕 `SELECT-OPTIONS` 参照 DDIC 字段 | 无替代，必须保留 |
| `TYPE-POOLS: slis.` | ALV 回调类型 `slis_t_extab`、`slis_selfield` | 使用 `if_alv_rm_grid_friend` 接口可替代 |
| `FORM` 子程序 | 兼容 ALV 回调签名 + 团队习惯 | 新模块可迁移到 `METHOD` |
| `MOVE-CORRESPONDING` | 结构映射（非 `CORRESPONDING #()`） | 可迁移到 `CORRESPONDING #()` |

**新开发的模块（如接口、工具类）不受此限制，应严格使用现代 ABAP 语法。**

---

## DEFINE 宏

### 使用场景

DEFINE 宏用于封装重复代码块，最常见的是 ALV 字段目录（fieldcat）填充。

```abap
"❌ 错误 — 逐行填充，重复代码多
CLEAR w_fieldcat.
w_fieldcat-fieldname = 'MATNR'.
w_fieldcat-seltext_l = '物料号'.
w_fieldcat-seltext_m = '物料号'.
w_fieldcat-seltext_s = '物料号'.
APPEND w_fieldcat TO t_fieldcat.

CLEAR w_fieldcat.
w_fieldcat-fieldname = 'MAKTX'.
w_fieldcat-seltext_l = '物料描述'.
w_fieldcat-seltext_m = '物料描述'.
w_fieldcat-seltext_s = '物料描述'.
APPEND w_fieldcat TO t_fieldcat.

"✅ 正确 — 用 DEFINE 宏封装
DEFINE set_fieldcat.
  CLEAR w_fieldcat.
  w_fieldcat-fieldname       = &1.
  w_fieldcat-seltext_l       = &2.
  w_fieldcat-seltext_m       = &2.
  w_fieldcat-seltext_s       = &2.
  w_fieldcat-checkbox        = &3.
  w_fieldcat-edit            = &4.
  w_fieldcat-ref_tabname     = &5.
  w_fieldcat-ref_fieldname   = &6.
  APPEND w_fieldcat TO t_fieldcat.
END-OF-DEFINITION.

"调用宏
set_fieldcat 'MATNR'  '物料号'   '' '' 'MARA' 'MATNR'.
set_fieldcat 'MAKTX'  '物料描述' '' '' 'MAKT' 'MAKTX'.
set_fieldcat 'MENGE'  '数量'     '' '' ''     ''.
```

### 宏命名规范

- 宏名用小写 + 下划线：`set_fieldcat`, `add_message`, `check_error`
- 用 `&1`, `&2`, `&3`... 引用参数，最多 9 个
- 宏定义紧邻使用它的 FORM 或 CLASS 之前
- 用 `END-OF-DEFINITION` 结束（不是 `END-OF-DEFINE`）

---

## 动态编程

### FIELD-SYMBOLS（字段符号）

```abap
"LOOP 中使用字段符号避免拷贝
LOOP AT gt_data ASSIGNING FIELD-SYMBOL(<fs_data>).
  <fs_data>-status = 'X'.  "直接修改内表数据
ENDLOOP.

"动态结构访问
ASSIGN COMPONENT 'MATNR' OF STRUCTURE <fs_data> TO FIELD-SYMBOL(<fs_field>).
IF sy-subrc = 0.
  <fs_field> = 'NEW_VALUE'.
ENDIF.
```

### CREATE DATA（动态类型创建）

```abap
"根据配置表动态创建数据对象
DATA: lv_req  TYPE REF TO data,
      lv_resp TYPE REF TO data.
FIELD-SYMBOLS: <fs_req>  TYPE any,
               <fs_resp> TYPE any.

"动态创建请求结构
CREATE DATA lv_req TYPE (gs_config-zipara).
ASSIGN lv_req->* TO <fs_req>.

"动态创建响应结构
CREATE DATA lv_resp TYPE (gs_config-zopara).
ASSIGN lv_resp->* TO <fs_resp>.
```

### 动态函数调用

```abap
"根据配置表动态调用函数模块
CALL FUNCTION gs_config-zfname
  EXPORTING
    i_req  = <fs_req>
  IMPORTING
    o_resp = <fs_resp>.
```

### 动态编程注意事项

| 规则 | 原因 |
|------|------|
| 使用前检查 `sy-subrc` | `ASSIGN COMPONENT` 可能找不到字段 |
| 动态名称要在日志中记录 | 运行时才知道调用的是什么 |
| 避免深层嵌套动态结构 | 调试困难，性能差 |
| 动态类型引用优先用 `TYPE REF TO data` | 可以适配任意结构 |

---

## 字符串处理

### 长文本按固定长度分割

文本字段（如 BAPI 文本行、ALV 单元格）有长度限制，需按固定长度（通常 132 字符）分割长文本：

```abap
DATA: lv_txt    TYPE string,
      lv_length TYPE n LENGTH 4,
      lv_num    TYPE n LENGTH 4,
      lv_count  TYPE n LENGTH 4,
      lv_start  TYPE n LENGTH 4.

lv_length = strlen( lv_source ).
lv_num    = lv_length DIV 132.
lv_num    = lv_num + 1.                "整除时也至少一段

DO lv_num TIMES.
  lv_count = lv_count + 1.
  lv_start = ( lv_count - 1 ) * 132.
  IF lv_length = 0.
    EXIT.                              "空字符串直接退出
  ENDIF.
  IF lv_num = lv_count.
    lv_txt = lv_source+lv_start(lv_length).  "最后一段取剩余长度
  ELSE.
    lv_length = lv_length - 132.
    lv_txt = lv_source+lv_start(132).        "中间段固定 132
  ENDIF.

  "将 lv_txt 填充到目标文本行
  APPEND lv_txt TO lt_lines.
ENDDO.
```

**要点**：
- 用 `DIV` 计算段数，`+1` 保证整除时也至少分一段
- 最后一段取剩余长度，中间段固定 132
- 源字符串为空时 `EXIT`，避免死循环

---

## 金额符号处理

### 借贷方向金额符号调整

根据借贷标识（`SHKZG`）自动调整金额符号，并校验金额方向与业务类型一致性：

```abap
"1. 根据借贷标识调整金额符号
LOOP AT lt_item INTO DATA(ls_item).
  READ TABLE lt_doc INTO DATA(ls_doc)
    WITH KEY docno = ls_item-refdoc
             item  = ls_item-refitem BINARY SEARCH.
  IF sy-subrc = 0.
    IF ls_doc-shkzg = 'H'.            "贷方：金额取反
      ls_item-wrbtr = ls_item-wrbtr * -1.
    ENDIF.
    lv_total = lv_total + ls_item-wrbtr.
  ENDIF.
ENDLOOP.

"2. 校验金额方向与业务类型一致性
CASE lv_doc_type.
  WHEN '1'.                            "发票：金额应为正
    IF lv_total <= 0.
      MESSAGE '传入类型为发票，但累计金额不为正数' TYPE 'E'.
    ENDIF.
  WHEN '2'.                            "贷项：金额应为负
    IF lv_total >= 0.
      MESSAGE '传入类型为贷项，但累计金额不为负数' TYPE 'E'.
    ENDIF.
ENDCASE.
```

**要点**：
- 贷方（`SHKZG = 'H'`）金额取反，借方（`S`）保持原值
- 累计金额后按业务类型校验方向，提前拦截错误数据

---

## 单位转换

### 通用单位转换 FORM

使用 `ASSIGN COMPONENT` 动态获取字段，调用 `CONVERSION_EXIT_CUNIT_INPUT` 进行单位校验和转换。

```abap
FORM conversion_cunit_data USING p_fieldname
                        CHANGING p_data.

  FIELD-SYMBOLS <fs_value>.

  "动态单位转换
  ASSIGN COMPONENT p_fieldname OF STRUCTURE p_data TO <fs_value>.
  IF sy-subrc = 0.
    CALL FUNCTION 'CONVERSION_EXIT_CUNIT_INPUT'
      EXPORTING
        input          = <fs_value>
      IMPORTING
        output         = <fs_value>
      EXCEPTIONS
        unit_not_found = 1
        OTHERS         = 2.
  ENDIF.

ENDFORM.

"调用示例
PERFORM conversion_cunit_data USING 'MEINS' CHANGING ls_mara.
PERFORM conversion_cunit_data USING 'GEWEI' CHANGING ls_mara.
PERFORM conversion_cunit_data USING 'BSTME' CHANGING ls_mara.
```

### 常见转换函数

| 函数 | 用途 | 示例 |
|------|------|------|
| `CONVERSION_EXIT_CUNIT_INPUT` | 单位格式转换（外部→内部） | `CONVERSION_EXIT_CUNIT_INPUT` |
| `CONVERSION_EXIT_CUNIT_OUTPUT` | 单位格式转换（内部→外部） | `CONVERSION_EXIT_CUNIT_OUTPUT` |
| `CONVERSION_EXIT_MATN1_INPUT` | 物料号加前导零（外部→内部） | `CONVERSION_EXIT_MATN1_INPUT` |
| `CONVERSION_EXIT_MATN1_OUTPUT` | 物料号去前导零（内部→外部） | `CONVERSION_EXIT_MATN1_OUTPUT` |
| `CONVERSION_EXIT_ALPHA_INPUT` | ALPHA 转换（加前导零） | `CONVERSION_EXIT_ALPHA_INPUT` |
| `CONVERSION_EXIT_ALPHA_OUTPUT` | ALPHA 转换（去前导零） | `CONVERSION_EXIT_ALPHA_OUTPUT` |

---

## 编号范围处理

### 典型流程

编号范围处理分两种场景：**内部给号**（系统自动分配）和**外部给号**（调用方传入）。

```abap
"1. 物料号加前导零
CALL FUNCTION 'CONVERSION_EXIT_MATN1_INPUT'
  EXPORTING
    input  = ls_head-matnr
  IMPORTING
    output = lv_matnr.

"2. 判断新增/修改
SELECT SINGLE COUNT(*) FROM mara WHERE matnr = lv_matnr.
IF sy-subrc = 0.
  lv_flag = 'U'.  "修改
ELSE.
  lv_flag = 'I'.  "新增
ENDIF.

"3. 新增时获取编号范围
IF lv_flag = 'I'.
  SELECT SINGLE numki numke FROM t134
    INTO (lv_n1, lv_n2)
    WHERE mtart = ls_mara-mtart.

  IF sy-subrc = 0.
    IF lv_matnr IS INITIAL.  "内部给号
      "检查 NRIV 编号范围配置
      SELECT COUNT(*) FROM nriv
        WHERE ( nrrangenr = lv_n1 OR nrrangenr = lv_n2 )
          AND externind = '' AND object = 'MATERIALNR'.
      IF sy-subrc <> 0.
        "编号范围未配置
        MESSAGE e319(m3) WITH ls_mara-mtart INTO cv_resp-msgtx.
        EXIT.
      ENDIF.

      "锁定编号范围 → 获取下一个号 → 解锁
      CALL FUNCTION 'NUMBER_RANGE_ENQUEUE'
        EXPORTING
          object           = 'MATERIALNR'
        EXCEPTIONS
          OTHERS           = 1.

      CALL FUNCTION 'NUMBER_GET_NEXT'
        EXPORTING
          nr_range_nr             = lv_nr
          object                  = 'MATERIALNR'
        IMPORTING
          number                  = lv_matnr
        EXCEPTIONS
          OTHERS                  = 1.

      CALL FUNCTION 'NUMBER_RANGE_DEQUEUE'
        EXPORTING
          object           = 'MATERIALNR'
        EXCEPTIONS
          OTHERS           = 1.

    ELSE.  "外部给号 → 号码校验
      CALL FUNCTION 'NUMBER_CHECK'
        EXPORTING
          nr_range_nr             = ls_t134-numke
          number                  = lv_matnr
          object                  = 'MATERIALNR'
        IMPORTING
          returncode              = lv_returncode
        EXCEPTIONS
          OTHERS                  = 1.

      IF lv_returncode IS NOT INITIAL.
        "号码不在范围内
        MESSAGE e318(m3) WITH lv_matnr ls_mara-mtart INTO cv_resp-msgtx.
        EXIT.
      ENDIF.
    ENDIF.
  ENDIF.
ENDIF.
```

### 编号范围三步骤（内部给号）

```
NUMBER_RANGE_ENQUEUE  →  NUMBER_GET_NEXT  →  NUMBER_RANGE_DEQUEUE
     (锁定)                   (获取号)              (解锁)
```

### 编号相关函数

| 函数 | 用途 |
|------|------|
| `NUMBER_RANGE_ENQUEUE` | 锁定编号范围对象 |
| `NUMBER_GET_NEXT` | 获取下一个编号（内部给号） |
| `NUMBER_RANGE_DEQUEUE` | 解锁编号范围对象 |
| `NUMBER_CHECK` | 检查编号是否在范围内（外部给号） |

---

## 分类视图处理

### BAPI 分类操作模式

分类视图处理分三步：获取分类对象键值 → 获取已有分类值 → 新建或修改分类。

```abap
"判断分类视图是否存在
CALL FUNCTION 'VB_BATCH_2_CLASS_OBJECT'
  EXPORTING
    i_matnr = lv_matnr
    i_charg = lv_klart
  IMPORTING
    e_objek = lv_objek
    e_obtab = lv_obtab
    e_klart = lv_klart
    e_class = lv_class.

"获取已有分类值
CALL FUNCTION 'BAPI_OBJCL_GETDETAIL'
  EXPORTING
    objecttable     = lv_obtab
    classnum        = lv_class
    classtype       = lv_klart
    objectkey_long  = lv_objek
    language        = sy-langu
  TABLES
    allocvaluesnum  = lt_allocvaluesnum
    allocvalueschar = lt_allocvalueschar
    allocvaluescurr = lt_allocvaluescurr
    return          = lt_return.

"判断分类视图是否存在
IF lt_allocvalueschar IS INITIAL.
  lv_flag = 'I'.  "新建分类
ELSE.
  lv_flag = 'U'.  "修改分类
ENDIF.

"新建分类
IF lv_flag = 'I'.
  CALL FUNCTION 'BAPI_OBJCL_CREATE'
    EXPORTING
      objectkeynew_long = lv_objectkey_long
      objecttablenew    = lv_objecttable
      classnumnew       = lv_classnum
      classtypenew      = lv_classtype
      standardclass     = 'X'
    TABLES
      allocvaluesnum    = lt_allocvaluesnum
      allocvalueschar   = lt_allocvalueschar
      allocvaluescurr   = lt_allocvaluescurr
      return            = lt_return.
ELSE.
  "修改分类
  CALL FUNCTION 'BAPI_OBJCL_CHANGE'
    EXPORTING
      objectkey          = lv_objectkey
      objecttable        = lv_objecttable
      classnum           = lv_classnum
      classtype          = lv_classtype
      standardclass      = 'X'
    TABLES
      allocvaluesnumnew  = lt_allocvaluesnum
      allocvaluescharnew = lt_allocvalueschar
      allocvaluescurrnew = lt_allocvaluescurr
      return             = lt_return.
ENDIF.

"分类操作后提交
IF sy-subrc = 0.
  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'
    EXPORTING
      wait = 'X'.
ENDIF.
```

### 分类相关函数

| 函数 | 用途 |
|------|------|
| `VB_BATCH_2_CLASS_OBJECT` | 获取分类对象键值 |
| `BAPI_OBJCL_GETDETAIL` | 获取已有分类值 |
| `BAPI_OBJCL_CREATE` | 创建分类 |
| `BAPI_OBJCL_CHANGE` | 修改分类 |

---

## JSON 处理

### 使用 /ui2/cl_json

```abap
"JSON → ABAP 结构（反序列化）
/ui2/cl_json=>deserialize(
  EXPORTING json        = lv_json_string
            pretty_name = /ui2/cl_json=>pretty_mode-camel_case
  CHANGING  data        = ls_data ).

"ABAP 结构 → JSON（序列化）
lv_json = /ui2/cl_json=>serialize(
  data        = ls_data
  pretty_name = /ui2/cl_json=>pretty_mode-camel_case ).
```

### JSON 格式判断

```abap
"根据第一个字符判断格式
CASE lv_value+0(1).
  WHEN '<'.     "XML 格式
    cl_demo_output=>write_xml( lv_value ).
  WHEN '{' OR '['.  "JSON 格式
    cl_demo_output=>write_json( lv_value ).
  WHEN OTHERS.      "纯文本
    cl_demo_output=>write_text( lv_value ).
ENDCASE.
```

---

## 相关规范文件

不同开发类型的专项规范：

| 类型 | 规范文件 |
|------|----------|
| 类与接口 | [abap-class.md](abap-class.md) |
| 函数模块 | [abap-interface.md](abap-interface.md) |
| 批导入 | [abap-batchinput.md](abap-batchinput.md) |