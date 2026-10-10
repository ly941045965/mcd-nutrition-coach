# 麦麦营养搭配师（McDonald's Nutrition Coach）

> 基于 **麦当劳中国 MCP** 营养数据，根据用户健身目标（减脂 / 增肌 / 维持）与热量、蛋白质预算，智能推荐麦当劳餐品组合，并输出可视化营养表。
>
> 本项目为「2026 麦当劳程序员创意开发大赛」参赛作品，由参赛者独立开发，非麦当劳官方产品。

## 它能帮你解决什么

「想吃麦当劳，又怕热量超标 / 蛋白质不够 / 钠爆表」——这是无数健身党和减脂期用户的真实痛点。
麦麦营养搭配师把麦当劳官方的餐品营养数据，变成**个性化、可执行的搭配方案**：

- 🥗 输入目标（减脂 / 增肌 / 维持），自动算出达标组合
- 💪 兼顾蛋白质摄入，增肌期也能放心吃麦麦
- 🧂 控制钠摄入，提示「钠爆表」风险
- 💰 （可选）一键算价，知道这顿花多少
- 📊 输出营养表，方便截图分享（利于传播 / 冲 Star）

## 功能亮点

| 能力 | 说明 | 底层 MCP 工具 |
|---|---|---|
| 营养数据获取 | 拉取麦当劳约 160 个餐品能量/蛋白/脂肪/碳水/钠/钙 | `list-nutrition-foods` |
| 组合优化 | 在营养库中搜索满足目标的最佳餐品组合 | `nutrition_coach.py`（本地算法） |
| 可售餐品对齐（可选） | 取当前门店可售餐品编码，确保推荐可点 | `query-meals` |
| 价格计算（可选） | 给推荐组合实时算价 | `calculate-price` |
| 时间感知（可选） | 结合当前时段给出建议（如早餐场景） | `now-time-info` |

## 安装

### 1. 配置麦当劳 MCP（前置条件）

在 WorkBuddy 左侧【专家·技能·连接器】→【连接器】→【自定义连接器】→【配置 MCP】，填入：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer ${MCD_MCP_TOKEN}"
      }
    }
  }
}
```

> Token 申请见 [麦当劳 MCP Server 指南](https://github.com/M-China/mcd-mcp-server)。**务必用环境变量占位符，切勿写入真实 Token。**

### 2. 安装本 Skill

将本仓库克隆 / 下载，在 WorkBuddy 中通过自定义 Skill 加载 `SKILL.md` 即可。

### 3. 本地优化器

- 实时（需 `MCD_TOKEN` 环境变量）：`python nutrition_coach.py --live --mode cut --target-cal 550 --target-protein 40`
- 离线演示（已内置真实 160 条快照）：`python nutrition_coach.py --input sample_nutrition.json --mode cut --target-cal 550 --target-protein 40`

## 使用方法（真实运行示例）

```
你：我减脂期，午饭想吃麦当劳，热量控制在 550 以内，蛋白尽量高，有推荐吗？
麦麦营养搭配师（nutrition_coach.py 输出）：

## 方案 1（评分 83.8）
| 餐品 | 热量(kcal) | 蛋白(g) | 脂肪(g) | 碳水(g) | 钠(mg) | 钙(mg) |
| 优品豆浆小杯 | 151 | 6 | 3 | 25 | 32 | 15 |
| 热奶铁大杯 | 249 | 14 | 11 | 22 | 134 | 431 |
| 蜜汁BBQ风味薄皮脆汁鸡-带骨里脊 | 152 | 20 | 5 | 6 | 635 | 28 |
| **合计** | **552** | **40** | **19** | **53** | **801** | **474** |
建议：蛋白达标✅
```

> 以上为 `list-nutrition-foods` 真实数据经优化器计算的结果（减脂 550kcal / 蛋白 40g 目标）。

## 目标用户

- 减脂 / 增肌 / 体重管理人群
- 关注「吃得开心又不超标」的普通消费者
- 想用麦当劳做健康餐搭配的营养爱好者

## 文件结构

```
mcd-nutrition-coach/
├── README.md                 # 项目介绍（必须）
├── CONTEST_DECLARATION.md    # 参赛声明（官方原版，不可改）
├── MCP_INTEGRATION.md        # MCP 接入说明（必须）
├── mcp-config.example.json   # 脱敏 MCP 配置示例（必须）
├── SKILL.md                  # WorkBuddy Skill 定义（核心源码/工作流）
├── nutrition_coach.py        # 餐品组合优化器（可运行源码）
├── sample_nutrition.json     # 真实营养数据快照（160 条，离线演示用）
└── workbuddy.md              # 用 WorkBuddy 开发时导出（申报 WorkBuddy 专项奖时提交）
```

## 免责声明

本项目输出仅供参考，**不构成医疗、营养或其他专业建议**。餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。
