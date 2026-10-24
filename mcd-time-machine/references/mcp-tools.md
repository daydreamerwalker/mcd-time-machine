# 麦当劳 MCP 工具速查（本 Skill 实际使用）

MCP Server：`https://mcp.mcd.cn`（Streamable HTTP，Header：`Authorization: Bearer <TOKEN>`）
本 Skill 只用**只读类**工具，绝不调用任何下单、支付、取消订单类写操作。

## 本 Skill 使用的工具

### order-list — 查询历史订单
- **用途**：年度报告、口味进化、特殊日期专题的**核心数据源**。
- **调用要点**：查询时间范围尽量覆盖 12 个月；分页拉取直到没有更多数据。
- **关键字段**（以实际返回为准）：订单号、下单/取餐时间、门店名称、就餐方式（外送/到店/得来速）、商品明细（名称/数量/价格）、实付金额、优惠金额。

### mall-order-list — 麦麦商城订单查询
- **用途**：补充积分兑换、周边购买记录（近一年）。
- **关键字段**：订单时间、商品名、支付积分、支付金额、订单状态。

### list-nutrition-foods — 餐品营养信息列表
- **用途**：为订单中的餐品匹配能量、蛋白质、脂肪、碳水化合物、钠，支撑营养摄入统计与口味进化图。
- **注意**：按餐品名称模糊匹配；匹配不到的营养项记 0 并在报告中注明「未匹配」。

### query-my-account — 我的积分查询
- **用途**：报告「积分章节」数据（可用/累计/即将过期积分）。

### query-my-coupons — 我的优惠券查询
- **用途**：省钱大师章节（已使用/可用券数与面额）。

### campaign-calendar — 活动日历查询工具
- **用途**：节假日专辑专题；把订单日期与活动日期关联，标注「活动期间下的单」。

### now-time-info — 获取当前时间信息
- **用途**：确定「年度」口径（报告年份）、判断当前月份，避免用训练数据猜日期。

### query-lottery-info / query-my-prizes — 抽奖活动与我的奖品
- **用途**：报告彩蛋章节（可选）：抽奖次数、奖品记录。

## 明确不使用的工具（写操作，仅提示用户）

`create-order`、`cancel-order`、`delivery-create-address`、`auto-bind-coupons`、`mall-create-order`、`draw-lottery`、`party-order-create` 等。本 Skill 是回忆录生成器，只读不写。

## 规范化数据契约（normalized.json）

Claude 调用 MCP 后，必须把原始返回整理成如下 JSON，再传给渲染脚本：

```json
{
  "meta": {
    "generated_at": "2026-10-24T12:00:00+08:00",
    "user_alias": "麦门信徒小吴",
    "data_source": "mcd-mcp",
    "year": 2026,
    "period": {"start": "2025-10-25", "end": "2026-10-24"}
  },
  "summary": {
    "total_orders": 128,
    "total_spend": 3865.5,
    "total_items": 342,
    "first_order_date": "2025-11-03",
    "late_night_orders": 31,
    "coupon_saved": 512.0,
    "points_earned": 1932,
    "points_available": 640,
    "stores_count": 17
  },
  "orders": [
    {
      "id": "MCD20251103...",
      "date": "2025-11-03",
      "time": "12:30",
      "type": "takeout",
      "store": "XX餐厅",
      "total": 45.0,
      "saved": 8.0,
      "items": [
        {"name": "巨无霸", "qty": 1, "price": 23.5, "category": "burger"}
      ]
    }
  ],
  "nutrition": {
    "calories": 186400, "protein": 5820, "fat": 6740, "carb": 16200, "sodium": 42800, "unit": "g/kcal/mg"
  },
  "campaigns": [
    {"date": "2026-01-01", "title": "新年活动", "status": "past"}
  ],
  "lottery": {"draw_count": 12, "prizes": 3}
}
```

字段缺失时的处理：数值型缺失填 0 并在文案中回避该指标；`orders` 为空时降级为「无真实数据」模式（见 SKILL.md 降级策略）。

## 限流与容错

- 每个 Token 限流 600 次/分钟；分页拉取时每次请求间隔 ≥1 秒。
- 401：Token 失效，提示用户去 open.mcd.cn 控制台重新激活。
- 429：等待 60 秒后重试当前页。
- 单工具连续失败 2 次：跳过该数据源，在报告末尾「数据说明」中注明缺失项，继续生成。
