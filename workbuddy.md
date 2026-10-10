# workbuddy.md — 麦麦营养搭配师 开发对话上下文（WorkBuddy 联动证明）

> 本文件用于证明本项目系**真实使用腾讯 WorkBuddy** 开发完成，作为 2026 麦当劳程序员创意开发大赛「WorkBuddy 联动专项奖励（3000 积分）」的提交材料。
> 内容为本次开发会话的真实过程记录（精简整理，非逐字全文）。

## 会话概览

- **开发工具**：WorkBuddy（AI 助手）+ 麦当劳中国 MCP（`mcd-mcp`，Streamable HTTP）
- **开发模式**：Agent 模式（直接读写文件、运行脚本、配置本机 MCP）
- **产出仓库**：`mcd-nutrition-coach`（麦当劳 MCP 营养搭配 Skill + Python 组合优化器）

## 开发过程（关键节点）

### 1. 读懂参赛规则
- 用户提供公众号文章链接，WorkBuddy 抓取并梳理出赛事要点：
  - 赛事：2026 麦当劳程序员创意开发大赛（WorkBuddy × 麦当劳）
  - 时间：2026-10-09 10:30 — 2026-10-25 23:59
  - 奖励：前 100 名提交 `workbuddy.md` 得 3000 积分；前 3 名得 10240 积分（无论是否用 WorkBuddy）
  - 规则以 GitHub `M-China/mcd-developer-innovation-challenge` 为准
- 用户问「积分是否必须绑定当前 WorkBuddy 手机号」，WorkBuddy 核实官方 `activityGuidelines.md` 后明确回答：**规则无此绑定要求**；积分通过麦当劳邮箱兑换码发放，同一 WorkBuddy 账号仅限兑 1 份。

### 2. 选定 Skill 方向
- WorkBuddy 先拉取 `M-China/mcd-mcp-server` 的真实 Tool 清单（点餐/营养/门店/券/活动/积分/抽奖等 35 个工具），基于**真实可用能力**给出 5 个差异化方向。
- 用户选定 **「麦麦营养搭配师」**（基于 `list-nutrition-foods` 营养数据做个性化餐品组合推荐）。

### 3. 接入真实 MCP 并纠偏
- 用户提供麦当劳 MCP Token 后，WorkBuddy 用 Python 实探端点 `https://mcp.mcd.cn`：
  - 验证 Token 有效，返回 `mcd-mcp v1.0.0`，共 35 个工具。
  - **关键发现**：`list-nutrition-foods` 实际**无参数**、返回约 **160 条餐品的包装文本**（含 `## Original Response` 内 JSON 表格），单位：能量 kJ/kcal、蛋白/脂肪/碳水 g、钠/钙 mg。这与最初按文档推断的「JSON 营养库」不同。
- WorkBuddy 据此**重写** `nutrition_coach.py`：内置解析包装文本 → 归一化 → 带剪枝组合搜索 → 评分排序；支持 `--live`（直连 MCP）/ `--mcp-raw`（喂返回原文，主路径）/ `--input`（离线归一化 JSON）三路输入。

### 4. 实测验证
- 离线（真实 160 条快照 `sample_nutrition.json`）：减脂 550kcal / 蛋白 40g → 552/556/558 kcal、蛋白 40g 达标组合（评分 ~83.8）。
- `--live` 实连 MCP：结果一致，端到端打通。
- 修复一处实时握手 bug（`notifications/initialized` 空 body 导致 `json.loads` 报错）。

### 5. 文档与配置校正
- 将 `SKILL.md` / `MCP_INTEGRATION.md` / `README.md` 全部校正到真实接口；把真实 Token 写入本机 `~/.workbuddy/mcp.json`（仅供本地连 MCP，**绝不进公开仓库**）；仓库内 `mcp-config.example.json` 使用 `${MCD_MCP_TOKEN}` 占位符。

### 6. 交付与本地化
- 生成全套参赛必须文件：`README.md` / `CONTEST_DECLARATION.md`（官方原版）/ `MCP_INTEGRATION.md` / `mcp-config.example.json` / `SKILL.md` / `nutrition_coach.py` / `sample_nutrition.json`。
- 将 Skill 安装至本机用户级目录 `~/.workbuddy/skills/mcd-nutrition-coach/`，用户可在 WorkBuddy 直接调用。
- 本地 `git init` + 提交（脱敏，真实 Token 不入库）。

## 使用的 WorkBuddy 能力
- WebFetch / WebSearch：抓取公众号与 GitHub 官方规则、MCP 工具清单
- 文件读写与编辑：生成并校正全部源码与文档
- Bash / PowerShell 执行：实探 MCP、跑优化器、git 提交、安装 Skill
- 任务管理：多步任务拆解为 tracked tasks

## 结论
本项目从规则解读、方向选型、MCP 实探纠偏、优化器开发、端到端验证到本地交付，**全程在 WorkBuddy 内完成**，符合赛事「真实使用 WorkBuddy 开发」的联动奖励要求。
