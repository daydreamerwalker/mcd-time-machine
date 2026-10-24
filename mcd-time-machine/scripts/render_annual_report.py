# -*- coding: utf-8 -*-
"""年度麦麦报告渲染器（麦当劳收藏卡 + 拍立得 + 像素游行风格）。
用法:
  python render_annual_report.py --data normalized.json --out report.html \
      [--title "2026 年度麦麦报告"] [--year 2026]
指标口径与章节结构见 references/report-playbook.md。
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (BRAND_RED, BRAND_YELLOW, CATEGORY_COLORS, CATEGORY_EMOJI,
                    CATEGORY_NAMES, DARK_CHART_THEME, PHOTO_FOR, all_orders,
                    categorize, category_counts, esc, fmt_int, fmt_money,
                    fmt_wan, footer_note, html_bars, is_late_night, item_counts,
                    load_data, latest_late_night, month_key, month_label,
                    monthly_series, nice_ceil, page_shell, personality,
                    photo_card, sprite_tag, store_counts, svg_donut,
                    svg_line_chart)
from pixel_art import (arches_svg, awning_css, bg_decor, barcode_css,
                       checker_css, confetti_svg, love_it_banner, moon_svg,
                       pixel_divider_svg, pixel_icon, sprite_parade)

REPORT_CSS = """
body{background:linear-gradient(180deg,#1A0B06 0%,#2B1408 40%,#1A0B06 100%);
color:#FFF6E0;min-height:100vh}
.wrap{max-width:780px;padding-bottom:40px}
.top-strip{position:relative;z-index:1}
/* ---- 封面 ---- */
.cover{min-height:94vh;display:flex;flex-direction:column;justify-content:center;
align-items:center;text-align:center;padding:40px 0;position:relative}
.cover .year{font-family:'Press Start 2P',monospace;font-size:15px;letter-spacing:.3em;
color:var(--yellow);text-shadow:3px 3px 0 var(--ink);margin:20px 0 6px}
.cover h1{font-size:42px;font-weight:900;line-height:1.4;color:#FFF6E0;
text-shadow:4px 4px 0 var(--red),8px 8px 0 var(--ink)}
.cover h1 em{font-style:normal;color:var(--yellow);
text-shadow:4px 4px 0 var(--red),8px 8px 0 var(--ink)}
.cover .who{font-size:15px;color:#E8D5B5;margin-top:18px;font-weight:700;
background:rgba(255,246,224,.08);border:2px solid rgba(255,246,224,.25);
padding:8px 16px;border-radius:99px}
.cover .cover-quote{margin-top:30px;font-size:17px;line-height:2.1;color:#FFE9C4;
max-width:26em;font-weight:600}
.cover .parade{margin-top:44px}
.cover .parade-item{height:96px}
.cover .scroll-hint{margin-top:36px;font-size:11px;color:#C9A96A;letter-spacing:.35em;
font-family:'Press Start 2P',monospace;animation:bob 2.2s ease-in-out infinite}
.cover .loveit{position:absolute;top:26px;right:0}
/* ---- 章节（奶油托盘纸卡） ---- */
.chapter{min-height:92vh;display:flex;flex-direction:column;justify-content:center;
padding:40px 0}
.tray{background:var(--cream);color:var(--ink);border:4px solid var(--ink);
border-radius:18px;padding:28px 26px;box-shadow:10px 10px 0 var(--ink);
position:relative;overflow:hidden}
.tray::before{content:"";position:absolute;left:0;right:0;top:0;height:10px;
background:repeating-linear-gradient(45deg,var(--red) 0 14px,var(--yellow) 14px 28px);
border-bottom:4px solid var(--ink)}
.tray{padding-top:38px}
.tray .ch-head{display:flex;align-items:flex-start;gap:14px;margin-bottom:6px}
.tray .ch-head .px-icon{width:46px;margin-top:2px}
.tray .ch-sub{color:#7A5A36}
.stat-row .stat{background:#fff}
.bubble{position:relative;background:#fff;border:3px solid var(--ink);border-radius:18px;
padding:22px 24px;box-shadow:6px 6px 0 var(--ink);margin:16px 0}
.bubble::after{content:"";position:absolute;left:44px;bottom:-24px;width:22px;height:22px;
background:#fff;border-right:3px solid var(--ink);border-bottom:3px solid var(--ink);
transform:rotate(45deg)}
.bubble .q{font-size:20px;font-weight:900;line-height:1.8}
.bubble .from{font-size:12.5px;color:#8A6A3B;margin-top:12px;font-weight:800}
.photo-flex{display:flex;gap:22px;align-items:center;flex-wrap:wrap;margin:14px 0}
.photo-flex .polaroid{flex:1;min-width:220px;max-width:300px}
.photo-flex .polaroid .photo{width:100%}
.moon-box{position:absolute;right:18px;top:16px;width:74px;opacity:.9}
.stamp{position:absolute;right:20px;bottom:18px}
.end{min-height:80vh;display:flex;flex-direction:column;justify-content:center;
align-items:center;text-align:center;position:relative}
.end .see{font-family:'Press Start 2P',monospace;font-size:20px;color:var(--yellow);
text-shadow:3px 3px 0 var(--ink);line-height:2}
.end .see-cn{font-size:32px;font-weight:900;margin-top:16px;color:#FFF6E0;
text-shadow:3px 3px 0 var(--red),6px 6px 0 var(--ink)}
.end .cover-quote{margin-top:22px;font-size:16px;color:#FFE9C4;line-height:2.1}
.end .parade{margin-top:36px}
.end .parade-item{height:84px}
"""


def svg_combo(spend, orders, labels):
    """左轴消费金额折线 + 右轴订单数柱状（像素风：柱带描边）。"""
    if not labels:
        return ""
    ymax = nice_ceil(max(spend) * 1.15) if spend else 1.0
    omax = nice_ceil(max(orders) * 1.2) if orders else 1.0
    w, h = 720, 280
    pl, pr, pt, pb = 54, 50, 30, 36
    iw, ih = w - pl - pr, h - pt - pb
    n = len(labels)
    bw = iw / max(n, 1) * 0.52
    parts = [f'<svg viewBox="0 0 {w} {h}" class="chart" xmlns="http://www.w3.org/2000/svg">']
    for k in range(6):
        yy = pt + ih - ih * k / 5
        parts.append(f'<line x1="{pl}" y1="{yy:.1f}" x2="{w-pr}" y2="{yy:.1f}" '
                     f'stroke="rgba(120,90,60,.20)" stroke-width="1"/>')
        parts.append(f'<text x="{pl-8}" y="{yy+4:.1f}" text-anchor="end" class="axis-label" '
                     f'fill="#A08C6D" font-size="11">¥{fmt_wan(ymax*k/5)}</text>')
        parts.append(f'<text x="{w-pr+8}" y="{yy+4:.1f}" class="axis-label" fill="#A08C6D" '
                     f'font-size="11">{fmt_int(omax*k/5)}单</text>')
    for i, lab in enumerate(labels):
        if n <= 9 or i % max(1, n // 9) == 0:
            parts.append(f'<text x="{pl+iw*(i+.5)/n:.1f}" y="{h-10}" text-anchor="middle" '
                         f'class="axis-label" fill="#A08C6D" font-size="11">{esc(lab)}</text>')
    for i, v in enumerate(orders):
        bh = (v / omax) * ih if omax else 0
        x = pl + iw * (i + .5) / n - bw / 2
        parts.append(f'<rect x="{x:.1f}" y="{pt+ih-bh:.1f}" width="{bw:.1f}" '
                     f'height="{bh:.1f}" fill="#FFC72C" stroke="#2B1408" '
                     f'stroke-width="2" rx="3"/>')
    pts = " ".join(f"{pl+iw*(i+.5)/n:.1f},{pt+ih-(v/ymax)*ih:.1f}"
                   for i, v in enumerate(spend))
    parts.append(f'<polyline points="{pts}" fill="none" stroke="{BRAND_RED}" '
                 f'stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, v in enumerate(spend):
        parts.append(f'<rect x="{pl+iw*(i+.5)/n-3.4:.1f}" y="{pt+ih-(v/ymax)*ih-3.4:.1f}" '
                     f'width="6.8" height="6.8" fill="{BRAND_RED}" stroke="#FFF6E0" '
                     f'stroke-width="1.4"/>')
    parts.append("</svg>")
    return "".join(parts)


def rank_rows(rows, unit=""):
    out = []
    for i, r in enumerate(rows):
        out.append(f"""
<div class="rank-row">
  <div class="rank-no">{i+1}</div>
  <div class="rank-body">
    <div class="rank-name">{esc(r['label'])}</div>
    <div class="rank-meta">{esc(r.get('meta', ''))}</div>
  </div>
  <div class="rank-num">{esc(str(r.get('display', r.get('value', ''))))}{esc(unit)}</div>
</div>""")
    return "".join(out)


def tray(inner, icon_cat="other", no="", title="", sub=""):
    icon = pixel_icon(icon_cat)
    return f"""
<div class="tray reveal">
  <div class="ch-head">{icon}
    <div style="flex:1">
      {f'<div class="ch-no">{esc(no)}</div>' if no else ''}
      <div class="ch-title" style="font-size:26px;text-shadow:2px 2px 0 var(--yellow)">
        {title}</div>
      {f'<div class="ch-sub" style="margin-bottom:6px">{sub}</div>' if sub else ''}
    </div>
  </div>
  {inner}
</div>"""


def build(data: dict, title: str) -> str:
    meta = data.get("meta") or {}
    summary = data.get("summary") or {}
    orders = all_orders(data)
    year = meta.get("year") or title[:4]
    alias = meta.get("user_alias", "XXX")

    items = item_counts(data)
    stores = store_counts(data)
    cats = category_counts(data)
    late = [o for o in orders if is_late_night(o)]
    labels, spend_s, order_s = monthly_series(data)
    nutri = data.get("nutrition") or {}
    acct = data.get("account") or summary

    top_items = items.most_common(3)
    top_stores = stores.most_common(3)
    top_item = top_items[0][0] if top_items else "麦乐鸡"
    top_item_cat = categorize(top_item)
    first = min(orders, key=lambda o: o.get("date", "9999")) if orders else None
    latest_late = latest_late_night(orders)
    peak_month = labels[spend_s.index(max(spend_s))] if (labels and spend_s) else ""
    perso = personality(summary, cats, len(late),
                        float(summary.get("coupon_saved", 0) or 0),
                        cats.get("breakfast", 0))

    item_rows = [{"label": n, "value": c, "meta": f"今年吃了 {c} 份",
                  "display": f"{c} 份"} for n, c in top_items]
    store_rows = [{"label": s, "value": c, "meta": f"到店/下单 {c} 次",
                   "display": f"{c} 次"} for s, c in top_stores]

    cat_items = [{"label": CATEGORY_NAMES.get(k, k), "value": v,
                  "color": CATEGORY_COLORS.get(k, "#8D99AE")}
                 for k, v in cats.most_common()]
    donut = svg_donut(cat_items, center_top=fmt_int(
        summary.get("total_items", sum(cats.values()))), center_bottom="件美食",
        theme=DARK_CHART_THEME)
    cat_legend = "".join(
        f'<span><i style="background:{CATEGORY_COLORS.get(k, "#8D99AE")}"></i>'
        f'{esc(CATEGORY_NAMES.get(k, k))} {v}</span>'
        for k, v in cats.most_common())

    quotes = []
    if latest_late:
        quotes.append(("今年你最晚的一单，是 "
                       f"{esc(str(latest_late.get('date', ''))[5:])} 的 "
                       f"{esc(latest_late.get('time', ''))}，"
                       f"那一单的{esc((latest_late.get('items') or [{}])[0].get('name', top_item))}，"
                       "是夜宵，也是勇气。",
                       "深夜食堂 · 最晚一单"))
    if top_items:
        quotes.append((f"你对{esc(top_item)}的爱，量化出来是 "
                       f"<span style='color:var(--red)'>{top_items[0][1]} 份</span>——"
                       "本命之位，无人能动。", "本命之选 · 年度复购王"))
    if float(summary.get("coupon_saved", 0) or 0) > 0:
        quotes.append((f"今年你从麦麦省手里省下 "
                       f"<span style='color:var(--red)'>{fmt_money(summary['coupon_saved'])}</span>，"
                       "会过日子的人，运气都不会太差。", "省钱大师 · 精打细算"))

    cover_quotes = {
        "深夜食堂常客": "城市的深夜很长，但你的取餐柜一直亮着灯。",
        "麦麦省锦鲤": "省下的每一块钱，都变成了快乐复利。",
        "堡族战神": "两个面包夹一切，包括你今年的坚持。",
        "薯条永动机": "金黄的薯条，是你这一年稳定的坐标系。",
        "麦门全勤生": "一年四季，麦门永存，你就是行走的代言人。",
    }
    cover_quote = cover_quotes.get(perso, "这一年，谢谢你把很多顿饭交给了麦麦。")

    ch = []
    # 封面
    ch.append(f"""
<section class="cover">
  {love_it_banner()}
  {arches_svg(color=BRAND_YELLOW, width=120)}
  <div class="year pxf">{esc(str(year))} ANNUAL REPORT</div>
  <h1>你的<em>年度麦麦报告</em></h1>
  <div class="who">{esc(alias)} · 数据周期 {esc(str(meta.get('period', {}).get('start', '--')))} 至
    {esc(str(meta.get('period', {}).get('end', '--')))}</div>
  <div class="cover-quote">{cover_quote}</div>
  {sprite_parade(["px-burger.png", "px-fries.png", "px-cola.png", "px-clown.png"])}
  <div class="scroll-hint">▼ SCROLL ▼</div>
</section>""")
    # 01 一切的开始
    if first:
        f_items = "、".join(esc(i.get("name", "")) for i in first.get("items", [])[:3]) or "一份开心"
        first_photo = photo_card(PHOTO_FOR.get(top_item_cat, "ph-bigmac.jpg"),
                                 caption=f"一切的开始 · {esc(top_item)}", tilt="-3deg")
        ch.append(f"""
<section class="chapter">{tray(f'''
  <div class="photo-flex">
    <div style="flex:1.2;min-width:230px">
      <div class="big-quote">{esc(str(first.get('date', '')))}，你在
        <span class="hl">{esc(first.get('store', '麦麦餐厅'))}</span>
        点了第一单：{f_items}。</div>
      <div class="ch-sub">实付 {fmt_money(first.get('total', 0))} · 就餐方式
        {esc(first.get('type', '--'))} · 从此打开新世界的大门</div>
      {''.join(f'<span class="tag tag-yellow">{t}</span>' for t in ["DAY 1", "首单纪念", "梦开始的地方"])}
    </div>
    {first_photo}
  </div>''', icon_cat="breakfast", no="CHAPTER 01", title="一切的开始",
  sub="所有后来的无数次，都源于这一天。")}
</section>""")
    # 02 干饭战绩
    ch.append(f"""
<section class="chapter">{tray(f'''
  <div class="stat-row">
    <div class="stat"><div class="num">{fmt_int(summary.get('total_orders', len(orders)))}</div><div class="lbl">总订单</div></div>
    <div class="stat"><div class="num">{fmt_money(summary.get('total_spend', 0))}</div><div class="lbl">总花费</div></div>
    <div class="stat"><div class="num">{fmt_int(summary.get('total_items', sum(cats.values())))}</div><div class="lbl">吃掉的美食</div></div>
    <div class="stat"><div class="num">{fmt_int(summary.get('stores_count', len(stores)))}</div><div class="lbl">打卡门店</div></div>
  </div>
  <div class="card card-cream" style="box-shadow:4px 4px 0 var(--ink)">
    <div class="ch-sub" style="margin-bottom:8px;font-weight:800">每月消费与订单节奏</div>
    {svg_combo(spend_s, order_s, labels)}
    <div class="ch-sub">消费最高的月份是 <span style="color:var(--red);font-weight:900">{esc(peak_month)}</span>，
      那个月一定发生了不少故事。</div>
  </div>''', icon_cat="fries", no="CHAPTER 02", title="干饭战绩",
  sub="数字不会说谎，胃也是。")}
</section>""")
    # 03 本命之选
    top_photo = photo_card(PHOTO_FOR.get(top_item_cat, "ph-bigmac.jpg"),
                           caption=f"年度本命 · {esc(top_item)}", tilt="2deg")
    ch.append(f"""
<section class="chapter">{tray(f'''
  <div class="photo-flex">
    <div style="flex:1.25;min-width:230px">{rank_rows(item_rows)}</div>
    {top_photo}
  </div>
  <div class="card card-yellow" style="box-shadow:4px 4px 0 var(--ink);margin-top:6px">
    <div class="ch-sub" style="margin-bottom:8px;font-weight:900;color:#7A5A00">
      {pixel_icon("combo")} 足迹最深的门店</div>
    {rank_rows(store_rows)}
  </div>''', icon_cat="burger", no="CHAPTER 03", title="本命之选",
  sub="选择恐惧症的你，在这些餐品面前从不犹豫。")}
</section>""")
    # 04 深夜食堂
    late_top = item_counts({"orders": late}).most_common(2)
    late_html = rank_rows([{"label": n, "value": c, "meta": f"深夜吃掉 {c} 份",
                            "display": f"{c} 份"} for n, c in late_top])
    fries_caption = (f"深夜食堂 · {esc(late_top[0][0])} ×{late_top[0][1]}"
                     if late_top else "深夜食堂")
    fries_photo = photo_card("ph-fries.jpg", caption=fries_caption, tilt="-2deg")
    ch.append(f"""
<section class="chapter">{tray(f'''
  <div class="moon-box">{moon_svg()}</div>
  <div class="stat-row">
    <div class="stat"><div class="num">{fmt_int(len(late))}</div><div class="lbl">深夜订单</div></div>
    <div class="stat"><div class="num">{esc((latest_late or {}).get('time', '--:--'))}</div><div class="lbl">最晚一单</div></div>
    <div class="stat"><div class="num">{esc((latest_late or {}).get('date', '--'))}</div><div class="lbl">最晚一单日期</div></div>
  </div>
  <div class="photo-flex">
    <div style="flex:1.2;min-width:220px">
      {late_html if late_top else '<div class="ch-sub">今年你没有深夜下单，作息非常人类，respect。</div>'}
    </div>
    {fries_photo}
  </div>''', icon_cat="drink", no="CHAPTER 04", title="深夜食堂",
  sub="22:00 之后的麦麦，是城市给你的深夜食堂。")}
</section>""")
    # 05 吃饭的方式
    type_counter = defaultdict(int)
    for o in orders:
        type_counter[str(o.get("type", "unknown"))] += 1
    type_name = {"takeout": "到店取餐", "delivery": "麦乐送外卖",
                 "drive": "得来速", "mall": "麦麦商城", "unknown": "其他"}
    type_items = [{"label": type_name.get(k, k), "value": v, "display": f"{v} 单"}
                  for k, v in sorted(type_counter.items(), key=lambda x: -x[1])]
    ch.append(f"""
<section class="chapter">{tray(f'''
  <div class="card card-cream" style="box-shadow:4px 4px 0 var(--ink)">{html_bars(type_items)}</div>
  <div class="photo-flex" style="margin-top:16px">
    {photo_card("ph-restaurant.jpg", caption="你的主场 · 麦麦餐厅", tilt="2deg")}
    <div class="ch-sub" style="flex:1;min-width:200px">到店、外卖、得来速——你用脚步丈量城市的烟火气。
      每一家去过的门店，都是这一年的地理坐标。</div>
  </div>''', icon_cat="combo", no="CHAPTER 05", title="吃饭的方式",
  sub="怎么吃都是吃，开心就好。")}
</section>""")
    # 06 口味人格
    nutri_html = "".join(
        f'<div class="nutri"><div class="v pxf">{esc(str(v))}</div><div class="k">{esc(k)}</div></div>'
        for k, v in (nutri.get("display") or {}).items())
    nutri_css = ".nutri{background:#fff;border:3px solid var(--ink);border-radius:12px;padding:14px;text-align:center;box-shadow:3px 3px 0 var(--ink)}.nutri .v{font-size:15px;font-weight:800;color:var(--red)}.nutri .k{font-size:12px;color:#8A6A3B;margin-top:6px;font-weight:700}.nutri-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:12px;margin-top:14px}"
    ch.append(f"""
<section class="chapter">{tray(f'''
  <style>{nutri_css}</style>
  <div class="donut-flex" style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;
    justify-content:center;background:#fff;border:3px solid var(--ink);border-radius:14px;
    padding:18px;box-shadow:4px 4px 0 var(--ink)">
    {donut}
    <div style="flex:1;min-width:230px">
      <div class="ch-sub" style="margin-bottom:6px;font-weight:900">品类占比</div>
      <div class="legend">{cat_legend}</div>
      <div style="margin-top:14px"><span class="tag tag-red">年度口味人格：{esc(perso)}</span></div>
    </div>
  </div>
  {f'<div class="card card-cream" style="box-shadow:4px 4px 0 var(--ink)"><div class="ch-sub" style="margin-bottom:4px;font-weight:900">营养摄入总览（按订单餐品匹配）</div><div class="nutri-grid">{nutri_html}</div></div>' if nutri_html else ''}''',
  icon_cat="dessert", no="CHAPTER 06", title="口味人格",
  sub="这一年，你的胃暴露了真实的你。")}
</section>""")
    # 07 省钱大师
    acct_points = acct.get("points_available", summary.get("points_available", 0))
    ch.append(f"""
<section class="chapter">{tray(f'''
  <div class="stat-row">
    <div class="stat"><div class="num">{fmt_money(summary.get('coupon_saved', 0))}</div><div class="lbl">优惠券省下</div></div>
    <div class="stat"><div class="num">{fmt_int(acct_points)}</div><div class="lbl">可用积分</div></div>
    <div class="stat"><div class="num">{fmt_int((data.get('lottery') or {}).get('draw_count', 0))}</div><div class="lbl">积分抽奖次数</div></div>
  </div>
  <div class="bubble"><div class="q">省下的钱，都是给未来囤的<span style="color:var(--red)">快乐储备金</span>。</div>
  <div class="from">—— 麦麦省资深用户</div></div>''', icon_cat="other", no="CHAPTER 07",
  title="省钱大师", sub="会吃，更会省。")}
</section>""")
    # 08 年度金句
    quote_cards = "".join(
        f'<div class="bubble reveal"><div class="q">{q}</div><div class="from">—— {esc(src)}</div></div>'
        for q, src in quotes)
    ch.append(f"""
<section class="chapter">{tray(f'''
  {quote_cards}''', icon_cat="chicken", no="CHAPTER 08", title="年度金句",
  sub="把这一年，浓缩成三句话。")}
</section>""")
    # 结尾
    ch.append(f"""
<section class="end reveal">
  <div class="see pxf">SEE YOU NEXT YEAR</div>
  <div class="see-cn">明年见，{esc(alias)}</div>
  <div class="tags" style="margin-top:22px">
    <span class="tag tag-red">{esc(perso)}</span>
    <span class="tag tag-yellow">深夜订单 {fmt_int(len(late))} 单</span>
    <span class="tag">本命 {esc(top_item)}</span>
  </div>
  <div class="cover-quote">麦麦的灯，会一直亮着。</div>
  {sprite_parade(["px-clown.png", "px-fries.png", "px-burger.png", "px-cola.png"])}
  <div style="position:absolute;inset:0;z-index:-1">{confetti_svg()}</div>
</section>""")

    awning_top = f'<div class="top-strip"><div class="awning" style="background:{awning_css(size=30)}"></div><div class="checker" style="background:{checker_css()}"></div></div>'
    body = f"""
<div class="wrap">
  {awning_top}
  {''.join(ch)}
  <div style="text-align:center;margin-top:20px">{pixel_divider_svg(30, 7)}</div>
  {footer_note(data)}
</div>"""
    decor = (bg_decor(arches_color="#FFC72C", arches_opacity=0.05,
                      sprite_opacity=0.12) +
             f'<div class="scanlines"></div>')
    return page_shell(title, body, extra_css=REPORT_CSS,
                      theme_bg="#1A0B06", decor=decor)


def main():
    ap = argparse.ArgumentParser(description="年度麦麦报告渲染器")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="年度麦麦报告")
    ap.add_argument("--year", default="")
    args = ap.parse_args()
    data = load_data(args.data)
    if args.year:
        data.setdefault("meta", {})["year"] = args.year
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(data, args.title), encoding="utf-8")
    print(f"年度报告已生成 -> {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
