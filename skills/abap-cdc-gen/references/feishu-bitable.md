---
name: feishu-bitable
description: 飞书多维表格集成 — 开发前必须先查飞书标准化清单，在飞书验证系统验证对象是否存在
---

# 飞书 Bitable 集成

> 下文脚本路径以 Claude Code 安装目录 `~/.claude/skills/abap-cdc-gen/` 为例；Codex 用户把 `.claude` 换成 `.codex`。

## 核心原则

**创建新 ABAP 对象或查找已有对象前，必须先查飞书标准化清单。不跳过此步骤。**

**为什么**：飞书清单是团队的标准化开发登记中心，记录了所有已开发/待开发的对象。跳过此步骤可能导致重复开发，或与已有命名冲突。

**边界条件** — 以下情况不需要查飞书：
- 仅修改现有代码（不创建新对象）
- 临时测试/学习用的本地对象（`$TMP`）

---

## 什么时候查飞书

以下操作前必须触发飞书查询：
- 创建新的 ABAP 程序、函数模块、类、事务码
- 查找已有开发对象
- 检查某个程序/事务/函数是否已存在
- 按模块（FI、CO、SD、MM 等）或描述查找对象

---

## 如何查询

```bash
# 在线搜索（默认，直接调飞书 API）
python "~/.claude/skills/abap-cdc-gen/scripts/feishu_search.py" "<关键词>"

# 离线搜索（从本地缓存搜索，无需联网）
python "~/.claude/skills/abap-cdc-gen/scripts/feishu_search.py" "<关键词>" --offline

# 先同步再搜索（确保数据最新）
python "~/.claude/skills/abap-cdc-gen/scripts/feishu_search.py" "<关键词>" --sync
```

关键词可以是：
- 程序名：`"ZFIR006"`
- 事务码：`"ZMM01"`
- 描述关键词：`"应收"`, `"采购"`, `"对账"`
- 模块前缀：`"FI"`, `"MM"`, `"SD"`

### 本地缓存

飞书清单自动同步到本地 markdown 文件，支持离线搜索：

```bash
# 手动同步
python "~/.claude/skills/abap-cdc-gen/scripts/feishu_sync.py"

# 本地缓存位置
~/.claude/skills/abap-cdc-gen/feishu_checklist.md
```

**定时同步 — 两种方式**：

| 方式 | 适用场景 | 安装 |
|------|---------|------|
| **Windows 任务计划**（推荐） | 团队共享，一次安装永久生效 | `powershell -ExecutionPolicy Bypass -File ~/.claude/skills/abap-cdc-gen/scripts/install_sync_task.ps1` |
| **Claude Code Cron** | 个人使用，依赖 Claude Code 运行 | 每人执行一次 `CronCreate` |

> Windows 任务计划方式独立于 Claude Code，即使未打开 VS Code 也会在后台定时运行。安装脚本只需在每台机器上执行一次。

---

## 结果处理

### 三步决策流程

```
飞书查询 → 飞书验证系统验证 → 向用户报告
```

### 飞书配置

- **表格**：14.标准化清单_OP&PCE
- **字段**：程序名、开发程序描述、事务代码、函数名、一级分类、二级分类、开发类型、开发申请
- **配置文件**：[../feishu_config.json](../feishu_config.json)
- **脚本**：[../scripts/feishu_search.py](../scripts/feishu_search.py)

### 结果处理规则

| 飞书状态 | 飞书验证系统状态 | 操作 |
|----------|-------------|------|
| ✅ 已登记 | ✅ 已存在 | 告知用户已存在，**不需要分析代码**，直接询问用户要做什么（复制到目标系统、打开参考等） |
| ✅ 已登记 | ❌ 不存在 | 告知用户已登记但未开发，询问是否新建 |
| ❌ 未找到 | - | 询问是否新建，并建议录入飞书清单 |

### 验证规则

**飞书验证系统是统一代码库的唯一真相来源。** 始终在飞书验证系统验证对象是否存在，不在目标系统验证。其他系统可能没有相同对象。

```bash
# 在飞书验证系统验证对象是否存在
SearchObject(object_name: "ZFIR006*", object_type: "PROG", maxResults: 100)
```

### 示例

```bash
# 用户说"帮我创建一个应收对账报表"
# 第一步：查飞书
python "~/.claude/skills/abap-cdc-gen/scripts/feishu_search.py" "应收对账"

# 飞书返回：ZFIR006 应收对账报表 已登记
# 第二步：在飞书验证系统验证
SearchObject(object_name: "ZFIR006", object_type: "PROG", maxResults: 100)

# 第三步：报告
# 场景A：飞书✅ + 飞书验证系统✅ → "ZFIR006 应收对账报表已存在，你希望我做什么？"
# 场景B：飞书✅ + 飞书验证系统❌ → "已登记但未开发，是否新建？"
# 场景C：飞书❌ → "未找到，是否新建并录入清单？"
```