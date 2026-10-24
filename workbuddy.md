# workbuddy.md — 使用 WorkBuddy 开发本项目的对话上下文导出

> 本文件用于麦当劳程序员节创意开发大赛「WorkBuddy 专项奖励」核验，记录本项目使用 WorkBuddy 的开发过程。

## 一、用户原始需求（2026-10-24）

> @scene#57:"开发 Skill" https://github.com/M-China/mcd-developer-innovation-challenge 搜索并阅读这个网页，我目前已经配置好了MCP，现在想要根据其内容开发一个skills，它的功能有：
> 1、能够通过用户的情感选择，让AI写出对应的文案，并且在相应的卡片上生成。
> 2、生成年度麦麦报告生成器，类似于"网易云年度报告"的消费回忆录。
> 3、生成有趣的口味进化图和消费习惯，摄入物质的变化。
> 4、最后是特殊日期回忆专题，特殊日期有节假日专辑，深夜食堂，一切的开始，以及用户自定义的日子，文案可以通过AI生成，也可以通过用户选择情感选择生成。
> 最终文件在F盘生成

## 二、WorkBuddy 开发过程

1. **网页调研**：WorkBuddy 抓取并解读了大赛主仓库 `mcd-developer-innovation-challenge` 与 MCP 官方仓库 `mcd-mcp-server`，提取出：MCP 接入地址 `https://mcp.mcd.cn`（Streamable HTTP + Bearer Token）、30+ 工具清单（重点锁定 `order-list`、`mall-order-list`、`list-nutrition-foods`、`query-my-account`、`query-my-coupons`、`campaign-calendar`、`now-time-info` 等只读工具）、以及参赛项目必备文件清单（README.md / CONTEST_DECLARATION.md / MCP_INTEGRATION.md / 源代码 / workbuddy.md）。

2. **架构设计**：确定「情感地图 + 数据契约 + 渲染器」三段式架构——
   - MCP 只读数据 → 规范化为 `normalized.json`
   - 文案由 Claude 按情感地图生成（或用户情感选择驱动）
   - 四个 Python 渲染器（仅标准库）产出自包含 HTML

3. **Skill 初始化**：调用 skill-creator 的 `init_skill.py` 在 `F:/mcd-time-machine/mcd-time-machine` 生成标准 Skill 骨架（SKILL.md + scripts/ + references/ + assets/）。

4. **参考文档**：编写 `references/emotion-map.md`（10 种情感的文案风格/配色/emoji）、`references/report-playbook.md`（指标口径、10 屏章节结构、口味人格判定、金句写法）、`references/mcp-tools.md`（工具速查、数据契约、限流容错）。

5. **渲染脚本**：编写 `scripts/common.py`（共享调色板、SVG 折线/环形/堆叠图、聚合函数、营养兜底库）与四个渲染器：`render_mood_cards.py`、`render_annual_report.py`、`render_taste_evolution.py`、`render_special_dates.py`。

6. **主入口**：编写 `SKILL.md`（触发条件、四步工作流、降级策略、合规红线）。

7. **演示验证**：编写 `assets/sample_data.json`（61 笔订单的模拟年度数据，含汇总与营养指标，由脚本自动计算保证自洽），运行全部渲染器生成 `demo/` 下四个演示 HTML，并修复了「最晚深夜订单」按深夜时刻（02:47 优先于 23:50）排序的问题。

8. **参赛文档与打包**：编写 README.md、MCP_INTEGRATION.md，按官方要求原文复制 CONTEST_DECLARATION.md，导出本文件，并用 `package_skill.py` 校验打包。

## 三、开发环境

- WorkBuddy（Windows，bash shell）
- Python 3.13（标准库，无第三方依赖）
- 麦当劳 MCP：用户已完成配置（Token 由用户在 open.mcd.cn 控制台申请，未在项目任何文件中出现）

## 四、项目产出

- Skill 源码：`mcd-time-machine/`（SKILL.md + 3  references + 5 scripts + 3 assets）
- 演示输出：`demo/01-mood-cards.html`、`demo/02-annual-report.html`、`demo/03-taste-evolution.html`、`demo/04-special-dates.html`
- 参赛文档：README.md、CONTEST_DECLARATION.md、MCP_INTEGRATION.md、workbuddy.md

---

## 五、第二轮迭代（2026-10-24 下午，用户反馈驱动）

用户反馈两条：① 地名/姓名改为「XXX」占位，等调用者自己输入；② 渲染画面「太 AI 化」，要求麦当劳元素尽可能铺满，背景加入像素人物图与实物图。

WorkBuddy 执行：

1. **匿名化**：`assets/sample_data.json` 中 58 处门店名改为 `XXX餐厅(N号店)`、用户名改为 `XXX`；文案示例 JSON 同步替换；SKILL.md 新增「询问用户昵称、严禁编造人名地名」规范。
2. **素材生产**（ImageGen，约 50–100 积分，已向用户告知）：
   - 4 张 8-bit 像素人物（汉堡/薯条/可乐/小丑精灵，透明背景 PNG）
   - 6 张实物照片（巨无霸/薯条/可乐/圣代/麦乐鸡/门店，商业摄影风 JPEG）
   - Press Start 2P 像素字体（Google Fonts latin 子集 woff2，12.5KB）
   - `tools/prepare_assets.py`：镜像覆盖去右下角水印 → floodfill 抠透明背景 → FASTOCTREE 量化压缩（精灵图 593KB→40KB）
3. **视觉系统重建**：新增 `scripts/pixel_art.py`（金拱门 SVG、像素餐品图标、雨棚条纹、棋盘格、条码、彩带、月亮、邮戳、背景装饰层）；重写 `common.py` 设计令牌（红黄/硬阴影贴纸风/去玻璃拟态/图片 data-uri 加载）。
4. **四页重做**：年度报告=深色暖底+奶油托盘纸卡+拍立得照片+像素游行封面；心情卡片=收藏卡+探头精灵；口味进化=托盘纸+像素进化时间线；特殊日期=门票小票+邮戳+条码。
5. **验证**：Edge 无头浏览器逐页截图检视，全部通过；重新打包 zip 并更新安装版 Skill。
