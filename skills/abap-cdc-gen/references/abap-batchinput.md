---
name: abap-batchinput
description: ABAP 批导入程序开发规范 — Excel上传 + 动态内表 + 接口函数模块模式
---

# ABAP 批导入程序规范

> **适用范围**: `ZMMB*`, `ZFIB*`, `ZPPB*`, `ZSDB*` 系列批导入程序。
> **通用编码规范**（命名、SELECT、注释等）见 [abap-coding.md](abap-coding.md)。
> **接口规范**（函数模块 I_REQ/O_RESP 结构）见 [abap-interface.md](abap-interface.md)。

## 目录

- [核心架构](#核心架构)
- [命名规范](#命名规范)
- [程序结构](#程序结构)
- [选择屏幕](#选择屏幕)
- [模板下载](#模板下载)
- [数据上传](#数据上传)
- [数据转换](#数据转换)
- [ALV 展示](#alv-展示)
- [数据导入](#数据导入)
- [进度条](#进度条)
- [结果回写](#结果回写)
- [完整程序模板](#完整程序模板)
- [禁止事项](#禁止事项)

---

## 核心架构

```
Excel 模板下载 ← SMW0 (WWWDATA)
       ↓
Excel 文件上传 → ZFM_GET_FIELDCAT 读取表头
       ↓
cl_alv_table_create=>create_dynamic_table 创建动态内表
       ↓
ZFM_GET_UPLOAD_DATA 读取数据入动态内表
       ↓
数据转换（单位转换、前导零等）
       ↓
REUSE_ALV_GRID_DISPLAY_LVC 展示数据
       ↓
用户勾选行 → 点击导入按钮
       ↓
按 NUMBER 分组 → 组装接口 REQ 结构
       ↓
CALL FUNCTION 接口函数模块 → O_RESP 返回结果
       ↓
结果回写 ALV (ID 状态图标 + MSG 消息)
```

**关键原则**: 批导程序本身不做业务逻辑，只负责数据上传、转换、分组、调用后端接口函数模块。所有业务逻辑（BAPI 调用、数据校验、数据库写入）都在接口函数模块中处理。

### 接口函数前置依赖

批导程序通过 `CALL FUNCTION` 调用接口函数模块（如 `ZFM_MMI001`）完成数据导入。因此**接口函数必须先于批导程序开发**：

```
开发顺序：
  1. 接口函数模块（含 DDIC 结构）   ← 必须先完成
  2. 批导程序                       ← 依赖接口函数存在
```

**如果接口函数不存在**（`SearchObject` 查不到）：
- 询问用户是否需要先开发接口函数模块（按 [abap-interface.md](abap-interface.md#ddic-先行开发流程) 的 DDIC 先行流程）
- 或直接调用 SAP 标准 BAPI（如 `BAPI_PO_CREATE1`、`BAPI_MATERIAL_SAVEDATA`），在批导程序中直接写 BAPI 调用逻辑（此时批导程序负责业务逻辑，但需用户确认）

> 接口函数注册到 ZTREST_CONF 后，不仅批导程序可调用，REST API 也可通过统一入口调用，实现"一套接口，多种入口"。

---

## 命名规范

### 程序名

| 模式 | 说明 | 示例 |
|------|------|------|
| `ZMMBnnn` | MM 模块批导 | `ZMMB001` 物料主数据 |
| `ZFIBnnn` | FI 模块批导 | `ZFIB001` 会计凭证 |
| `ZPPBnnn` | PP 模块批导 | `ZPPB001` BOM 维护 |
| `ZSDBnnn` | SD 模块批导 | `ZSDB001` 销售订单 |

### 事务码

| 前缀 | 说明 | 示例 |
|------|------|------|
| 与程序同名 | 事务码 = 程序名 | `ZMMB001` → TCODE `ZMMB001` |

### 接口函数模块

| 模式 | 说明 | 示例 |
|------|------|------|
| `ZFM_{Module}I{nnn}` | 模块接口函数 | `ZFM_MMI001` (MM), `ZFM_FII001` (FI), `ZFM_PPI001` (PP), `ZFM_SDI001` (SD) |

### 接口命名对应关系

| 批导程序 | 接口函数 | 请求结构 | 响应结构 |
|----------|----------|----------|----------|
| `ZMMB001` | `ZFM_MMI001` | `ZSMMI001_REQ` | `ZSREST_OUT` |
| `ZFIB001` | `ZFM_FII001` | `ZSFII001_REQ` | `ZSREST_OUT` |
| `ZPPB001` | `ZFM_PPI001` | `ZSPPI001_REQ` | `ZSREST_OUT` |
| `ZSDB001` | `ZFM_SDI001` | `ZSSDI001_REQ` | `ZSREST_OUT` |

---

## 程序结构

### 代码注释头

程序头注释遵循 [abap-coding.md](abap-coding.md#程序头注释模板) 统一模板，格式如下：

```abap
*&---------------------------------------------------------------------*
*& Report ZMMB001
*&---------------------------------------------------------------------*
*& Program Name                   ：ZMMB001
*& Program Description            : 物料主数据批导
*& Company                        : 上海汉得-SAP项目
*& ABAPER                         ：HANDAI
*& Finish Date                    ：20221025
*&---------------------------------------------------------------------*
*& Remark：物料主数据批量导入
*&   1). Excel 模板上传;
*&   2). 数据转换校验;
*&   3). 调用 ZFM_MMI001 接口;
*&---------------------------------------------------------------------*
*& Change Record：
*& Date         Developer           ReqNo       Descriptions
*& ==========  ==================  ==========  ========================
*& 20221025     HANDAI              SD1K900125   Create
*&---------------------------------------------------------------------*
```

> **注意**: 分隔线统一使用单横杠 `-`，禁止双等号 `=`。变更记录中的表格分隔线除外。

### 变量声明顺序

```abap
REPORT zmmb001.

"1. 全局类型定义（缓存类型）
TYPES: BEGIN OF ty_temp,
         number TYPE zenumber,    "排序号
         id     TYPE icon_d,      "成功/失败图标
         msg    TYPE bapi_msg,    "消息
       END OF ty_temp.

"2. 全局变量定义
DATA: gt_data TYPE REF TO data.        "动态内表引用
DATA: gt_temp TYPE TABLE OF ty_temp,   "缓存表
      gs_temp TYPE ty_temp.

"3. 进度条
DATA: gv_per  TYPE p,
      gv_stxt TYPE string,
      gv_num  TYPE i VALUE 0,
      gv_sign TYPE i VALUE 0.

"4. ALV 定义
DATA: gt_fieldcat TYPE lvc_t_fcat,
      gs_fieldcat TYPE lvc_s_fcat,
      gs_layout   TYPE lvc_s_layo.

"5. FIELD-SYMBOLS
FIELD-SYMBOLS: <ft_data>  TYPE STANDARD TABLE,  "动态内表
               <fs_temp>  TYPE ty_temp,         "缓存行
               <fs_data>,                       "数据行
               <fs_value>.                      "字段值
```

---

## 选择屏幕

### 标准布局

```abap
SELECTION-SCREEN BEGIN OF BLOCK blk WITH FRAME TITLE TEXT-001.

  PARAMETERS: rb_down TYPE char1 RADIOBUTTON GROUP grp1 USER-COMMAND cre,
              rb_upld TYPE char1 RADIOBUTTON GROUP grp1 DEFAULT 'X'.
  PARAMETERS: p_path  TYPE rlgrap-filename MODIF ID m2.

SELECTION-SCREEN END OF BLOCK blk.
```

### 选择屏幕控制

```abap
AT SELECTION-SCREEN OUTPUT.
  LOOP AT SCREEN.
    IF screen-group1 = 'M2'.
      IF rb_upld = 'X'.
        screen-active = 1.
      ELSE.
        screen-active = 0.
      ENDIF.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP.
```

### 文件选择 F4 Help

```abap
AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_path.
  CALL FUNCTION 'KD_GET_FILENAME_ON_F4'
    CHANGING
      file_name = p_path.
```

### 主流程

```abap
START-OF-SELECTION.
  IF rb_down = 'X'.
    PERFORM frm_download_file.       "下载模板
  ELSEIF rb_upld = 'X'.
    PERFORM frm_get_data.            "上传数据
    PERFORM frm_process_data.        "数据转换
    PERFORM frm_display_alv.         "ALV展示
  ENDIF.
```

---

## 模板下载

模板文件存储在 SMW0 (`WWWDATA` 表)，`objid = sy-repid`（程序名与模板名一致）。

```abap
FORM frm_download_file.
  DATA: lv_file              TYPE rlgrap-filename,
        lv_objid             TYPE wwwdata-objid,
        ls_key               TYPE wwwdatatab,
        lv_subrc             TYPE sy-subrc,
        lv_filename          TYPE string,
        lv_path              TYPE string,
        lv_fullpath          TYPE string,
        lv_default_file_name TYPE string.

  "默认文件名
  lv_default_file_name = TEXT-001 && '.xlsx'.

  "选择保存路径
  CALL METHOD cl_gui_frontend_services=>file_save_dialog
    EXPORTING
      window_title      = '请选择路径'
      default_file_name = lv_default_file_name
      file_filter       = 'Excel 文件 (*.xlsx)'
    CHANGING
      filename          = lv_filename
      path              = lv_path
      fullpath          = lv_fullpath
    EXCEPTIONS
      OTHERS            = 1.

  lv_file  = lv_fullpath.
  lv_objid = sy-repid.   "模板名与程序名一致

  IF lv_fullpath IS NOT INITIAL.
    SELECT SINGLE *
      FROM wwwdata
      INTO CORRESPONDING FIELDS OF ls_key
      WHERE objid = lv_objid
        AND relid = 'MI'.

    CALL FUNCTION 'DOWNLOAD_WEB_OBJECT'
      EXPORTING
        key         = ls_key
        destination = lv_file
      IMPORTING
        rc          = lv_subrc.

    IF lv_subrc = 0.
      MESSAGE '模板下载成功' TYPE 'S'.
    ENDIF.
  ELSE.
    MESSAGE '下载取消！' TYPE 'S' DISPLAY LIKE 'E'.
  ENDIF.
ENDFORM.
```

### 多模板变体

当需要下载多个不同模板时，通过 `SY-REPID` 加后缀区分：

```abap
"场景A模板
lv_objid = sy-repid && '_A'.
"场景B模板
lv_objid = sy-repid && '_B'.
```

---

## 数据上传

### 标准流程

```abap
FORM frm_get_data.
  DATA: lt_return TYPE bapiret2_t,
        ls_return TYPE bapiret2,
        lv_msg    TYPE char220.

  "1. 获取 Excel 表头字段
  REFRESH gt_fieldcat.
  CALL FUNCTION 'ZFM_GET_FIELDCAT'
    EXPORTING
      i_path      = p_path       "Excel 文件路径
      i_end_col   = 100          "最大列数
    TABLES
      et_fieldcat = gt_fieldcat  "字段目录
      et_return   = lt_return.

  "2. 检查错误
  IF lt_return IS NOT INITIAL.
    LOOP AT lt_return INTO ls_return WHERE type = 'E'.
      lv_msg = lv_msg && ls_return-message.
    ENDLOOP.
    IF lv_msg IS NOT INITIAL.
      MESSAGE lv_msg TYPE 'S' DISPLAY LIKE 'E'.
      STOP.
    ENDIF.
  ENDIF.

  "3. 创建动态内表
  CALL METHOD cl_alv_table_create=>create_dynamic_table
    EXPORTING
      it_fieldcatalog = gt_fieldcat
    IMPORTING
      ep_table        = gt_data.
  ASSIGN gt_data->* TO <ft_data>.

  "4. 获取 Excel 数据
  CALL FUNCTION 'ZFM_GET_UPLOAD_DATA'
    TABLES
      et_data = <ft_data>.

  "5. 删除 CHECK 列（ALV 选择框列，不需要显示）
  DELETE gt_fieldcat WHERE fieldname = 'CHECK'.

  "6. 排序
  DATA(lt_sort) = VALUE abap_sortorder_tab(
    ( name = 'NUMBER' )
  ).
  SORT <ft_data> BY (lt_sort).
ENDFORM.
```

### 关键函数

| 函数 | 作用 |
|------|------|
| `ZFM_GET_FIELDCAT` | 读取 Excel 第一行表头，生成 LVC 字段目录 |
| `cl_alv_table_create=>create_dynamic_table` | 根据字段目录创建动态内表 |
| `ZFM_GET_UPLOAD_DATA` | 读取 Excel 数据行到动态内表 |

### 动态内表固定列

Excel 模板的列由业务决定，但以下列是框架自动添加的：

| 列名 | 类型 | 说明 |
|------|------|------|
| `CHECK` | CHAR1 | 选择框，由 ALV 布局 `box_fname` 渲染 |
| `NUMBER` | ZENUMBER | 序号，用于分组多行数据（如抬头+行项目） |
| `ID` | ICON-ID | 导入结果状态图标（绿灯/红灯） |
| `MSG` | CHAR220 | 导入结果消息 |

---

## 数据转换

在 `frm_process_data` 中进行数据预处理。通用转换函数（`CONVERSION_EXIT_CUNIT_INPUT`、`CONVERSION_EXIT_MATN1_INPUT`、`CONVERSION_EXIT_ALPHA_INPUT` 等）见 [abap-coding.md 单位转换](abap-coding.md#单位转换)。

### ZFM_CONVERSION_EXIT 封装

批导程序通过 `ZFM_CONVERSION_EXIT` 封装函数对动态内表字段进行批量转换：

```abap
"单位转换
CALL FUNCTION 'ZFM_CONVERSION_EXIT'
  EXPORTING
    iv_fieldname = 'MEINS'
    iv_exit      = zgl0_cunit_in     "常量：CONVERSION_EXIT_CUNIT_INPUT
  CHANGING
    cs_data      = <fs_data>.

"ALPHA 转换（前导零）
CALL FUNCTION 'ZFM_CONVERSION_EXIT'
  EXPORTING
    iv_fieldname = 'GL_ACCOUNT'
    iv_exit      = zgl0_alpha_in
  CHANGING
    cs_data      = <fs_data>.
```

### 常用转换出口常量

| 常量 | 对应函数 |
|------|----------|
| `zgl0_cunit_in` | `CONVERSION_EXIT_CUNIT_INPUT` |
| `zgl0_alpha_in` | `CONVERSION_EXIT_ALPHA_INPUT` |
| `zgl0_matn1_in` | `CONVERSION_EXIT_MATN1_INPUT` |

---

## ALV 展示

> **注意**: 批导程序使用 `REUSE_ALV_GRID_DISPLAY_LVC` 而非 `CL_SALV_TABLE`。原因是批导需要 `box_fname`（复选框列）和自定义 GUI 状态（工具栏导入按钮），`CL_SALV_TABLE` 对这些场景支持不足。通用报表场景仍应使用 `CL_SALV_TABLE`（见 [abap-coding.md ALV 规范](abap-coding.md#alv-规范)）。

### 标准 ALV 配置

```abap
FORM frm_display_alv.
  "布局
  CLEAR gs_layout.
  gs_layout-box_fname = 'CHECK'.     "选择框列
  gs_layout-zebra     = 'X'.         "斑马线
  gs_layout-cwidth_opt = 'X'.        "自动列宽

  "ALV 显示
  CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY_LVC'
    EXPORTING
      i_callback_program       = sy-repid
      i_callback_pf_status_set = 'FRM_SET_PF_STATUS'
      i_callback_user_command  = 'FRM_USER_COMMAND'
      is_layout_lvc            = gs_layout
      it_fieldcat_lvc          = gt_fieldcat
      i_save                   = 'A'
    TABLES
      t_outtab                 = <ft_data>
    EXCEPTIONS
      program_error            = 1
      OTHERS                   = 2.
ENDFORM.
```

### GUI 状态

```abap
FORM frm_set_pf_status USING pt_extab TYPE slis_t_extab.
  SET PF-STATUS 'STANDARD'.
ENDFORM.
```

> **注意**: GUI 状态 `STANDARD` 需要在程序中通过 `SE41` 创建，包含导入按钮（功能码 `ZLOAD` 或 `ZIMPORT`）。

### 工具栏命令

```abap
FORM frm_user_command USING pv_ucomm    TYPE syucomm
                            ps_selfield TYPE slis_selfield.
  DATA: lv_grid TYPE REF TO cl_gui_alv_grid.

  "获取 ALV Grid 实例
  CALL FUNCTION 'GET_GLOBALS_FROM_SLVC_FULLSCR'
    IMPORTING
      e_grid = lv_grid.
  CALL METHOD lv_grid->check_changed_data.
  ps_selfield-refresh = 'X'.

  CASE pv_ucomm.
    WHEN 'ZLOAD' OR 'ZIMPORT'.   "导入按钮
      PERFORM frm_save_data.
  ENDCASE.

  "刷新 ALV
  CALL METHOD lv_grid->refresh_table_display.
ENDFORM.
```

> **功能码约定**: `ZLOAD` 和 `ZIMPORT` 两种命名均可，取决于各模块 GUI 状态定义。

---

## 数据导入

### 导入前检查 (frm_before_import)

```abap
FORM frm_before_import CHANGING p_flag.
  DATA: lv_number   TYPE zenumber,
        lv_checkbox TYPE char1,
        lv_id       TYPE icon-id.

  CLEAR: gt_temp.

  "1. 筛选选中的、未导入的行
  LOOP AT <ft_data> ASSIGNING <fs_data>.
    CLEAR: lv_checkbox, lv_id.
    PERFORM frm_convent_data_out USING <fs_data> 'CHECK' CHANGING lv_checkbox.
    PERFORM frm_convent_data_out USING <fs_data> 'ID'    CHANGING lv_id.

    IF lv_checkbox = 'X' AND lv_id <> icon_led_green.
      CLEAR: gs_temp.
      PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING gs_temp-number.
      APPEND gs_temp TO gt_temp.
    ENDIF.
  ENDLOOP.

  "2. 去重
  IF gt_temp IS NOT INITIAL.
    SORT gt_temp BY number.
    DELETE ADJACENT DUPLICATES FROM gt_temp COMPARING number.

    "设置进度条总数
    gv_num = lines( gt_temp ).

    "3. 选中所有相同 NUMBER 的行
    LOOP AT <ft_data> ASSIGNING <fs_data>.
      CLEAR: lv_number.
      PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING lv_number.
      READ TABLE gt_temp TRANSPORTING NO FIELDS
        WITH KEY number = lv_number BINARY SEARCH.
      IF sy-subrc = 0.
        PERFORM frm_convent_data_in USING 'CHECK' 'X' CHANGING <fs_data>.
      ENDIF.
    ENDLOOP.
  ELSE.
    p_flag = 'X'.
    MESSAGE s001(zgl01) DISPLAY LIKE 'E'.  "请选择至少一条数据
  ENDIF.
ENDFORM.
```

### 保存数据 - 单行模式 (Flat)

适用于每行独立的场景（如采购信息记录、信用主数据）：

```abap
FORM frm_save_data.
  DATA: lv_flag   TYPE char1,
        lv_number TYPE zenumber,
        lv_field  TYPE fieldname VALUE 'NUMBER'.
  DATA: ls_req  TYPE zsmmi005_req,
        ls_resp TYPE zsrest_out.

  PERFORM frm_before_import CHANGING lv_flag.
  CHECK lv_flag IS INITIAL.

  LOOP AT <ft_data> ASSIGNING <fs_data>.
    PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING lv_number.
    READ TABLE gt_temp ASSIGNING <fs_temp> WITH KEY number = lv_number BINARY SEARCH.
    IF sy-subrc <> 0.
      CONTINUE.
    ENDIF.

    AT NEW (lv_field).
      CLEAR: ls_req, ls_resp.
      MOVE-CORRESPONDING <fs_data> TO ls_req-req.
    ENDAT.

    AT END OF (lv_field).
      CALL FUNCTION 'ZFM_MMI005'
        EXPORTING
          i_req  = ls_req
        IMPORTING
          o_resp = ls_resp.

      "记录结果
      IF ls_resp-msgty = 'S'.
        <fs_temp>-id = icon_led_green.
      ELSE.
        <fs_temp>-id = icon_led_red.
      ENDIF.
      <fs_temp>-msg = ls_resp-msgtx.

      "进度条
      gv_sign = gv_sign + 1.
      gv_per  = gv_sign / gv_num * 100.
      gv_stxt = |当前条目 { gv_sign } / 总条目 { gv_num }|.
      CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
        EXPORTING
          percentage = gv_per
          text       = gv_stxt.
    ENDAT.
  ENDLOOP.

  "回写 ALV
  PERFORM frm_write_back_alv.
ENDFORM.
```

### 保存数据 - 抬头+行项目模式 (Header+Item)

适用于订单类场景（如销售订单、BOM、会计凭证）：

```abap
FORM frm_save_data.
  DATA: lv_flag   TYPE char1,
        lv_number TYPE zenumber,
        lv_field  TYPE fieldname VALUE 'NUMBER'.
  DATA: ls_req  TYPE zssdi001_req,
        ls_item TYPE zssdi001_item_in,
        ls_resp TYPE zsrest_out.

  PERFORM frm_before_import CHANGING lv_flag.
  CHECK lv_flag IS INITIAL.

  LOOP AT <ft_data> ASSIGNING <fs_data>.
    PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING lv_number.
    READ TABLE gt_temp ASSIGNING <fs_temp> WITH KEY number = lv_number BINARY SEARCH.
    IF sy-subrc <> 0.
      CONTINUE.
    ENDIF.

    "抬头（每条 NUMBER 的第一行）
    AT NEW (lv_field).
      CLEAR: ls_req, ls_resp.
      MOVE-CORRESPONDING <fs_data> TO ls_req-req-head.
    ENDAT.

    "行项目（每一行）
    CLEAR: ls_item.
    MOVE-CORRESPONDING <fs_data> TO ls_item.
    IF ls_item IS NOT INITIAL.
      APPEND ls_item TO ls_req-req-item.
    ENDIF.

    "每组 NUMBER 结束，调用接口
    AT END OF (lv_field).
      CALL FUNCTION 'ZFM_SDI001'
        EXPORTING
          i_req  = ls_req
        IMPORTING
          o_resp = ls_resp.

      "记录结果
      IF ls_resp-msgty = 'S'.
        <fs_temp>-id = icon_led_green.
      ELSE.
        <fs_temp>-id = icon_led_red.
      ENDIF.
      <fs_temp>-msg = ls_resp-msgtx.

      "进度条
      gv_sign = gv_sign + 1.
      gv_per  = gv_sign / gv_num * 100.
      gv_stxt = |当前条目 { gv_sign } / 总条目 { gv_num }|.
      CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
        EXPORTING
          percentage = gv_per
          text       = gv_stxt.
    ENDAT.
  ENDLOOP.

  "回写 ALV
  PERFORM frm_write_back_alv.
ENDFORM.
```

### 结果回写

```abap
FORM frm_write_back_alv.
  DATA: lv_number TYPE zenumber.

  LOOP AT <ft_data> ASSIGNING <fs_data>.
    CLEAR: lv_number.
    PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING lv_number.
    READ TABLE gt_temp ASSIGNING <fs_temp> WITH KEY number = lv_number BINARY SEARCH.
    IF sy-subrc = 0.
      PERFORM frm_convent_data_in USING 'ID'  <fs_temp>-id  CHANGING <fs_data>.
      PERFORM frm_convent_data_in USING 'MSG' <fs_temp>-msg CHANGING <fs_data>.
    ENDIF.
  ENDLOOP.
ENDFORM.
```

---

## 进度条

```abap
"进度条变量
DATA: gv_per  TYPE p,          "百分比
      gv_stxt TYPE string,     "显示文本
      gv_num  TYPE i VALUE 0,  "总条数
      gv_sign TYPE i VALUE 0.  "当前序号

"在 frm_before_import 中设置总数
gv_num = lines( gt_temp ).

"每处理完一条，更新进度
gv_sign = gv_sign + 1.
gv_per  = gv_sign / gv_num * 100.
gv_stxt = |当前条目 { gv_sign } / 总条目 { gv_num }|.
CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
  EXPORTING
    percentage = gv_per
    text       = gv_stxt.
```

---

## 动态内表字段读写

### 通用辅助函数

```abap
"读取动态内表字段值
FORM frm_convent_data_out USING p_data
                                p_fieldname
                       CHANGING c_value.
  ASSIGN COMPONENT p_fieldname OF STRUCTURE p_data TO <fs_value>.
  IF sy-subrc = 0.
    c_value = <fs_value>.
  ENDIF.
ENDFORM.

"写入动态内表字段值
FORM frm_convent_data_in USING p_fieldname
                               p_value
                      CHANGING p_data.
  ASSIGN COMPONENT p_fieldname OF STRUCTURE p_data TO <fs_value>.
  IF sy-subrc = 0.
    <fs_value> = p_value.
  ENDIF.
ENDFORM.
```

### 常用标准数据元素

| 数据元素 | 用途 | 说明 |
|----------|------|------|
| `ZENUMBER` | 排序号 | 自定义域，用于分组多行数据 |
| `ZESAPN` | SAP 返回单号 | 自定义域，如物料号、凭证号等 |
| `ICON_D` / `ICON-ID` | 状态图标 | 绿灯/红灯 |

---

## 完整程序模板

```abap
*&---------------------------------------------------------------------*
*& Report ZXXB001
*&---------------------------------------------------------------------*
*& Program Name                   ：ZXXB001
*& Program Description            : XX批导入
*& Company                        : 上海汉得-SAP项目
*& ABAPER                         ：HANDAI
*& Finish Date                    ：YYYYMMDD
*&---------------------------------------------------------------------*
*& Remark：XX批导入
*&   1). Excel 模板上传;
*&   2). 数据转换校验;
*&   3). 调用接口函数;
*&---------------------------------------------------------------------*
*& Change Record：
*& Date         Developer           ReqNo       Descriptions
*& ==========  ==================  ==========  ========================
*& YYYYMMDD     HANDAI               Transport    Create
*&---------------------------------------------------------------------*
REPORT zxxb001.

"----------------------------------------------------------------------*
" 全局类型定义
"----------------------------------------------------------------------*
TYPES: BEGIN OF ty_temp,
         number TYPE zenumber,
         id     TYPE icon_d,
         msg    TYPE bapi_msg,
       END OF ty_temp.

"----------------------------------------------------------------------*
" 全局变量
"----------------------------------------------------------------------*
DATA: gt_data  TYPE REF TO data.
DATA: gt_temp  TYPE TABLE OF ty_temp,
      gs_temp  TYPE ty_temp.

DATA: gv_per   TYPE p,
      gv_stxt  TYPE string,
      gv_num   TYPE i VALUE 0,
      gv_sign  TYPE i VALUE 0.

DATA: gt_fieldcat TYPE lvc_t_fcat,
      gs_fieldcat TYPE lvc_s_fcat,
      gs_layout   TYPE lvc_s_layo.

FIELD-SYMBOLS: <ft_data>  TYPE STANDARD TABLE,
               <fs_temp>  TYPE ty_temp,
               <fs_data>,
               <fs_value>.

"----------------------------------------------------------------------*
" 选择屏幕
"----------------------------------------------------------------------*
SELECTION-SCREEN BEGIN OF BLOCK blk WITH FRAME TITLE TEXT-001.
  PARAMETERS: rb_down TYPE char1 RADIOBUTTON GROUP grp1 USER-COMMAND cre,
              rb_upld TYPE char1 RADIOBUTTON GROUP grp1 DEFAULT 'X'.
  PARAMETERS: p_path  TYPE rlgrap-filename MODIF ID m2.
SELECTION-SCREEN END OF BLOCK blk.

INITIALIZATION.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_path.
  CALL FUNCTION 'KD_GET_FILENAME_ON_F4'
    CHANGING file_name = p_path.

AT SELECTION-SCREEN OUTPUT.
  LOOP AT SCREEN.
    IF screen-group1 = 'M2'.
      IF rb_upld = 'X'.
        screen-active = 1.
      ELSE.
        screen-active = 0.
      ENDIF.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP.

START-OF-SELECTION.
  IF rb_down = 'X'.
    PERFORM frm_download_file.
  ELSEIF rb_upld = 'X'.
    PERFORM frm_get_data.
    PERFORM frm_process_data.
    PERFORM frm_display_alv.
  ENDIF.

"----------------------------------------------------------------------*
" FORM 实现
"----------------------------------------------------------------------*

"----------------------------------------------------------------------*
" 模板下载
"----------------------------------------------------------------------*
FORM frm_download_file.
  DATA: lv_file   TYPE rlgrap-filename,
        lv_objid  TYPE wwwdata-objid,
        ls_key    TYPE wwwdatatab,
        lv_subrc  TYPE sy-subrc,
        lv_filename TYPE string,
        lv_path     TYPE string,
        lv_fullpath TYPE string,
        lv_default_file_name TYPE string.

  lv_default_file_name = TEXT-001 && '.xlsx'.
  CALL METHOD cl_gui_frontend_services=>file_save_dialog
    EXPORTING
      window_title      = '请选择路径'
      default_file_name = lv_default_file_name
      file_filter       = 'Excel 文件 (*.xlsx)'
    CHANGING
      filename          = lv_filename
      path              = lv_path
      fullpath          = lv_fullpath
    EXCEPTIONS
      OTHERS            = 1.

  lv_file  = lv_fullpath.
  lv_objid = sy-repid.

  IF lv_fullpath IS NOT INITIAL.
    SELECT SINGLE * FROM wwwdata
      INTO CORRESPONDING FIELDS OF ls_key
      WHERE objid = lv_objid AND relid = 'MI'.
    CALL FUNCTION 'DOWNLOAD_WEB_OBJECT'
      EXPORTING key = ls_key destination = lv_file
      IMPORTING rc  = lv_subrc.
    IF lv_subrc = 0.
      MESSAGE '模板下载成功' TYPE 'S'.
    ENDIF.
  ELSE.
    MESSAGE '下载取消！' TYPE 'S' DISPLAY LIKE 'E'.
  ENDIF.
ENDFORM.

"----------------------------------------------------------------------*
" 数据上传
"----------------------------------------------------------------------*
FORM frm_get_data.
  DATA: lt_return TYPE bapiret2_t,
        ls_return TYPE bapiret2,
        lv_msg    TYPE char220.

  REFRESH gt_fieldcat.
  CALL FUNCTION 'ZFM_GET_FIELDCAT'
    EXPORTING
      i_path      = p_path
      i_end_col   = 100
    TABLES
      et_fieldcat = gt_fieldcat
      et_return   = lt_return.

  IF lt_return IS NOT INITIAL.
    LOOP AT lt_return INTO ls_return WHERE type = 'E'.
      lv_msg = lv_msg && ls_return-message.
    ENDLOOP.
    IF lv_msg IS NOT INITIAL.
      MESSAGE lv_msg TYPE 'S' DISPLAY LIKE 'E'.
      STOP.
    ENDIF.
  ENDIF.

  CALL METHOD cl_alv_table_create=>create_dynamic_table
    EXPORTING it_fieldcatalog = gt_fieldcat
    IMPORTING ep_table        = gt_data.
  ASSIGN gt_data->* TO <ft_data>.

  CALL FUNCTION 'ZFM_GET_UPLOAD_DATA'
    TABLES et_data = <ft_data>.

  DELETE gt_fieldcat WHERE fieldname = 'CHECK'.

  "排序
  DATA(lt_sort) = VALUE abap_sortorder_tab(
    ( name = 'NUMBER' )
  ).
  SORT <ft_data> BY (lt_sort).
ENDFORM.

"----------------------------------------------------------------------*
" 数据转换
"----------------------------------------------------------------------*
FORM frm_process_data.
  "TODO: 添加业务特定的数据转换（单位、前导零等）
  IF <ft_data> IS NOT INITIAL.
    LOOP AT <ft_data> ASSIGNING <fs_data>.
      "单位转换示例
      CALL FUNCTION 'ZFM_CONVERSION_EXIT'
        EXPORTING
          iv_fieldname = 'MEINS'
          iv_exit      = zgl0_cunit_in
        CHANGING
          cs_data      = <fs_data>.
    ENDLOOP.
  ENDIF.
ENDFORM.

"----------------------------------------------------------------------*
" ALV 展示
"----------------------------------------------------------------------*
FORM frm_display_alv.
  CLEAR gs_layout.
  gs_layout-box_fname  = 'CHECK'.
  gs_layout-zebra      = 'X'.
  gs_layout-cwidth_opt = 'X'.

  CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY_LVC'
    EXPORTING
      i_callback_program       = sy-repid
      i_callback_pf_status_set = 'FRM_SET_PF_STATUS'
      i_callback_user_command  = 'FRM_USER_COMMAND'
      is_layout_lvc            = gs_layout
      it_fieldcat_lvc          = gt_fieldcat
      i_save                   = 'A'
    TABLES
      t_outtab                 = <ft_data>
    EXCEPTIONS
      program_error            = 1
      OTHERS                   = 2.
ENDFORM.

FORM frm_set_pf_status USING pt_extab TYPE slis_t_extab.
  SET PF-STATUS 'STANDARD'.
ENDFORM.

FORM frm_user_command USING pv_ucomm    TYPE syucomm
                            ps_selfield TYPE slis_selfield.
  DATA: lv_grid TYPE REF TO cl_gui_alv_grid.
  CALL FUNCTION 'GET_GLOBALS_FROM_SLVC_FULLSCR'
    IMPORTING e_grid = lv_grid.
  CALL METHOD lv_grid->check_changed_data.
  ps_selfield-refresh = 'X'.

  CASE pv_ucomm.
    WHEN 'ZLOAD'.
      PERFORM frm_save_data.
  ENDCASE.

  CALL METHOD lv_grid->refresh_table_display.
ENDFORM.

"----------------------------------------------------------------------*
" 数据导入
"----------------------------------------------------------------------*
FORM frm_save_data.
  DATA: lv_flag   TYPE char1,
        lv_number TYPE zenumber,
        lv_field  TYPE fieldname VALUE 'NUMBER'.

  "TODO: 替换为实际接口类型
  DATA: ls_req  TYPE zsxxi001_req,
        ls_resp TYPE zsrest_out.

  PERFORM frm_before_import CHANGING lv_flag.
  CHECK lv_flag IS INITIAL.

  LOOP AT <ft_data> ASSIGNING <fs_data>.
    PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING lv_number.
    READ TABLE gt_temp ASSIGNING <fs_temp> WITH KEY number = lv_number BINARY SEARCH.
    IF sy-subrc <> 0.
      CONTINUE.
    ENDIF.

    AT NEW (lv_field).
      CLEAR: ls_req, ls_resp.
      MOVE-CORRESPONDING <fs_data> TO ls_req-req.
    ENDAT.

    AT END OF (lv_field).
      "TODO: 替换为实际接口函数
      CALL FUNCTION 'ZFM_XXI001'
        EXPORTING i_req  = ls_req
        IMPORTING o_resp = ls_resp.

      IF ls_resp-msgty = 'S'.
        <fs_temp>-id = icon_led_green.
      ELSE.
        <fs_temp>-id = icon_led_red.
      ENDIF.
      <fs_temp>-msg = ls_resp-msgtx.

      gv_sign = gv_sign + 1.
      gv_per  = gv_sign / gv_num * 100.
      gv_stxt = |当前条目 { gv_sign } / 总条目 { gv_num }|.
      CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
        EXPORTING percentage = gv_per text = gv_stxt.
    ENDAT.
  ENDLOOP.

  "回写结果
  LOOP AT <ft_data> ASSIGNING <fs_data>.
    CLEAR: lv_number.
    PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING lv_number.
    READ TABLE gt_temp ASSIGNING <fs_temp> WITH KEY number = lv_number BINARY SEARCH.
    IF sy-subrc = 0.
      PERFORM frm_convent_data_in USING 'ID'  <fs_temp>-id  CHANGING <fs_data>.
      PERFORM frm_convent_data_in USING 'MSG' <fs_temp>-msg CHANGING <fs_data>.
    ENDIF.
  ENDLOOP.
ENDFORM.

"----------------------------------------------------------------------*
" 导入前检查
"----------------------------------------------------------------------*
FORM frm_before_import CHANGING p_flag.
  DATA: lv_number   TYPE zenumber,
        lv_checkbox TYPE char1,
        lv_id       TYPE icon-id.

  CLEAR: gt_temp.

  LOOP AT <ft_data> ASSIGNING <fs_data>.
    CLEAR: lv_checkbox, lv_id.
    PERFORM frm_convent_data_out USING <fs_data> 'CHECK' CHANGING lv_checkbox.
    PERFORM frm_convent_data_out USING <fs_data> 'ID'    CHANGING lv_id.
    IF lv_checkbox = 'X' AND lv_id <> icon_led_green.
      CLEAR: gs_temp.
      PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING gs_temp-number.
      APPEND gs_temp TO gt_temp.
    ENDIF.
  ENDLOOP.

  IF gt_temp IS NOT INITIAL.
    SORT gt_temp BY number.
    DELETE ADJACENT DUPLICATES FROM gt_temp COMPARING number.
    gv_num = lines( gt_temp ).

    LOOP AT <ft_data> ASSIGNING <fs_data>.
      CLEAR: lv_number.
      PERFORM frm_convent_data_out USING <fs_data> 'NUMBER' CHANGING lv_number.
      READ TABLE gt_temp TRANSPORTING NO FIELDS
        WITH KEY number = lv_number BINARY SEARCH.
      IF sy-subrc = 0.
        PERFORM frm_convent_data_in USING 'CHECK' 'X' CHANGING <fs_data>.
      ENDIF.
    ENDLOOP.
  ELSE.
    p_flag = 'X'.
    MESSAGE s001(zgl01) DISPLAY LIKE 'E'.
  ENDIF.
ENDFORM.

"----------------------------------------------------------------------*
" 动态内表字段读写
"----------------------------------------------------------------------*
FORM frm_convent_data_out USING p_data
                                p_fieldname
                       CHANGING c_value.
  ASSIGN COMPONENT p_fieldname OF STRUCTURE p_data TO <fs_value>.
  IF sy-subrc = 0.
    c_value = <fs_value>.
  ENDIF.
ENDFORM.

FORM frm_convent_data_in USING p_fieldname
                               p_value
                      CHANGING p_data.
  ASSIGN COMPONENT p_fieldname OF STRUCTURE p_data TO <fs_value>.
  IF sy-subrc = 0.
    <fs_value> = p_value.
  ENDIF.
ENDFORM.
```

---

## 禁止事项

| 禁止 | 原因 | 替代方案 |
|------|------|----------|
| 在批导程序中直接写 BAPI/BAPI_TRANSACTION_COMMIT | 业务逻辑应在接口函数模块中统一处理 | 在接口函数模块中调用 BAPI |
| 不处理 `ZFM_GET_FIELDCAT` 返回的错误 | 表头格式错误时继续执行会导致数据错乱 | 检查 `lt_return` 中 `type = 'E'` 的消息并 STOP |
| 不检查 `frm_before_import` 返回的 `p_flag` | 无选中数据时调用接口会出错 | `CHECK lv_flag IS INITIAL` |
| 不处理 `AT END OF` 中最后一条数据 | 最后一条数据可能不会被处理 | 确保 `AT END OF` 中调用接口 |
| 不写回 ALV 结果 | 用户不知道导入结果 | 写入 `ID`（图标）和 `MSG`（消息）字段 |
| 不限制 `i_end_col` | Excel 列数过多影响性能 | 根据实际列数设置合理的 `i_end_col`（通常 40-100） |
| 模板下载使用绝对路径 | 不同用户环境路径不同 | 使用 `cl_gui_frontend_services=>file_save_dialog` 让用户选择 |
| 忘记 `DELETE gt_fieldcat WHERE fieldname = 'CHECK'` | CHECK 列会在 ALV 中显示为普通列 | 删除后再传 ALV |