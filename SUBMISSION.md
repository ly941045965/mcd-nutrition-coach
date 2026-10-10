# 参赛报名 · Issue 提交模板（2026 麦当劳程序员创意开发大赛）

> 使用说明：把本文件内容复制到你 GitHub 仓库 Issue 的提交框（按 `M-China/mcd-developer-innovation-challenge` 的 Issue 模板）。
> 推完公开仓库后，将下方 `{{REPO_URL}}` 替换为你的仓库真实地址即可发布。

---

## 项目名称
**麦麦营养搭配师（MCD Nutrition Coach）**

## 仓库地址
{{REPO_URL}}
（公开仓库，建议命名 `mcd-nutrition-coach`）

## 一句话简介
基于麦当劳中国 MCP 真实营养数据，按用户减脂 / 增肌 / 维持目标与热量、蛋白质预算，智能推荐达标餐品组合并输出可视化营养表。

## 创意亮点
- **真实数据驱动**：直接调用麦当劳官方 `list-nutrition-foods`，非编造热量。
- **组合优化器**：在热量窗口内枚举餐品组合，按「热量贴合 + 蛋白达标 + 控钠」评分排序，输出 Top-K 方案。
- **零资金风险**：全程只读 MCP 工具，不下单 / 不领券 / 不抽奖，公开演示安全。
- **即开即用**：内置真实 160 条营养快照，免 Token 也能离线演示；支持 `--live` 直连实时数据。

## 使用的麦当劳 MCP 工具
| 工具 | 用途 |
|---|---|
| `list-nutrition-foods` | 拉取全部餐品营养数据（核心输入，无参数） |
| `query-meals` | （增强）按门店取可售餐品，过滤推荐组合 |
| `calculate-price` | （增强）对最终组合算价 |
| `now-time-info` | （可选）获知当前时段 |

## 技术实现
- **Skill 层**：`SKILL.md` 定义 WorkBuddy 工作流（收集目标 → 拉营养数据 → 交优化器 → 输出营养表）。
- **优化器层**：`nutrition_coach.py`（纯 Python 标准库，无需第三方依赖）解析 MCP 包装文本 → 归一化 → 带剪枝组合搜索 → 评分排序。
- **演示数据**：`sample_nutrition.json` 为真实 160 条营养快照。

## 效果示例（减脂 550kcal / 蛋白 40g）
| 餐品 | 热量(kcal) | 蛋白(g) | 脂肪(g) | 碳水(g) | 钠(mg) | 钙(mg) |
|---|---|---|---|---|---|---|
| 优品豆浆小杯 | 151 | 6 | 3 | 25 | 32 | 15 |
| 热奶铁大杯 | 249 | 14 | 11 | 22 | 134 | 431 |
| 蜜汁BBQ风味薄皮脆汁鸡-带骨里脊 | 152 | 20 | 5 | 6 | 635 | 28 |
| **合计** | **552** | **40** | **19** | **53** | **801** | **474** |

> 结论：蛋白达标✅，钠在安全线内，放心吃。输出仅供参考，不构成医疗/营养专业建议。

## 已提交材料
- [x] `README.md` — 项目介绍 / 安装 / 用法
- [x] `CONTEST_DECLARATION.md` — 官方参赛声明（原版未改）
- [x] `MCP_INTEGRATION.md` — MCP 接入说明与业务价值
- [x] `mcp-config.example.json` — 脱敏配置（`${MCD_MCP_TOKEN}` 占位符）
- [x] `SKILL.md` / `nutrition_coach.py` / `sample_nutrition.json` — 源码与演示数据
- [x] `workbuddy.md` — **WorkBuddy 开发对话上下文（联动专项奖励证明）**

## 作者信息
- GitHub：{{YOUR_GITHUB_ID}}
- 邮箱：{{YOUR_EMAIL}}
- WorkBuddy 账号：与开发本项目的账号一致（用于兑换 3000 积分联动奖励）

## 声明
本人确认已阅读并遵守《参赛声明 CONTEST_DECLARATION.md》，所提交作品为原创，且仅调用麦当劳 MCP 的只读能力，未产生任何真实下单 / 扣费。
