# ABAP 开发技能包（abap-cdc-gen）

> 适用项目：`hand-300940-sap-ai-build/scc`（猪齿鱼）
>
> 一个可被 **Claude Code** 和 **Codex** 加载的 ABAP 开发技能，涵盖编码规范、开发工作流、飞书清单查询、SAP REST API 调用与代码质量检查。

## 1. 前置条件

| 工具 | 用途 | 获取方式 |
|------|------|----------|
| **mcp-abap-adt MCP + SAP 连接** | ABAP 开发（依赖 `mcp__mcp-abap-adt__*` 工具） | 前提条件，需先配置好 |
| **VS Code** | 编辑器 | https://code.visualstudio.com/ |
| **Claude Code / Codex** | AI 编程助手 | 内部分发 |
| **Git** | 版本控制 | https://git-scm.com/ |
| **猪齿鱼 SSH Key** | 代码拉取/推送 | 见下方配置 |
| **飞书自建应用凭据** | 飞书清单查询 | 见「配置飞书」 |

> ⚠️ **mcp-abap-adt MCP 与 SAP 连接是本技能的前置依赖，使用前需先配置好**（由团队统一分发与配置，本技能不含其安装步骤）。

## 2. 配置猪齿鱼 SSH 密钥

### 2.1 生成密钥（如已有可跳过）

```bash
ssh-keygen -t ed25519 -C "你的邮箱@hand-china.com"
# 一路回车即可
```

### 2.2 添加公钥到猪齿鱼

```bash
cat ~/.ssh/id_ed25519.pub
```

登录 [code.choerodon.com.cn](https://code.choerodon.com.cn) → 右上角头像 → **个人设置** → **SSH 密钥** → 粘贴公钥 → 保存。

## 3. 安装技能

技能需要安装到 AI 助手的**全局技能目录**，重启 Claude Code / Codex 后生效。

### 3.1 克隆仓库

```bash
git clone git@code.choerodon.com.cn:hand-300940-sap-ai-build/scc.git
cd scc
```

### 3.2 构建

第一次克隆后，需要先构建编译后的指令文件：

```bash
node skills/abap-cdc-gen/build-skill.mjs
```

构建脚本会把 `references/` 目录下的 7 个规范文件编译为 `build/bundle.json`（单行 minified JSON），供 AI 加载执行。

> 后续更新时，如果只改了 `references/*.md`，也需要重新执行此步骤。详见下方「更新技能」。

### 3.3 一键安装（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

脚本会检查 `build/bundle.json` 是否存在，然后把技能复制到：

- Claude Code：`~/.claude/skills/abap-cdc-gen/`
- Codex：`~/.codex/skills/abap-cdc-gen/`

飞书配置（`feishu_config.json`）已随技能包提交，安装后即用，无需填写。

### 3.4 手动安装（可选）

只用一个工具时，把 `skills/abap-cdc-gen/` 整个目录复制到对应位置即可：

- Claude Code：`~/.claude/skills/abap-cdc-gen/`（项目级则为 `<项目>/.claude/skills/abap-cdc-gen/`）
- Codex：`~/.codex/skills/abap-cdc-gen/`

> ⚠️ **技能不会因为"把目录放进项目根目录"就被自动发现**——必须放到上述固定位置，且入口文件必须叫 `SKILL.md`（大写）。安装后需重启 AI 助手才会扫描到。

## 4. 配置飞书

公开版不含飞书凭据：安装后编辑 `feishu_config.json`，填入飞书自建应用 `app_secret` 与多维表 `base_token`（向管理员索取，切勿提交到公开仓库）。

```json
{
  "app_id": "cli_a6b6e185e45d900c",
  "app_secret": "<YOUR_APP_SECRET>",
  "base_token": "<YOUR_BASE_TOKEN>",
  "table_id": "tblxDzi8Q1pt5vjm",
  "table_name": "14.标准化清单_OP&PCE",
  "search_fields": ["程序名", "开发程序描述", "事务代码", "函数名", "文本", "一级分类", "二级分类"]
}
```

> 凭据权限由飞书应用自带的权限范围（scopes）控制；如需按个人账号访问，可扫码登录自己的飞书。

## 5. 技能包结构

```text
skills/abap-cdc-gen/
├── SKILL.md                     ← 技能入口（AI 助手据此发现并加载）
├── README.md                    ← 本文件
├── build-skill.mjs              ← 构建脚本（仅开发者使用）
├── build/
│   └── bundle.json              ← 编译后的完整指令（编码规范、工作流、安全规则等）
├── feishu_config.json           ← 飞书配置模板（需自行填写 app_secret / base_token）
├── references/                  ← 源文件（仅开发者使用，构建时编译到 bundle.json）
│   ├── abap-coding.md
│   ├── abap-workflow.md
│   ├── abap-class.md
│   ├── abap-interface.md
│   ├── abap-batchinput.md
│   ├── api-catalog.md           ← 接口目录（SD1 系统参考，其他系统可替换）
│   ├── feishu-bitable.md
│   ├── rest-api.md
│   └── safety.md
└── scripts/
    ├── feishu_search.py         ← 飞书搜索脚本
    ├── feishu_sync.py           ← 飞书清单同步脚本
    ├── feishu_sync.bat          ← 同步脚本 bat 包装器
    ├── install_sync_task.ps1    ← 安装 Windows 定时同步任务
    └── rest_api_call.py         ← REST API 调用脚本
```

> **references/ 目录下的源文件仅用于构建，用户安装后不会看到这些文件的内容。**
> 所有编码规范、工作流、安全规则已编译到 `build/bundle.json` 中。

## 6. 日常使用

### 更新技能

```bash
git pull

# 如果 references/*.md 有变更，需要重新构建 bundle.json
node skills/abap-cdc-gen/build-skill.mjs

# 重新复制到全局技能目录
powershell -ExecutionPolicy Bypass -File install.ps1
```

> **注意**：如果只改了 `build-skill.mjs` 本身（构建脚本逻辑），不需要重新构建。如果改了 `references/*.md`（规范内容），**必须先构建再安装**，否则 AI 读到的还是旧的 `bundle.json`。

### 安装飞书清单定时同步（可选，Windows）

飞书多维表格「14.标准化清单_OP&PCE」是团队的开发对象注册中心。安装定时同步后，技能目录下会自动缓存一份 `feishu_checklist.md`，查询时无需每次联网。

```powershell
powershell -ExecutionPolicy Bypass -File ~/.claude/skills/abap-cdc-gen/scripts/install_sync_task.ps1
```

> 从安装后的技能目录执行（配置/缓存/定时同步都以**安装目录**为唯一来源）；Codex 用户把路径里的 `.claude` 换成 `.codex`。

安装后在 Windows 任务计划程序中创建 `ABAP_FeishuChecklistSync` 任务（工作日 9:17 / 14:17 后台运行），输出到技能目录的 `feishu_checklist.md`（已加入 `.gitignore`）。

**验证**：

```powershell
Get-ScheduledTask -TaskName "ABAP_FeishuChecklistSync"
Start-ScheduledTask -TaskName "ABAP_FeishuChecklistSync"   # 手动触发一次
```

### 常见问题

**Q: git pull 提示冲突怎么办？**

通常是你修改了本地文件。保留远程版本：

```bash
git stash
git pull
```

**Q: 飞书搜索不生效？**

1. 确认飞书应用凭据有效（`feishu_config.json` 随包提交，一般无需改动）；
2. 首次使用飞书功能时会自动弹出浏览器进行 OAuth 认证，按提示操作即可。

**Q: 如何更新团队共享的技能包？**

1. 修改 `skills/abap-cdc-gen/` 下对应文件（如 `references/*.md`）
2. **重新构建**：`node skills/abap-cdc-gen/build-skill.mjs`（重要！否则 bundle.json 是旧的）
3. `git add` + `git commit` + `git push`
4. 通知团队成员 `git pull` 后重跑 `install.ps1`
