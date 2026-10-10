# MCP 接入说明（MCP_INTEGRATION.md）

本文件说明「麦麦营养搭配师」实际使用的麦当劳 MCP Server、Tool、调用流程与业务价值，用于赛事资格核验。

## 1. 使用的 MCP Server

- **名称**：麦当劳中国 MCP Server（McDonald's China MCP Server）
- **官方接入地址**：`https://mcp.mcd.cn`
- **传输协议**：Streamable HTTP
- **鉴权方式**：请求头 `Authorization: Bearer <MCP_TOKEN>`（Token 通过 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 申请）
- **使用指南**：https://github.com/M-China/mcd-mcp-server
- **速率限制**：每 Token 每分钟最多 600 次请求（超出返回 429）

## 2. 实际使用的 Tool 清单

| Tool 名称 | 入参 | 用途 | 本项目中的调用场景 |
|---|---|---|---|
| `list-nutrition-foods` | 无 | 获取麦当劳约 160 个餐品的营养成分（能量kJ/kcal、蛋白、脂肪、碳水、钠、钙） | **核心数据源**：拉取营养库供组合优化 |
| `query-meals` | `storeCode`/`orderType`/`beType`（可选 `beCode`/`reservationDate`） | 查询当前门店可售卖餐品列表 | （可选）对齐「可售餐品」，确保推荐组合在门店真实可点 |
| `calculate-price` | `storeCode`/`orderType`/`beType`/`items`（可选 `needTableware` 等） | 按商品列表（可含优惠券）计算金额、配送费、优惠及应付总价 | （可选）给推荐组合实时算价 |
| `now-time-info` | 无 | 返回当前完整时间信息 | （可选）结合时段给出场景建议（如早餐 / 下午茶） |

> 本项目**核心链路仅使用只读类 Tool `list-nutrition-foods`**，不涉及下单、领券、抽奖等写操作，公开演示零资金风险。`query-meals` / `calculate-price` / `now-time-info` 作为可选增强项。

## 3. 调用流程

```
[用户输入] 目标(减脂/增肌/维持) + 热量/蛋白预算 + 忌口 + 门店(可选)
    │
    ▼
[Step 1] 确认 mcd-mcp 连接器已启用（配置见 mcp-config.example.json）
    │
    ▼
[Step 2] 调用 list-nutrition-foods（无参数） → 得到「包装文本」原始返回
    │        （文本内含 data 字符串表格：[160]{productName,...calcium}: 每行一条）
    │
    ▼
[Step 3] 将返回文本保存为 mcp_raw_nutrition.txt，运行本地优化器：
         python nutrition_coach.py --mcp-raw mcp_raw_nutrition.txt \
           --mode <cut|bulk|maintain> --target-cal <kcal> --target-protein <g> \
           --exclude <忌口> --max-items 3 --top-k 3 --out report.md
    │        （nutrition_coach.py 内置：解析包装文本 → 归一化 → 组合搜索 → 评分排序）
    │
    ▼
[Step 4] (可选) 调用 query-meals / calculate-price（需门店上下文）→ 对齐可售 + 算价
    │
    ▼
[输出] 营养表 + 推荐组合 + (价格) + 免责声明
```

> 开发者自检也可 `python nutrition_coach.py --live --mode cut --target-cal 550 --target-protein 40`（脚本用环境变量 `MCD_TOKEN` 直连 MCP）；离线演示用 `--input sample_nutrition.json`（已内置 160 条真实快照）。

## 4. 业务价值

- **把「营养数据」变成「可执行建议」**：用户不再需要自己查热量、手算配比，降低健康饮食的决策成本。
- **真实串起 MCP 能力**：营养查询（只读）→ 本地组合优化 → （可选）可售对齐 + 价格计算，形成完整闭环。
- **安全可传播**：核心链路纯只读，演示无需真实下单，适合公开分享与 GitHub Star 传播。
- **贴合赛事主题**：呼应「身材管控期也想吃麦当劳」这一高频真实场景，兼顾创意与实用价值。
