---
name: api-catalog
description: SAP 接口目录 — 130 系统全部 REST API 接口的编号、触发关键词、参数说明和 JSON 示例
---

# SAP 接口目录

> 本文档记录 SD1/Client 130 系统中所有已注册到 ZTREST_CONF 的 REST API 接口。
> 用于自然语言 → 接口匹配，帮助用户快速找到对应接口并填写参数。

## 接口总表

| 接口编号 | 接口名称 | 触发关键词 | 类型 | 模块 | 函数模块 |
|---------|---------|-----------|:----:|:----:|---------|
| AIGCI001 | 物料主数据状态查询(基本+工厂) | 物料状态、物料主数据状态、工厂视图 | Q | AI | ZFM_AIGC_MARAWERKS |
| AIGCI002 | 物料主数据状态查询(销售组织+分销渠道) | 物料状态、销售视图 | Q | AI | |
| AIGCI003 | 物料主数据状态查询(库存地点) | 物料状态、库存视图 | Q | AI | ZFM_AIGC_MARALGORT |
| AIGCI004 | 物料主数据状态查询(财务评估类) | 物料状态、财务视图 | Q | AI | |
| AII001 | 销售订单执行情况查询 | 销售订单、SO、订单执行 | Q | FI | ZFM_AII001 |
| EXAMI001 | 会计凭证创建 | 会计凭证、FI凭证、凭证创建 | M | FI | ZEXAM_FI001 |
| FII001 | 会计凭证创建 | 会计凭证、FI凭证、凭证创建 | M | FI | ZFM_FII001 |
| FII002 | 固定资产创建 | 固定资产、资产创建、固定资产新增 | M | FI | ZFM_FII002 |
| FII003 | 会计凭证冲销 | 凭证冲销、反记账、凭证取消 | M | FI | ZFM_FII003 |
| FII041 | 供应商主数据查询 | 供应商查询、供应商主数据 | Q | FI | ZFM_FII041 |
| MMI001 | 物料主数据维护 | 物料创建、物料修改、物料主数据 | M | MM | ZFM_MMI001 |
| MMI002 | 采购订单维护 | 采购订单、PO、创建采购单 | M | MM | ZFM_MMI002 |
| MMI003 | 采购申请维护 | 采购申请、PR、请购单 | M | MM | ZFM_MMI003 |
| MMI004 | 供应商维护 | 供应商创建、供应商修改 | M | MM | ZFM_MMI004 |
| MMI005 | 采购信息记录维护 | 信息记录、采购信息记录 | M | MM | ZFM_MMI005 |
| MMI006 | 物料移动 | 物料移动、收货、发货、转储 | M | MM | ZFM_MMI006 |
| MMI007 | 货源清单维护 | 货源清单 | M | MM | ZFM_MMI007 |
| MMI008 | 配额协议维护 | 配额协议 | M | MM | ZFM_MMI008 |
| MMI009 | 物料凭证冲销 | 物料凭证冲销、取消收货 | M | MM | ZFM_MMI009 |
| MMI010 | 预制发票维护 | 预制发票、发票校验 | M | MM | ZFM_MMI010 |
| MMI010_MRKO | 寄售类发票接口 | 寄售发票、代销发票 | M | MM | ZFM_MMI010_MRKO |
| MMI012 | 批次特性维护 | 批次、批次特性 | M | PP | ZFM_MMI012 |
| MMI013 | 内向交货单接口 | 内向交货单、采购交货 | M | PP | ZFM_MMI013 |
| PPI001 | BOM维护 | BOM、物料清单 | M | PP | ZFM_PPI001 |
| PPI002 | 计划订单维护 | 计划订单、计划订单创建 | M | PP | ZFM_PPI002 |
| PPI003 | 工艺路线维护 | 工艺路线 | M | PP | ZFM_PPI003 |
| PPI004 | 计划独立需求维护 | 独立需求、PIR | M | PP | ZFM_PPI004 |
| PPI005 | 生产订单维护 | 生产订单、工单、生产工单 | M | PP | ZFM_PPI005 |
| PPI006 | 生产订单报工维护 | 报工、工时确认、完工确认 | M | PP | ZFM_PPI006 |
| PPI007 | 生产版本主数据维护 | 生产版本 | M | PP | ZFM_PPI007 |
| PPI008 | 工作中心主数据 | 工作中心 | M | PP | ZFM_PPI008 |
| PPI009 | 组件分配维护 | 组件分配 | M | PP | ZFM_PPI009 |
| PPI010 | 生产订单(取消)关闭 | 订单关闭、订单取消、生产订单关闭 | M | PP | ZFM_PPI010 |
| PPI011 | 工艺路线主数据传输 | 工艺路线传输 | M | PP | ZFM_PPI011 |
| PPI012 | BOM主数据查询 | BOM查询 | Q | PP | ZFM_PPI012 |
| PPI013 | 订单组件批量更改 | 组件更改、订单组件 | M | PP | ZFM_PPI013 |
| PPI016 | 计划独立需求外部查询 | 独立需求查询、PIR查询 | Q | PP | ZFM_PPI016 |
| PPI017 | 工作中心查询 | 工作中心查询 | Q | PP | ZFM_PPI017 |
| PPI018 | 计划订单查询 | 计划订单查询 | Q | PS | ZFM_PPI018 |
| PPI019 | 生产订单查询 | 生产订单查询 | Q | PS | ZFM_PPI019 |
| PSI001 | 项目主数据查询 | 项目查询、WBS查询 | Q | PS | ZFM_PSI001 |
| PSI002 | 项目创建维护 | 项目创建、WBS创建 | M | PS | ZFM_PSI002 |
| PSI003 | 项目状态维护 | 项目状态、WBS状态 | M | QM | ZFM_PSI003 |
| PSI004 | 项目信息外部系统查询 | 项目信息查询 | Q | QM | ZFM_PSI004 |
| QMI001 | 检验特性维护 | 检验特性 | M | SD | ZFM_QMI001 |
| QMI002 | 检验计划维护 | 检验计划 | M | SD | ZFM_QMI002 |
| SDI001 | 销售订单维护 | 销售订单、SO、创建销售单 | M | SD | ZFM_SDI001 |
| SDI002 | 客户维护 | 客户创建、客户修改 | M | SD | ZFM_SDI002 |
| SDI003 | 价格主数据维护 | 价格主数据、定价条件 | M | SD | ZFM_SDI003 |
| SDI004 | 交货单创建修改 | 交货单、DN、发货单 | M | SD | ZFM_SDI004 |
| SDI005 | 信用主数据批量维护 | 信用主数据、信用额度 | M | SD | ZFM_SDI005 |
| SDI006 | 交货单拣配过账与冲销 | 拣配过账、交货单过账 | M | SD | ZFM_SDI006 |
| SDI007 | 客户物料主数据维护 | 客户物料、客户物料主数据 | M | SD | ZFM_SDI007 |
| SDI008 | 交货单查询 | 交货单查询 | M | SD | ZFM_SDI008 |
| SDI009 | 客户主数据查询 | 客户查询 | M | SD | ZFM_SDI009 |
| SDI010 | 销售订单外部系统信贷审批 | 信贷审批 | M | SD | ZFM_SDI010 |
| SDI011 | 交货单POD确认 | POD、交货单确认 | M | SD | ZFM_SDI011 |
| SDI013 | 交货单冲销删除 | 交货单冲销、删除交货单 | M | SD | ZFM_SDI013 |
| SDI014 | 交货单推送外部系统 | 交货单推送 | P | SD | ZFM_SDI014 |
| SDI047 | 交货单-创建拣配过账 | 创建交货单、拣配过账 | M | SD | ZFM_SDI047 |
| SRM201 | 业务实体数据同步 | 业务实体同步 | P | 接口 | ZFM_SRMO021 |
| SRM202 | 库存组织数据同步(工厂) | 工厂同步、库存组织同步 | P | 接口 | ZFM_SRMI202 |
| SRM205 | 采购组织数据同步 | 采购组织同步 | P | 接口 | ZFM_SRMI205 |
| SRM210 | ERP供应商数据同步 | 供应商同步 | P | 接口 | ZFM_SRMI210 |
| SRM212 | 物料品类数据同步 | 品类同步 | P | 接口 | ZFM_SRMI212 |
| SRM213 | 物料数据同步 | 物料同步 | P | 接口 | ZFM_SRMI213 |
| SRM401 | 采购申请导入SRM推送 | PR推送SRM | P | 接口 | ZFM_SRMI401 |
| SRM402 | 采购订单导入SRM推送 | PO推送SRM | P | 接口 | ZFM_SRMI402 |
| SRM403 | 采购接收导入SRM推送 | 收货推送SRM | P | 接口 | ZFM_SRMI403 |
| SRM414 | 供货能力清单导入SRM | 供货能力同步 | P | 接口 | ZFM_SRMI414 |
| SRM901_A | 文档UUID获取 | 文档UUID | P | 接口 | ZFM_SRMI901 |
| SRM901_B | 二进制文件推送 | 文件推送 | P | 接口 | ZFM_SRMI901 |
| Z10207 | AI预留接口 | AI接口 | M | 接口 | ZFM_MMI101 |
| Z10207_1 | AI测试物料接口 | AI测试 | M | 接口 | ZFM_MMI102 |
| Z10207_FI008 | 内部订单主数据创建接口(测试) | 内部订单、测试 | M | 接口 | ZFI_OA2SAP_FI008 |
| Z10207_MM004 | PR创建 | PR创建 | M | 接口 | Z10207PR_CREATE |
| Z10207_SD017 | OA查询销售订单接口 | OA查询、销售订单 | Q | 接口 | ZSD_OA2SAP_SD017 |
| ZHLY001 | 测试汇联易接口 | 汇联易、测试 | M | 接口 | ZFM_DEMO001 |

> 类型：`M`=写入接口, `Q`=查询接口, `P`=推送接口

> **注意**：接口编号（ZNUMB）是路由编号，实际业务由函数模块（ZFNAME）决定。
> 本目录记录的是按主键查询 ZTREST_CONF 获取的正确映射（ZNUMB 后缀与 ZFNAME 后缀对齐）。

---

## 接口详情

### 公共请求结构

所有接口的请求报文遵循统一框架：

```json
{
  "ZNUMB": "接口编号",
  "UUID": "32位随机字符串（脚本自动生成）",
  "FSYSID": "调用系统标识",
  "REQ": {
    // 业务参数，结构因接口而异
  }
}
```

### 公共响应结构

写入接口统一使用 `ZSREST_OUT`，查询接口使用专用 `ZSxxx_RESP`：

```json
{
  "msgty": "S",        // S=成功, E=错误, W=警告
  "msgtx": "消息文本",
  "uuid": "回显UUID",
  "sapnum": "单据号",
  "resp": []           // 查询接口的数据表
}
```

### 公共结构（ZSREST_IN / ZSREST_OUT）

**ZSREST_IN** — 所有接口的公共请求头（部分接口用 include 引入，部分接口直接平铺 uuid/znumb/fsysid）：

| 字段 | 类型 | 说明 |
|------|------|------|
| uuid | ZESYSUUID_C32 | 唯一标识（调用方生成，32位） |
| znumb | ZENUMB | 接口编号 |
| fsysid | ZEFSYSID | 调用系统标识，如 `BEATBOT`、`ERP` |

**ZSREST_OUT** — 所有写入接口的公共响应：

| 字段 | 类型 | 说明 |
|------|------|------|
| msgty | MSGTY | S=成功, E=错误, W=警告, I=信息 |
| msgtx | BAPI_MSG | 消息文本 |
| msgid | MSGID | 消息类 |
| msgno | MSGNO | 消息号 |
| uuid | ZESYSUUID_C32 | 回显 UUID（原样返回） |
| sapnum | ZESAPN | SAP 单据号 |
| field1~3 | CHAR20 | 预留字段 |

---

### AIGCI001 — 物料主数据状态查询（基本视图+工厂）

**函数模块**：ZFM_AIGC_MARAWERKS
**入参结构**：ZSAIGC001_REQ → ZSAIGC001_IN
**出参结构**：ZSAIGC001_RESP（含 ZSREST_OUT + resp: ZTAIGC_MARAWERKS_T）
**类型**：查询

**参数说明**：

| REQ 路径 | 字段 | 类型 | 必填 | 说明 |
|----------|------|------|:----:|------|
| req.ivMode | iv_mode | ZE_MODE | 否 | 模式：空/02=实时查询, 01=后台保存, 03=离线读表 |
| req.rtMatnr[].sign | SIGN | SIGN | 是 | RANGE 符号：I=包含, E=排除 |
| req.rtMatnr[].option | OPTION | OPTION | 是 | RANGE 选项：EQ/BT/CP/... |
| req.rtMatnr[].low | LOW | MATNR | 是 | 物料号（18位，带前导零） |
| req.rtMatnr[].high | HIGH | MATNR | 否 | 物料号高值（BT 区间时使用） |
| req.rtWerks[].sign | SIGN | SIGN | 是 | RANGE 符号 |
| req.rtWerks[].option | OPTION | OPTION | 是 | RANGE 选项 |
| req.rtWerks[].low | LOW | WERKS_D | **是** | 工厂 |
| req.rtWerks[].high | HIGH | WERKS_D | 否 | 工厂高值 |

**JSON 示例**：

```json
{
  "ZNUMB": "AIGCI001",
  "UUID": "<自动生成>",
  "FSYSID": "BEATBOT",
  "REQ": {
    "ivMode": "02",
    "rtMatnr": [{"sign": "I", "option": "EQ", "low": "000000001000000420"}],
    "rtWerks": [{"sign": "I", "option": "EQ", "low": "1000"}]
  }
}
```

---

### MMI001 / ZFM_MMI001 — 物料主数据维护

**函数模块**：ZFM_MMI001
**入参结构**：ZSMMI001_REQ → ZSMMI001_IN（head + mara + marc + marm + mbew + mvke + mlan + ausp）
**出参结构**：ZSREST_OUT
**类型**：写入

**参数说明**（完整字段见 xlsx 文档或 `GetStructure` 查询）：

| REQ 路径 | 字段 | 必填 | 说明 |
|----------|------|:----:|------|
| req.head.matnr | MATNR | **是** | 物料号（18位，带前导零） |
| req.head.basicView | BASIC_VIEW | 否 | 基本视图 |
| req.head.salesView | SALES_VIEW | 否 | 销售视图 |
| req.head.purchaseView | PURCHASE_VIEW | 否 | 采购视图 |
| req.head.mrpView | MRP_VIEW | 否 | MRP 视图 |
| req.mara.mtart | MTART | **是** | 物料类型 |
| req.mara.maktx | MAKTX | **是** | 物料描述 |
| req.mara.meins | MEINS | **是** | 基本计量单位 |
| req.mara.matkl | MATKL | **是** | 物料组 |
| req.marc[].werks | WERKS_D | **是** | 工厂 |
| req.marc[].ekgrp | EKGRP | **是** | 采购组 |
| req.marc[].dispo | DISPO | 否 | MRP 控制者 |
| req.marc[].dismm | DISMM | 否 | MRP 类型 |
| req.mbew[].bwkey | BWKEY | **是** | 评估范围 |
| req.mbew[].bklas | BKLAS | **是** | 评估类 |
| req.mbew[].vprsv | VPRSV | **是** | 价格控制 |

**JSON 示例**：

```json
{
  "ZNUMB": "MMI001",
  "UUID": "<自动生成>",
  "FSYSID": "BEATBOT",
  "REQ": {
    "head": {"matnr": "1000000043", "basicView": "X", "purchaseView": "X", "mrpView": "X", "accountView": "X", "costView": "X"},
    "mara": {"mtart": "ROH", "maktx": "测试物料", "meins": "ST", "matkl": "Z101"},
    "marc": [{"werks": "1000", "ekgrp": "101", "dismm": "ND"}],
    "mbew": [{"bwkey": "1000", "vprsv": "S", "bklas": "3001"}]
  }
}
```

---
### MMI002 / ZFM_MMI002 — 采购订单维护（PO）

**函数模块**：ZFM_MMI002
**入参结构**：ZSMMI002_REQ → ZSMMI002_IN（head + item[]）
**出参结构**：ZSREST_OUT
**类型**：写入（空 ebeln 创建，传 ebeln 修改）

**参数说明**：

| REQ 路径 | 字段 | 类型 | 必填 | 说明 |
|----------|------|------|:----:|------|
| req.head.ebeln | EBELN | 采购订单号 | 否 | 空=创建，传值=修改 |
| req.head.bsart | ESART | 采购订单类型 | **是** | 如 NB |
| req.head.lifnr | LIFNR | 供应商 | **是** | |
| req.head.ekorg | EKORG | 采购组织 | **是** | |
| req.head.ekgrp | BKGRP | 采购组 | **是** | |
| req.head.bukrs | BUKRS | 公司代码 | **是** | |
| req.head.zterm | DZTERM | 付款条件 | 否 | |
| req.item[].ebelp | EBELP | 行项目号 | **是** | 外部给号 |
| req.item[].matnr | MATNR | 物料号 | 是* | 与 txz01 至少一项 |
| req.item[].txz01 | TXZ01 | 短文本 | 是* | 文本行时填 |
| req.item[].menge | BSTMG | 数量 | **是** | |
| req.item[].meins | MEINS | 单位 | **是** | |
| req.item[].werks | WERKS_D | 工厂 | **是** | |
| req.item[].eindt | EINDT | 交货日期 | **是** | |
| req.item[].netpr | NETPR | 不含税单价 | 否 | |
| req.item[].waers | WAERS | 币种 | 否 | |

**JSON 示例**：

```json
{
  "ZNUMB": "MMI002",
  "UUID": "<自动生成>",
  "FSYSID": "BEATBOT",
  "REQ": {
    "head": {
      "bsart": "NB",
      "lifnr": "0000100000",
      "ekorg": "1000",
      "ekgrp": "101",
      "bukrs": "1000"
    },
    "item": [
      {
        "ebelp": "00010",
        "matnr": "000000001000000051",
        "txz01": "测试采购订单物料",
        "menge": 5,
        "meins": "ST",
        "werks": "1000",
        "eindt": "20261231",
        "netpr": "10.00",
        "waers": "CNY"
      }
    ]
  }
}

---

### MMI003 / ZFM_MMI003 — 采购申请维护（PR）

**函数模块**：ZFM_MMI003
**入参结构**：ZSMMI003_REQ → ZSMMI003_IN（head + item[]）
**出参结构**：ZSREST_OUT
**类型**：写入

| REQ 路径 | 字段 | 类型 | 必填 | 说明 |
|----------|------|------|:----:|------|
| req.head.banfn | BANFN | CHAR10 | 否 | 采购申请号（外部给号时传入） |
| req.head.bsart | BSART | CHAR4 | **是** | 采购申请类型（如 NB） |
| req.head.headTxt | HEAD_TXT | CHAR | 否 | 抬头文本 |
| req.item[].matnr | MATNR | CHAR40 | **是** | 物料号 |
| req.item[].menge | MENGE_D | QUAN13 | **是** | 采购数量 |
| req.item[].meins | MEINS | CHAR3 | **是** | 单位 |
| req.item[].werks | WERKS_D | CHAR4 | **是** | 工厂 |
| req.item[].lgort | LGORT_D | CHAR4 | 否 | 库存地点 |
| req.item[].ekgrp | EKGRP | CHAR3 | **是** | 采购组 |
| req.item[].ekorg | EKORG | CHAR4 | **是** | 采购组织 |
| req.item[].lfdat | LFDAT | DATS | 否 | 交货日期 |
| req.item[].kostl | KOSTL | CHAR10 | 否 | 成本中心 |
| req.item[].txz01 | TXZ01 | CHAR40 | 否 | 行项目短文本 |

### MMI004 / ZFM_MMI004 — 供应商维护

**函数模块**：ZFM_MMI004
**入参结构**：ZSMMI004_REQ → ZSMMI004_IN（central_data + bank_data[] + company_data[] + purchasing_data[]）
**出参结构**：ZSREST_OUT
**类型**：写入

| REQ 路径 | 字段 | 类型 | 必填 | 说明 |
|----------|------|------|:----:|------|
| req.centralData.lifnr | LIFNR | CHAR10 | 否 | 供应商号（外部给号时传入） |
| req.centralData.name1 | BU_NAMEOR1 | CHAR40 | **是** | 名称1 |
| req.centralData.buGroup | BU_GROUP | CHAR4 | **是** | 业务伙伴分组（如 BP01） |
| req.centralData.city1 | AD_CITY1 | CHAR40 | **是** | 城市 |
| req.centralData.street | AD_STREET | CHAR60 | 否 | 街道 |
| req.centralData.country | LAND1 | CHAR3 | 否 | 国家（CN） |
| req.companyData[].bukrs | BUKRS | CHAR4 | **是** | 公司代码 |
| req.companyData[].akont | AKONT | CHAR10 | **是** | 统驭科目 |
| req.companyData[].zterm | DZTERM | CHAR4 | 否 | 付款条件 |
| req.purchasingData[].ekorg | EKORG | CHAR4 | **是** | 采购组织 |
| req.bankData[].banks | BU_BANKS | CHAR3 | 否 | 银行国家 |
| req.bankData[].bankl | BU_BANKK | CHAR15 | 否 | 银行代码 |
| req.bankData[].bankn | BU_BANKN | CHAR18 | 否 | 银行账号 |

---

### SDI001 / ZFM_SDI001 — 销售订单维护
**函数模块**：ZFM_SDI001
**入参结构**：ZSSDI001_REQ → ZSSDI001_IN（head + item[] + 定价 + 计划行）
**出参结构**：ZSSDI003_RESP
**类型**：写入

**主要字段**：

| REQ 路径 | 字段 | 必填 | 说明 |
|----------|------|:----:|------|
| req.head.auart | AUART | **是** | 订单类型（如 TA, OR） |
| req.head.vkorg | VKORG | **是** | 销售组织 |
| req.head.vtweg | VTWEG | **是** | 分销渠道 |
| req.head.spart | SPART | **是** | 产品组 |
| req.head.kunag | KUNAG | **是** | 售达方 |
| req.head.kunwe | KUNWE | **是** | 送达方 |
| req.head.bstkd | BSTKD | 否 | 客户采购订单号 |
| req.head.waerk | WAERK | 否 | 货币 |
| req.head.zterm | DZTERM | 否 | 付款条件 |
| req.item[].matnr | MATNR | **是** | 物料 |
| req.item[].zmeng | ZMENG | **是** | 目标数量 |
| req.item[].vrkme | MEINS | **是** | 销售单位 |
| req.item[].werks | WERKS_D | **是** | 工厂 |
| req.schedule[].edatu | EDATU | **是** | 计划交货日期 |
| req.schedule[].wmeng | WMENG | **是** | 计划数量 |

**JSON 示例**：

```json
{
  "ZNUMB": "SDI001",
  "UUID": "<自动生成>",
  "FSYSID": "BEATBOT",
  "REQ": {
    "head": {
      "auart": "TA",
      "vkorg": "1000",
      "vtweg": "10",
      "spart": "00",
      "kunag": "0000010001",
      "kunwe": "0000010001",
      "bstkd": "PO12345",
      "waerk": "CNY",
      "zterm": "0001"
    },
    "item": [
      {
        "matnr": "000000001000000420",
        "zmeng": 100,
        "vrkme": "PC",
        "werks": "1000"
      }
    ],
    "schedule": [
      {
        "edatu": "2026-10-01",
        "wmeng": 100
      }
    ]
  }
}

---

### FII003 / ZFM_FII003 — 会计凭证冲销

**函数模块**：ZFM_FII003
**入参结构**：ZSFII003_REQ → ZSFII003_IN
**出参结构**：ZSREST_OUT

| REQ 字段 | 必填 | 说明 |
|----------|:----:|------|
| req.belnr | **是** | 凭证号 |
| req.bukrs | **是** | 公司代码 |
| req.gjahr | **是** | 会计年度 |
| req.stgrd | **是** | 冲销原因 |
| req.budat | **是** | 过账日期 |

---

### EXAMI001 / ZEXAM_FI001 — 会计凭证创建

**函数模块**：ZEXAM_FI001
**入参结构**：由 ZTREST_CONF 配置决定，用 `GetStructure` 查询实际结构
**出参结构**：ZSREST_OUT
**类型**：写入

---

---

### PPI005 / ZFM_PPI005 — 生产订单维护

**函数模块**：ZFM_PPI005
**入参结构**：ZSPPI005_REQ → ZSPPI005_IN
**出参结构**：ZSREST_OUT
**类型**：写入

| REQ 路径 | 字段 | 必填 | 说明 |
|----------|------|:----:|------|
| req.matnr | MATNR | **是** | 物料 |
| req.werks | WERKS_D | **是** | 工厂 |
| req.aufnr | AUFNR | 否 | 订单号（修改时传入） |
| req.gstrp | GSTRP | **是** | 基本开始日期 |
| req.gmein | GMEIN | **是** | 基本计量的单位 |
| req.text1 | TXT01 | 否 | 订单文本 |

---
### PSI002 / ZFM_PSI002 — 项目创建维护

**函数模块**：ZFM_PSI002
**入参结构**：由 ZTREST_CONF 配置决定，用 `GetStructure` 查询实际结构
**出参结构**：由 ZTREST_CONF 配置决定
**类型**：写入

---
## 自然语言 → 接口匹配指南

| 用户说 | 匹配接口 | 需用户提供 |
|--------|---------|-----------|
| "创建物料主数据" | MMI001 (ZFM_MMI001) | 物料号、基本视图、工厂视图、销售视图等 |
| "创建采购订单/PO/采购单" | MMI002 (ZFM_MMI002) | 订单类型、供应商、采购组织、物料、数量、工厂、交货日期 |
| "创建采购申请/PR/请购单" | MMI003 (ZFM_MMI003) | 物料、数量、工厂、采购组、采购组织 |
| "创建供应商/供应商维护" | MMI004 (ZFM_MMI004) | 名称、分组、公司代码、统驭科目、采购组织 |
| "创建销售订单/SO" | SDI001 (ZFM_SDI001) | 订单类型、销售组织、售达方、物料、数量、交货日期 |
| "创建客户/客户维护" | SDI002 (ZFM_SDI002) | 客户信息、销售数据 |
| "创建交货单/DN" | SDI004 (ZFM_SDI004) | 销售订单号、物料、数量 |
| "创建生产订单/工单" | PPI005 (ZFM_PPI005) | 物料、工厂、生产版本 |
| "生产订单报工/完工确认" | PPI006 (ZFM_PPI006) | 订单号、数量、工时 |
| "创建会计凭证/FI凭证" | FII001 (ZFM_FII001) | 凭证类型、公司代码、行项目 |
| "凭证冲销/反记账" | FII003 (ZFM_FII003) | 凭证号、公司代码、年度、冲销原因 |
| "创建固定资产" | EXAMI001 (ZEXAM_FI001) | 资产分类、公司代码、描述、金额 |
| "查询物料状态" | AIGCI001 | 物料号、工厂 |
| "查询供应商" | FII041 (ZFM_FII041) | 供应商号 |
| "查询交货单" | SDI008 (ZFM_SDI008) | 交货单号 |
| "查询项目/WBS" | PSI001 (ZFM_PSI001) | 项目号 |
| "BOM维护" | PPI001 (ZFM_PPI001) | 物料、工厂、BOM数据 |
| "工艺路线维护" | PPI003 (ZFM_PPI003) | 物料、工厂、工艺路线数据 |
