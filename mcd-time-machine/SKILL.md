---
name: mcd-time-machine
description: 麦当劳消费回忆录生成器（麦麦时光机）。当用户想要生成麦麦年度报告、麦当劳年度报告、类似网易云年度报告的消费回忆录、情感语录卡片、口味进化图、消费习惯分析、摄入物质变化统计，或特殊日期回忆专题（节假日专辑、深夜食堂、一切的开始、自定义纪念日）时使用本 Skill。通过麦当劳 MCP（mcd-mcp）读取真实订单、营养、积分与活动数据，生成可分享的精美 HTML。仅使用只读工具，绝不创建订单。
---

# 麦麦时光机（MCD Time Machine）

## Overview

把用户的麦当劳消费数据变成有温度的回忆：四大能力——**情感语录卡片**（选一种心情，AI 写文案并渲染成分享卡片）、**年度麦麦报告**（滚动叙事页）、**口味进化图**（品类人格进化 + 摄入物质变化曲线 + 新欢旧爱 + 消费习惯画像）、**特殊日期回忆专题**（节假日专辑 / 深夜食堂 / 一切的开始 / 用户自定义纪念日，文案支持 AI 生成或用户情感选择驱动）。

数据流：麦当劳 MCP 只读工具 → 整理为规范化 JSON → `scripts/` 渲染器产出自包含 HTML → `present_files` 交付。

视觉规范（`scripts/pixel_art.py` + `scripts/common.py`）：麦当劳经典红黄、雨棚条纹、棋盘格、硬阴影贴纸卡、8-bit 像素人物（汉堡/薯条/可乐/小丑精灵）、金拱门背景水印、拍立得实物照片、门票小票 + 邮戳 + 条码、Press Start 2P 像素字体数字。全部素材原创生成，base64 内联，单文件离线可分享。

## 前置条件

1. 麦当劳 MCP 已配置并启用（`https://mcp.mcd.cn`，Streamable HTTP，`Authorization: Bearer <TOKEN>`）。若本会话没有 `mcd-mcp` 相关工具，先引导用户在连接器菜单启用，或按「降级策略」用演示数据出图。
2. Python 3.8+（仅标准库，无需安装第三方包）。
3. 输出目录：优先用户指定目录（例如 `F:/mcd-time-machine/demo/`）；未指定时用当前工作目录下 `mcd-output/`。

## 工作流（四步）

### 第 1 步：确认需求与口径

- 确认用户要哪个能力：心情卡片 / 年度报告 / 口味进化 / 特殊日期专题（可多选，也可全都要）。
- 确认时间范围：默认「近 12 个月」；年度报告默认当前自然年（用 `now-time-info` 取当前日期，不要用训练数据猜）。
- **询问用户昵称**（报告封面与页脚的称呼）：用户提供则用真名/昵称；不提供则用「麦门信徒」等通用称呼，**严禁编造具体人名或地名**；门店名一律原样使用 MCP 返回的真实门店名。
- 确认情感（仅卡片与特殊日期专题）：给出 10 个选项——治愈 / 开心 / emo / 孤独 / 热血 / 摆烂 / 甜蜜 / 怀旧 / 感恩 / 叛逆，或让用户描述心情由 Claude 匹配。
- 特殊日期专题还需确认：包含哪些主题（默认全部）、自定义纪念日的具体日期。

### 第 2 步：获取数据并规范化

调用只读工具（详细用法见 `references/mcp-tools.md`）：

| 用途 | 工具 |
|---|---|
| 历史订单（核心） | `order-list`（分页拉满 12 个月，请求间隔 ≥1s） |
| 商城订单 | `mall-order-list` |
| 营养匹配 | `list-nutrition-foods` |
| 积分 | `query-my-account` |
| 优惠券 | `query-my-coupons` |
| 活动日历 | `campaign-calendar` |
| 当前时间 | `now-time-info` |

把结果整理成 `references/mcp-tools.md` 定义的 **normalized.json**（含 `meta / summary / orders / nutrition / campaigns / lottery`），写入 `mcd-output/normalized.json`。要点：

- 每笔订单：`date, time, type, store, total, saved, items[{name,qty,price,category}]`。
- 餐品营养：优先用 `list-nutrition-foods` 的返回值写入 item 级字段；匹配失败的留给渲染器的内置兜底库。
- 单工具连续失败 2 次即跳过该数据源，继续生成，并在报告末尾注明缺失项。
- 429 等待 60s 重试；401 提示用户重新激活 Token 并停止，不要反复重试。

### 第 3 步：生成文案

- **用户选了情感**：按 `references/emotion-map.md` 中该情感的「风格 + 配色 + emoji」写文案。原则：必须引用真实数据（餐品名、门店、时间、金额、次数）；主文案 20–60 字，副文案 8–16 字；每条数据点作为 notes 注脚。文案写入一个 cards JSON（`[{"topic"/"emotion","main","sub","notes":[...]}]`），`topic` 取 `first / late-night / holiday / custom`，心情卡片用 `emotion` 字段。
- **用户选 AI 自由生成**：先统计数据亮点（深夜单数、复购王、首单、省钱额），再匹配最贴近的情感风格产出同样结构的文案。
- 文案示例见 `assets/sample_cards.json` 与 `assets/sample_topics.json`。

### 第 4 步：渲染并交付

```bash
# ① 情感语录卡片（--cards 省略则走模板兜底）
python scripts/render_mood_cards.py --data mcd-output/normalized.json \
    --out mcd-output/mood-cards.html --title "麦麦心情卡片" --cards mcd-output/cards.json

# ② 年度麦麦报告
python scripts/render_annual_report.py --data mcd-output/normalized.json \
    --out mcd-output/annual-report.html --title "2026 年度麦麦报告"

# ③ 口味进化图 / 消费习惯 / 摄入物质变化
python scripts/render_taste_evolution.py --data mcd-output/normalized.json \
    --out mcd-output/taste-evolution.html --title "我的口味进化史"

# ④ 特殊日期回忆专题
python scripts/render_special_dates.py --data mcd-output/normalized.json \
    --out mcd-output/special-dates.html --date 2026-05-20 \
    --topics "first,late-night,holiday,custom" --cards mcd-output/topics.json
```

年度报告的指标口径、章节顺序与金句写法遵循 `references/report-playbook.md`。渲染完成后用 `present_files` 交付全部 HTML，并在回复中给出数据亮点摘要（总订单、总花费、深夜单数、口味人格）。

## 降级策略

- **MCP 不可用 / 无 Token**：使用 `assets/sample_data.json` 跑通全流程出演示图，明确告知用户「当前为演示数据，接入 MCP 后即可生成真实回忆」。
- **订单为空**：报告降级为「首单预告」文案，不编造任何数据。
- **营养未匹配**：自动跳过摄入物质曲线，仅在文案中说明。
- **图片/字体缺失**：像素精灵、拍立得照片、像素字体按缺失处理——页面自动去掉对应装饰（背景金拱门纹理与 SVG 图案仍在），不报错、不留空白占位。
- **某主题无数据**（如无深夜订单、自定义日期无订单）：照常输出该章节，用「没有也是一种答案」的温和文案填充，不留空白。

## 合规红线（必须遵守）

1. 只调用只读工具；**绝不**调用 `create-order / cancel-order / draw-lottery / mall-create-order / auto-bind-coupons / delivery-create-address / party-order-create` 等任何写操作。
2. 不记录、不回显、不写入用户的 MCP Token。
3. 营养数据只陈述事实，不做健康/医疗建议（见 CONTEST_DECLARATION 使用提示）。
4. 输出为个人回忆用途，注明「非麦当劳官方产品，餐品信息以官方渠道为准」。
5. 项目为麦当劳程序员节创意开发大赛参赛作品，原创开发，不暗示官方背书。

## Resources

- `references/mcp-tools.md` — MCP 工具用法、normalized.json 契约、限流容错。**第 2 步必读。**
- `references/emotion-map.md` — 10 种情感的文案风格、配色、emoji 与生成流程。**写文案前必读。**
- `references/report-playbook.md` — 年度报告指标定义、品类映射、口味人格判定、金句写法。**做年度报告前必读。**
- `scripts/common.py` — 共享模块（品牌设计令牌、像素字体内联、图片 data-uri 加载、SVG 图表、聚合函数、营养兜底库）；被四个渲染器导入，不要单独执行。
- `scripts/pixel_art.py` — 纯 SVG 麦当劳素材库（金拱门、像素餐品图标、雨棚条纹、棋盘格、条码、彩带、月亮、邮戳、背景装饰层）。
- `scripts/render_mood_cards.py` — 情感语录卡片渲染器。
- `scripts/render_annual_report.py` — 年度麦麦报告渲染器。
- `scripts/render_taste_evolution.py` — 口味进化 / 摄入物质 / 消费习惯渲染器。
- `scripts/render_special_dates.py` — 特殊日期回忆专题渲染器。
- `assets/images/` — 10 张原创素材（4 张 8-bit 像素人物 PNG + 6 张实物美食/门店 JPEG），渲染时以 base64 内联进 HTML；**文件缺失时装饰自动降级，不影响生成**。
- `assets/fonts/PressStart2P-latin.woff2` — 像素字体（latin 子集，base64 内联，离线可用）；缺失时数字回退等宽字体。
- `assets/sample_data.json` — 一年期演示数据（61 单，地名与人名均为 XXX 占位，含汇总与营养指标）。
- `assets/sample_cards.json` / `assets/sample_topics.json` — 文案 JSON 示例（Claude 生成文案时对齐此结构）。
