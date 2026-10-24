# MCP_INTEGRATION.md — 麦当劳 MCP 集成说明

## 1. 使用的 MCP Server

| 项 | 内容 |
|---|---|
| Server 名称 | `mcd-mcp`（麦当劳中国 MCP Server） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 认证 | `Authorization: Bearer <MCP_TOKEN>`（Token 由 open.mcd.cn 控制台申请） |
| 官方仓库 | https://github.com/M-China/mcd-mcp-server |
| 调用范围 | **仅只读工具**，不使用任何下单/支付/取消类写操作 |

## 2. 实际使用的 Tool 与调用流程

```
用户请求
   │
   ▼
① now-time-info ─────────── 确定当前日期与报告年份口径
   │
   ▼
② order-list ────────────── 分页拉取近 12 个月历史订单（核心数据源）
   │   └─ 429 时等待 60s 重试；401 时终止并提示重新激活 Token
   ▼
③ mall-order-list ───────── 补充麦麦商城积分兑换/周边订单
   │
   ▼
④ list-nutrition-foods ──── 为订单餐品匹配能量/蛋白质/脂肪/碳水/钠
   │
   ▼
⑤ query-my-account ──────── 可用/累计/即将过期积分
   │
   ▼
⑥ query-my-coupons ──────── 优惠券张数与面额（省钱统计）
   │
   ▼
⑦ campaign-calendar ─────── 当月活动日历（节假日专辑专题；订单与活动日期交叉）
   │
   ▼
⑧ 规范化整理 ────────────── 统一为 normalized.json（meta/summary/orders/nutrition/campaigns/lottery）
   │
   ▼
⑨ 渲染脚本（本地 Python，标准库）── 输出 4 类 HTML
   │
   ▼
⑩ present_files 交付
```

### 各 Tool 在业务场景中的分工

| Tool | 业务场景 | 产出指标 |
|---|---|---|
| `order-list` | 年度报告 / 口味进化 / 特殊日期 | 总订单、总花费、复购王、门店 Top3、月度分布、深夜订单、首单、品类分布、时间-of-day 分布 |
| `mall-order-list` | 年度报告「吃饭的方式」 | 商城订单数、积分兑换记录 |
| `list-nutrition-foods` | 口味进化「摄入物质变化」 | 月度热量/钠/蛋白质曲线、年度营养总览 |
| `query-my-account` | 年度报告「省钱大师」 | 可用积分、累计积分、即将过期积分 |
| `query-my-coupons` | 年度报告「省钱大师」 | 优惠券节省金额 |
| `campaign-calendar` | 特殊日期「节假日专辑」 | 活动日历与订单日期交叉标注 |
| `now-time-info` | 全局 | 报告年份、当前月份、相识天数 |
| `query-lottery-info` / `query-my-prizes` | 年度报告彩蛋（可选） | 抽奖次数、奖品数 |

**明确不调用**：`create-order`、`cancel-order`、`delivery-create-address`、`auto-bind-coupons`、`mall-create-order`、`draw-lottery`、`party-order-create`。回忆录生成器只读不写，从设计上杜绝误操作下单。

## 3. 调用细节与容错

- **分页**：`order-list` 按时间范围循环拉取，每次请求间隔 ≥1 秒，尊重 600 次/分钟限流。
- **错误码**：401（Token 失效）→ 引导用户去 open.mcd.cn 控制台重新激活后停止；429（限流）→ 等待 60s 重试当前页；单工具连续失败 2 次 → 跳过该数据源并在报告「数据说明」中注明，流程不中断。
- **数据缺失**：数值型缺失填 0 并在文案中回避该指标；`orders` 为空时降级为「首单预告」，不编造数据。
- **营养匹配**：`list-nutrition-foods` 返回按餐品名写入 item 级营养字段；匹配失败的由渲染器内置常见餐品营养兜底库近似，并在页面注明「未匹配/近似值」。

## 4. 业务价值

1. **数据再消费**：把沉睡在账户里的订单流水变成有情绪、可分享的个人年度叙事，提升用户与麦当劳 App/小程序的情感连接。
2. **场景延伸**：从「点餐工具」延伸出「回忆工具」——深夜食堂、首单纪念、节日专辑等场景天然适合社交传播，形成自传播闭环。
3. **安全示范**：全程只读，为「MCP + 个人消费数据」类创意提供了合规、最小权限的实现范式。
4. **创意可复制**：情感地图 + 数据契约 + 渲染器三段式架构，可复用到其他品牌/其他 MCP 的年度报告类场景。
