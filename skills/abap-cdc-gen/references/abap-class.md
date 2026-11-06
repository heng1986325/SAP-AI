---
name: abap-class
description: ABAP 类与接口开发规范 — 命名、结构、可见性、方法、异常处理、测试类、BadI
---

# ABAP 类与接口规范

## 目录

- [核心要求](#核心要求)
- [命名规范](#命名规范)
- [类结构](#类结构)
- [方法参数](#方法参数)
- [构造函数](#构造函数)
- [异常处理](#异常处理)
- [局部测试类](#局部测试类)
- [BadI 实现类](#badi-实现类)
- [类中的 ALV](#类中的-alv)
- [现代语法在类中的应用](#现代语法在类中的应用)

---

## 核心要求

**所有 ABAP 类与接口必须遵循以下规范。通用编码规范（命名、SELECT、注释等）见 [abap-coding.md](abap-coding.md)。**

---

## 命名规范

### 类名

```
ZCL_<模块>_<描述>
```

| 前缀 | 说明 | 示例 |
|------|------|------|
| `ZCL_` | 普通类 | `ZCL_MM_ARTICLE`, `ZCL_FI_POSTING` |
| `ZCX_` | 异常类 | `ZCX_MM_VALIDATION`, `ZCX_FI_AMOUNT` |

### 接口名

```
ZIF_<模块>_<描述>
```

| 前缀 | 说明 | 示例 |
|------|------|------|
| `ZIF_` | 普通接口 | `ZIF_MM_ARTICLE`, `ZIF_FI_POSTING` |

### 方法名

**动词 + 名词**，描述方法做什么，不是怎么做。

| 动词 | 用途 | 示例 |
|------|------|------|
| `GET_` | 读取数据 | `GET_DATA`, `GET_MATERIAL` |
| `SET_` | 设置属性 | `SET_STATUS`, `SET_HEADER` |
| `CHECK_` | 校验 | `CHECK_AUTHORITY`, `CHECK_INPUT` |
| `VALIDATE_` | 验证 | `VALIDATE_MATERIAL`, `VALIDATE_AMOUNT` |
| `CALCULATE_` | 计算 | `CALCULATE_TOTAL`, `CALCULATE_TAX` |
| `CONVERT_` | 转换 | `CONVERT_UNIT`, `CONVERT_CURRENCY` |
| `BUILD_` / `CREATE_` | 构建/创建 | `BUILD_ALV`, `CREATE_ORDER` |
| `DISPLAY_` / `SHOW_` | 显示 | `DISPLAY_ALV`, `SHOW_MESSAGE` |
| `HANDLE_` / `ON_` | 事件处理 | `HANDLE_HOTSPOT`, `ON_USER_COMMAND` |
| `IS_` / `HAS_` | 布尔判断 | `IS_VALID`, `HAS_ERRORS` |

```abap
"❌ 错误 — 无意义名称
METHODS: m1, proc, do_it.

"✅ 正确 — 动词 + 名词
METHODS: get_data,
         validate_material,
         calculate_total.
```

---

## 类结构

### 标准结构

```abap
CLASS zcl_mm_article DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    "类型定义
    TYPES: BEGIN OF ty_result,
             matnr TYPE matnr,
             maktx TYPE maktx,
           END OF ty_result.

    "常量
    CONSTANTS: gc_flag_x TYPE flag VALUE 'X'.

    "方法
    METHODS: constructor,
             get_data
               IMPORTING iv_matnr       TYPE matnr
               RETURNING VALUE(rs_data) TYPE ty_result,

             display_alv.

  PROTECTED SECTION.
    "供子类使用的方法和数据

  PRIVATE SECTION.
    "内部方法
    METHODS: validate_input
               IMPORTING iv_matnr       TYPE matnr
               RETURNING VALUE(rv_valid) TYPE abap_bool.

    "成员变量
    DATA: mv_matnr TYPE matnr,
          mt_data  TYPE STANDARD TABLE OF ty_result.

ENDCLASS.

CLASS zcl_mm_article IMPLEMENTATION.

  METHOD constructor.
    "初始化
  ENDMETHOD.

  METHOD get_data.
    "实现
  ENDMETHOD.

  METHOD display_alv.
    "实现
  ENDMETHOD.

  METHOD validate_input.
    "实现
  ENDMETHOD.

ENDCLASS.
```

### 可见性规则

| 可见性 | 用途 | 示例 |
|--------|------|------|
| `PUBLIC SECTION` | 外部调用接口、类型、常量 | `get_data`, `display_alv` |
| `PROTECTED SECTION` | 供子类继承使用 | 模板方法中的钩子方法 |
| `PRIVATE SECTION` | 内部实现细节 | 成员变量、内部辅助方法 |

**原则**：优先 `PRIVATE`，需要被子类使用时用 `PROTECTED`，对外暴露的用 `PUBLIC`。

---

## 方法参数

### 参数方向

```abap
METHODS: method_name
  IMPORTING iv_param1      TYPE typ1         "输入参数
  EXPORTING ev_param2      TYPE typ2         "输出参数
  CHANGING  cv_param3      TYPE typ3         "修改参数
  RETURNING VALUE(rv_result) TYPE typ4.      "返回值（仅一个）
```

### 参数命名

| 方向 | 前缀 | 示例 |
|------|------|------|
| IMPORTING | `I_` / `IV_` | `IV_MATNR`, `I_BUKRS` |
| EXPORTING | `E_` / `EV_` | `EV_RESULT`, `E_MESSAGE` |
| CHANGING | `C_` / `CV_` | `CV_COUNT`, `C_DATA` |
| RETURNING | `R_` / `RV_` | `RV_VALID`, `R_RESULT` |

### 参数设计原则

- 优先用 `RETURNING` 而非 `EXPORTING`（只有一个返回值时）
- 不导出不需要的参数
- 复杂结构用 `TYPE` 定义类型，不传大量单独参数

```abap
"❌ 错误 — 大量单独参数
METHODS: create_order
  IMPORTING iv_kunnr  TYPE kunnr
            iv_vkorg  TYPE vkorg
            iv_vtweg  TYPE vtweg
            iv_spart  TYPE spart
            iv_werks  TYPE werks_d
            iv_lgort  TYPE lgort_d
            iv_matnr  TYPE matnr
            iv_menge  TYPE menge_d
            iv_meins  TYPE meins.

"✅ 正确 — 结构化参数，用 TYPE 定义
TYPES: BEGIN OF ty_order_input,
         kunnr TYPE kunnr,
         vkorg TYPE vkorg,
         vtweg TYPE vtweg,
         spart TYPE spart,
         werks TYPE werks_d,
         lgort TYPE lgort_d,
         matnr TYPE matnr,
         menge TYPE menge_d,
         meins TYPE meins,
       END OF ty_order_input.

METHODS: create_order
  IMPORTING is_input TYPE ty_order_input.
```

---

## 构造函数

### CONSTRUCTOR（实例构造器）

```abap
"❌ 错误 — 构造器做大量业务逻辑
METHOD constructor.
  "不要在这里做 SELECT、调用 BAPI 等
  SELECT * FROM mara INTO TABLE mt_data.
ENDMETHOD.

"✅ 正确 — 构造器只做初始化
METHOD constructor.
  "只初始化成员变量
  CLEAR: mv_matnr, mt_data.
ENDMETHOD.
```

### CLASS_CONSTRUCTOR（类构造器）

```abap
CLASS zcl_util DEFINITION.
  PUBLIC SECTION.
    CLASS-DATA: gv_instance_count TYPE i.
    CLASS-METHODS: class_constructor.
ENDCLASS.

CLASS zcl_util IMPLEMENTATION.
  METHOD class_constructor.
    "类加载时执行一次，初始化静态数据
    gv_instance_count = 0.
  ENDMETHOD.
ENDCLASS.
```

---

## 异常处理

### 类内部异常处理

```abap
METHOD process_data.
  TRY.
      "可能出错的操作
      lo_api->post( is_data ).

    CATCH cx_sy_arithmetic_error INTO DATA(lx_math).
      "算术异常
      MESSAGE lx_math->get_text( ) TYPE 'E'.

    CATCH cx_root INTO DATA(lx_root).
      "通用异常兜底
      MESSAGE lx_root->get_text( ) TYPE 'E'.
  ENDTRY.
ENDMETHOD.
```

### 自定义异常类

```abap
"定义异常类
CLASS zcx_mm_validation DEFINITION
  INHERITING FROM cx_static_check
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    METHODS: constructor
      IMPORTING textid   LIKE textid OPTIONAL
                previous LIKE previous OPTIONAL
                iv_field TYPE fieldname,
      get_field RETURNING VALUE(rv_field) TYPE fieldname.

  PRIVATE SECTION.
    DATA: mv_field TYPE fieldname.

ENDCLASS.

CLASS zcx_mm_validation IMPLEMENTATION.
  METHOD constructor.
    super->constructor( textid = textid previous = previous ).
    mv_field = iv_field.
  ENDMETHOD.
  METHOD get_field.
    rv_field = mv_field.
  ENDMETHOD.
ENDCLASS.

"使用异常类
METHOD validate_material.
  IF iv_matnr IS INITIAL.
    RAISE EXCEPTION TYPE zcx_mm_validation
      EXPORTING iv_field = 'MATNR'.
  ENDIF.
ENDMETHOD.
```

---

## 局部测试类

### 测试类结构

```abap
CLASS lcl_test DEFINITION
  FINAL
  FOR TESTING
  RISK LEVEL HARMLESS
  DURATION SHORT.

  PRIVATE SECTION.
    "被测对象
    DATA: mo_cut TYPE REF TO zcl_mm_article.

    "测试数据
    DATA: mv_matnr TYPE matnr.

    "Setup/Teardown
    METHODS: setup,
             teardown.

    "测试方法
    METHODS: get_data_ok     FOR TESTING,
             get_data_not_found FOR TESTING,
             validate_input_ok FOR TESTING.

ENDCLASS.

CLASS lcl_test IMPLEMENTATION.

  METHOD setup.
    "每个测试方法前执行
    mo_cut = NEW #( ).
    mv_matnr = 'MAT001'.
  ENDMETHOD.

  METHOD teardown.
    "每个测试方法后执行
    CLEAR: mo_cut, mv_matnr.
  ENDMETHOD.

  METHOD get_data_ok.
    "正常场景
    DATA(ls_result) = mo_cut->get_data( mv_matnr ).

    cl_abap_unit_assert=>assert_not_initial( ls_result ).
    cl_abap_unit_assert=>assert_equals(
      act = ls_result-matnr
      exp = 'MAT001' ).
  ENDMETHOD.

  METHOD get_data_not_found.
    "异常场景
    DATA(ls_result) = mo_cut->get_data( 'INVALID' ).

    cl_abap_unit_assert=>assert_initial( ls_result ).
  ENDMETHOD.

  METHOD validate_input_ok.
    "边界场景
    DATA(lv_valid) = mo_cut->validate_input( '' ).

    cl_abap_unit_assert=>assert_false( lv_valid ).
  ENDMETHOD.

ENDCLASS.
```

### 测试类命名

| 类名 | 说明 |
|------|------|
| `LTCL_<类名>` | 局部测试类，如 `LTCL_ARTICLE` |
| `LCL_<描述>` | 局部辅助类，如 `LCL_DATA_GENERATOR` |

---

## BadI 实现类

### 命名规范

```
ZCL_IM_<BADI_NAME>
```

```abap
"示例：MB_DOCUMENT_BADI 的增强实现
CLASS zcl_im_mb_document_badi DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

  PUBLIC SECTION.
    INTERFACES: if_ex_mb_document_badi.

ENDCLASS.

CLASS zcl_im_mb_document_badi IMPLEMENTATION.

  METHOD if_ex_mb_document_badi~mb_document_before_update.
    "实现增强逻辑
  ENDMETHOD.

  METHOD if_ex_mb_document_badi~mb_document_update.
    "实现增强逻辑
  ENDMETHOD.

ENDCLASS.
```

---

## 类中的 ALV

### 使用 CL_SALV_TABLE

```abap
CLASS zcl_mm_report DEFINITION.
  PRIVATE SECTION.
    DATA: mo_alv TYPE REF TO cl_salv_table.

    METHODS: build_alv,
             set_columns,
             set_layout,
             display_alv.
ENDCLASS.

CLASS zcl_mm_report IMPLEMENTATION.

  METHOD build_alv.
    TRY.
        cl_salv_table=>factory(
          IMPORTING r_salv_table = mo_alv
          CHANGING  t_table      = mt_data ).

        "设置列属性
        set_columns( ).

        "设置布局
        set_layout( ).

      CATCH cx_salv_msg INTO DATA(lx_msg).
        MESSAGE lx_msg->get_text( ) TYPE 'E'.
    ENDTRY.
  ENDMETHOD.

  METHOD set_columns.
    DATA(lo_columns) = mo_alv->get_columns( ).
    lo_columns->set_optimize( abap_true ).

    "设置关键列
    TRY.
        DATA(lo_column) = lo_columns->get_column( 'MATNR' ).
        lo_column->set_key( abap_true ).
        lo_column->set_long_text( '物料号' ).
      CATCH cx_salv_not_found.
    ENDTRY.
  ENDMETHOD.

  METHOD set_layout.
    DATA(lo_layout) = mo_alv->get_layout( ).
    lo_layout->set_zebra( abap_true ).
    lo_layout->set_default( abap_true ).
  ENDMETHOD.

  METHOD display_alv.
    mo_alv->display( ).
  ENDMETHOD.

ENDCLASS.
```

**禁止使用 `REUSE_ALV_GRID_DISPLAY`**，使用 `CL_SALV_TABLE` 代替。

---

## 现代语法在类中的应用

### 内联声明

```abap
"❌ 错误 — 提前声明所有变量
DATA lv_index TYPE i.
DATA lv_message TYPE string.
lv_index = 1.
lv_message = 'OK'.

"✅ 正确 — 内联声明
DATA(lv_index) = 1.
DATA(lv_message) = 'OK'.
```

### NEW 和 REF

```abap
"❌ 错误
DATA lo_obj TYPE REF TO zcl_util.
CREATE OBJECT lo_obj.

"✅ 正确
DATA(lo_obj) = NEW zcl_util( ).
```

### 表表达式

```abap
"❌ 错误
READ TABLE lt_data INTO ls_data WITH KEY matnr = 'MAT001'.

"✅ 正确
ls_data = lt_data[ matnr = 'MAT001' ].
```

### FOR 表达式

```abap
"❌ 错误
DATA lt_matnr TYPE TABLE OF matnr.
LOOP AT lt_data INTO ls_data.
  APPEND ls_data-matnr TO lt_matnr.
ENDLOOP.

"✅ 正确
DATA(lt_matnr) = VALUE matnr_table(
  FOR ls IN lt_data ( ls-matnr )
).
```