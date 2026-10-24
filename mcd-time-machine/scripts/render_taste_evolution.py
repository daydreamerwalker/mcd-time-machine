# -*- coding: utf-8 -*-
"""口味进化图 / 消费习惯 / 摄入物质变化 渲染器（托盘纸 + 像素进化树风格）。
用法:
  python render_taste_evolution.py --data normalized.json --out taste.html \
      [--title "我的口味进化史"]
章节: ① 口味人格进化时间线 ② 品类占比堆叠演变 ③ 摄入物质变化(热量/钠曲线)
      ④ 新欢与旧爱 ⑤ 消费习惯画像 ⑥ 进化预言
"""
import argparse
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (BRAND_RED, BRAND_YELLOW, CATEGORY_COLORS, CATEGORY_EMOJI,
                    CATEGORY_NAMES, PHOTO_FOR, all_orders, categorize,
                    category_counts, esc, fmt_int, fmt_money, footer_note,
                    html_bars, is_late_night, item_counts, item_nutrition,
                    load_data, month_key, month_label, nice_ceil, page_shell,
                    photo_card, quarterly_persona, sprite_tag, svg_donut,
                    svg_line_chart, svg_stacked_bars)
from pixel_art import (arches_svg, awning_css, bg_decor, barcode_css,
                       checker_css, love_it_banner, pixel_divider_svg,
                       pixel_icon, sprite_parade)

TASTE_CSS = """
.wrap{max-width:840px}
.sec-title{font-size:25px;font-weight:900;margin:44px 0 4px;display:flex;
align-items:center;gap:12px}
.sec-title .px-icon{width:40px}
.sec-sub{font-size:13.5px;color:#8A6A3B;margin-bottom:18px;line-height:1.9;
font-weight:600}
.timeline{display:flex;gap:0;overflow-x:auto;padding:28px 6px 12px;margin:0 -6px}
.tl-item{flex:1;min-width:148px;position:relative;text-align:center;padding:0 8px}
.tl-item::before{content:"";position:absolute;top:12px;left:-50%;width:100%;height:5px;
background:repeating-linear-gradient(45deg,var(--red) 0 8px,var(--yellow) 8px 16px);
opacity:.5;z-index:0}
.tl-item:first-child::before{display:none}
.tl-dot{position:relative;z-index:1;width:26px;height:26px;border-radius:50%;
margin:0 auto 12px;background:var(--yellow);border:4px solid var(--ink);
box-shadow:3px 3px 0 var(--ink)}
.tl-q{font-size:12px;font-weight:900;color:#A08C6D;letter-spacing:.06em;
font-family:'Press Start 2P',monospace}
.tl-cat{font-size:16px;font-weight:900;margin:8px 0 2px}
.tl-share{font-size:12px;color:#8A6A3B;font-weight:700}
.tl-tag{display:inline-block;margin-top:8px;font-size:11.5px;font-weight:900;
padding:5px 11px;border-radius:99px;background:var(--red);color:#fff;
border:3px solid var(--ink);box-shadow:2px 2px 0 var(--ink)}
.evo-card{background:var(--yellow);border:4px solid var(--ink);border-radius:18px;
padding:24px;box-shadow:8px 8px 0 var(--ink);margin:16px 0;position:relative;
overflow:hidden}
.evo-card::after{content:"";position:absolute;right:-30px;bottom:-30px;width:150px;
height:150px;border-radius:50%;background:rgba(255,255,255,.25)}
.evo-head{display:flex;align-items:center;gap:14px;margin-bottom:8px;
position:relative;z-index:1}
.evo-emoji{font-size:36px}
.evo-name{font-size:19px;font-weight:900}
.evo-desc{font-size:13.5px;color:#6B4A00;line-height:1.95;position:relative;z-index:1;
font-weight:600}
.evo-path{font-family:'Press Start 2P',monospace;font-size:12px;color:var(--red);
margin-top:10px;position:relative;z-index:1;line-height:1.8}
.shift-row{display:flex;align-items:center;gap:12px;padding:10px 0;
border-bottom:3px dotted rgba(43,20,8,.14);font-size:14px}
.shift-row:last-child{border-bottom:none}
.shift-cat{width:110px;flex:none;font-weight:900}
.shift-track{flex:1;height:16px;background:rgba(43,20,8,.07);
border:2px solid var(--ink);border-radius:99px;position:relative;overflow:hidden}
.shift-fill{position:absolute;top:0;bottom:0;border-radius:99px}
.shift-pct{width:96px;flex:none;text-align:right;font-weight:900;
font-variant-numeric:tabular-nums;font-family:'Press Start 2P',monospace;font-size:11px}
.up{color:var(--red)}
.down{color:#4C9A6A}
.habit-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
gap:12px;margin:14px 0}
.habit{background:#fff;border:3px solid var(--ink);border-radius:14px;padding:16px;
text-align:center;box-shadow:4px 4px 0 var(--ink)}
.habit .v{font-size:17px;font-weight:900;color:var(--red);
font-family:'Press Start 2P',monospace;line-height:1.5}
.habit .k{font-size:12px;color:#8A6A3B;margin-top:8px;font-weight:800}
.prophecy{background:var(--red);color:#fff;border:4px solid var(--ink);
border-radius:18px;padding:28px;margin:30px 0;line-height:2.1;font-size:15px;
box-shadow:8px 8px 0 var(--ink);position:relative;overflow:hidden}
.prophecy::before{content:"";position:absolute;left:0;right:0;top:0;height:10px;
background:repeating-linear-gradient(45deg,var(--yellow) 0 14px,#fff 14px 28px)}
.prophecy{padding-top:40px}
.prophecy b{color:var(--yellow)}
.photo-flex{display:flex;gap:22px;align-items:center;flex-wrap:wrap;margin:6px 0}
.photo-flex .polaroid{flex:1;min-width:210px;max-width:270px}
"""

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def quarter_key(date_str):
    y, m = int(str(date_str)[:4]), int(str(date_str)[5:7])
    return f"{str(y)[2:]}年Q{(m - 1) // 3 + 1}"


def build(data: dict, title: str) -> str:
    orders = all_orders(data)
    meta = data.get("meta") or {}
    summary = data.get("summary") or {}

    q_cats = defaultdict(Counter)
    for o in orders:
        for it in o.get("items", []):
            q_cats[quarter_key(o.get("date", ""))][categorize(it.get("name", ""))] += int(it.get("qty", 1) or 1)
    q_keys = sorted(q_cats)
    tl_items, stacked_rows, q_personas = [], [], {}
    for qk in q_keys:
        cats = q_cats[qk]
        total = sum(cats.values()) or 1
        top_cat, top_n = cats.most_common(1)[0]
        share = top_n / total
        q_personas[qk] = quarterly_persona(cats)
        tl_items.append(
            f'<div class="tl-item"><div class="tl-dot"></div>'
            f'<div class="tl-q">{esc(qk)}</div>'
            f'<div class="tl-cat">{CATEGORY_EMOJI.get(top_cat, "✨")} '
            f'{esc(CATEGORY_NAMES.get(top_cat, top_cat))}</div>'
            f'<div class="tl-share">占比 {share*100:.0f}%</div>'
            f'<div class="tl-tag">{esc(q_personas[qk])}</div></div>')
        stacked_rows.append({"label": qk.replace("年", ""),
                             "segments": [{"value": v, "color": CATEGORY_COLORS.get(k, "#8D7B68"),
                                           "name": CATEGORY_NAMES.get(k, k)[:2]}
                                          for k, v in cats.most_common()]})
    path = []
    for qk in q_keys:
        if not path or path[-1] != q_personas[qk]:
            path.append(q_personas[qk])
    path_str = " → ".join(path) if path else "麦门全勤生"

    # 摄入物质变化
    m_nutri = defaultdict(Counter)
    for o in orders:
        for it in o.get("items", []):
            n = item_nutrition(it)
            q = int(it.get("qty", 1) or 1)
            for k, v in n.items():
                m_nutri[month_key(o.get("date", ""))][k] += v * q
    m_keys = sorted(m_nutri)
    m_labels = [month_label(k) for k in m_keys]
    cal_series = [round(m_nutri[k]["calories"]) for k in m_keys]
    na_series = [round(m_nutri[k]["sodium"] / 1000, 1) for k in m_keys]
    pro_series = [round(m_nutri[k]["protein"]) for k in m_keys]
    has_nutri = any(cal_series)

    # 新欢与旧爱
    dated = sorted(orders, key=lambda o: o.get("date", ""))
    half = max(1, len(dated) // 2)
    early, late_half = dated[:half], dated[half:]
    early_items, late_items = Counter(), Counter()
    for o in early:
        for it in o.get("items", []):
            early_items[it.get("name", "")] += int(it.get("qty", 1) or 1)
    for o in late_half:
        for it in o.get("items", []):
            late_items[it.get("name", "")] += int(it.get("qty", 1) or 1)
    new_fav = [k for k, _ in late_items.most_common() if k not in early_items][:3]
    old_fav = [k for k, _ in early_items.most_common() if k not in late_items][:3]
    early_cats, late_cats = Counter(), Counter()
    for o in early:
        for it in o.get("items", []):
            early_cats[categorize(it.get("name", ""))] += int(it.get("qty", 1) or 1)
    for o in late_half:
        for it in o.get("items", []):
            late_cats[categorize(it.get("name", ""))] += int(it.get("qty", 1) or 1)
    e_total = sum(early_cats.values()) or 1
    l_total = sum(late_cats.values()) or 1
    shifts = []
    for cat in set(early_cats) | set(late_cats):
        delta = (late_cats.get(cat, 0) / l_total - early_cats.get(cat, 0) / e_total) * 100
        if abs(delta) >= 3:
            shifts.append({"label": CATEGORY_NAMES.get(cat, cat), "value": abs(delta),
                           "cat": cat, "delta": delta})
    shifts.sort(key=lambda x: -x["value"])
    shift_rows = []
    for s in shifts[:6]:
        arrow = "↑" if s["delta"] > 0 else "↓"
        cls = "up" if s["delta"] > 0 else "down"
        w = min(100, abs(s["delta"]) * 2.2)
        color = CATEGORY_COLORS.get(s["cat"], "#8D7B68")
        shift_rows.append(
            f'<div class="shift-row"><span class="shift-cat">{esc(s["label"])}</span>'
            f'<span class="shift-track"><span class="shift-fill" '
            f'style="width:{w:.0f}%;background:{color}"></span></span>'
            f'<span class="shift-pct {cls}">{arrow} {abs(s["delta"]):.0f}%</span></div>')

    # 消费习惯画像
    tod = {"早餐": 0, "午餐": 0, "下午茶": 0, "晚餐": 0, "深夜食堂": 0}
    wd_counter = Counter()
    for o in orders:
        t = o.get("time", "")
        hh = int(t.split(":")[0]) if ":" in t else 12
        if is_late_night(o) or hh >= 21:
            tod["深夜食堂"] += 1
        elif hh < 10:
            tod["早餐"] += 1
        elif hh < 14:
            tod["午餐"] += 1
        elif hh < 17:
            tod["下午茶"] += 1
        else:
            tod["晚餐"] += 1
        try:
            wd_counter[date.fromisoformat(o.get("date", "2026-01-01")).weekday()] += 1
        except ValueError:
            pass
    fav_wd = WEEKDAY_NAMES[wd_counter.most_common(1)[0][0]] if wd_counter else "--"
    avg_order = (float(summary.get("total_spend", 0)) / len(orders)) if orders else 0
    per_month = len(orders) / max(1, len({month_key(o.get("date", "")) for o in orders}))
    tod_items = [{"label": k, "value": v, "display": f"{v} 单",
                  "color": BRAND_RED if k == "深夜食堂" else BRAND_YELLOW}
                 for k, v in tod.items() if v]
    tod_donut = svg_donut([{"label": k, "value": v,
                            "color": BRAND_RED if k == "深夜食堂" else BRAND_YELLOW}
                           for k, v in tod.items() if v],
                          center_top=str(len(orders)), center_bottom="总订单")

    secs = []
    secs.append(f"""
<div class="sec-title">{pixel_icon("combo")} 🧬 口味人格进化时间线</div>
<div class="sec-sub">按季度统计你的主导品类与口味人格——看看你是怎么一步步进化的。</div>
<div class="card"><div class="timeline">{''.join(tl_items)}</div></div>
<div class="evo-card">
  <div class="evo-head"><span class="evo-emoji">🐣➡️🦖</span>
    <span class="evo-name">进化路线</span></div>
  <div class="evo-desc">口味是会成长的。从 {esc(q_keys[0]) if q_keys else '--'} 到
    {esc(q_keys[-1]) if q_keys else '--'}，你的品类偏好发生了这些变化——</div>
  <div class="evo-path pxf">{esc(path_str)}</div>
</div>""")

    secs.append(f"""
<div class="sec-title">{pixel_icon("burger")} 📊 品类占比演变</div>
<div class="sec-sub">每个季度，你的胃如何分配它的爱。</div>
<div class="card">{svg_stacked_bars(stacked_rows)}</div>""")

    if has_nutri:
        secs.append(f"""
<div class="sec-title">{pixel_icon("drink")} 🔥 摄入物质变化</div>
<div class="sec-sub">热量与钠的月度曲线（钠按克计）。数据来自订单餐品营养匹配，
  精确值以麦当劳官方营养信息为准。</div>
<div class="card">
  <div style="font-size:15px;font-weight:900;margin-bottom:6px">每月热量摄入（kcal）</div>
  {svg_line_chart([{"name": "热量", "color": BRAND_RED, "values": cal_series}], m_labels)}
  <div style="font-size:15px;font-weight:900;margin:20px 0 6px">每月钠摄入（g）</div>
  {svg_line_chart([{"name": "钠", "color": "#3E7CB1", "values": na_series}], m_labels, y_unit="g")}
  <div style="font-size:15px;font-weight:900;margin:20px 0 6px">每月蛋白质摄入（g）</div>
  {svg_line_chart([{"name": "蛋白质", "color": "#7CB342", "values": pro_series}], m_labels, y_unit="g")}
</div>""")
    else:
        secs.append(f"""
<div class="sec-title">{pixel_icon("drink")} 🔥 摄入物质变化</div>
<div class="sec-sub">订单中未匹配到营养数据，跳过曲线。可补充 list-nutrition-foods
  的匹配结果后重新生成。</div>""")

    new_old_photo = photo_card(
        PHOTO_FOR.get(late_cats.most_common(1)[0][0] if late_cats else "burger",
                      "ph-bigmac.jpg"),
        caption=f"新欢 · {esc(new_fav[0])}" if new_fav else "新欢待定", tilt="3deg")
    secs.append(f"""
<div class="sec-title">{pixel_icon("dessert")} 💔 新欢与旧爱</div>
<div class="sec-sub">拿今年后半程和前半程对比，你的胃变心了吗？</div>
<div class="card">
  <div class="photo-flex">
    <div style="flex:1.3;min-width:230px">
      <div style="font-size:15px;font-weight:900;margin-bottom:10px">🆕 新宠榜</div>
      <div class="sec-sub" style="margin-bottom:16px">{esc('、'.join(new_fav)) if new_fav else '这一年你没有换过心头好，专一得让人感动。'}</div>
      <div style="font-size:15px;font-weight:900;margin-bottom:10px">📉 失宠榜</div>
      <div class="sec-sub">{esc('、'.join(old_fav)) if old_fav else '没有旧爱被冷落，你是个博爱但长情的人。'}</div>
    </div>
    {new_old_photo}
  </div>
</div>
<div class="card">
  <div style="font-size:15px;font-weight:900;margin-bottom:8px">品类占比变化（前后半程差值）</div>
  {''.join(shift_rows) if shift_rows else '<div class="sec-sub">品类结构非常稳定，你没有明显变心。</div>'}
</div>""")

    secs.append(f"""
<div class="sec-title">{pixel_icon("chicken")} 🧭 消费习惯画像</div>
<div class="sec-sub">什么时候吃、多久吃一次、每次花多少——习惯比口味更诚实。<br>
  时段口径：早餐 10:00 前 / 午餐 10:00–14:00 / 下午茶 14:00–17:00 / 晚餐 17:00–21:00 / 深夜食堂 21:00 后。</div>
<div class="habit-grid">
  <div class="habit"><div class="v">{esc(fav_wd)}</div><div class="k">最爱的下单日</div></div>
  <div class="habit"><div class="v">{fmt_money(avg_order)}</div><div class="k">平均每单实付</div></div>
  <div class="habit"><div class="v">{per_month:.1f}单</div><div class="k">月均订单数</div></div>
  <div class="habit"><div class="v">{fmt_int(tod['深夜食堂'])}单</div><div class="k">深夜食堂打卡</div></div>
</div>
<div class="card" style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;
justify-content:center">{tod_donut}
<div style="flex:1;min-width:230px">{html_bars(tod_items)}</div></div>""")

    top_now = late_items.most_common(1)[0][0] if late_items else (
        item_counts(data).most_common(1)[0][0] if item_counts(data) else "麦乐鸡")
    next_cat = late_cats.most_common(1)[0][0] if late_cats else "burger"
    secs.append(f"""
<div class="prophecy">🔮 <b>进化预言</b>：按当前趋势，下个季度你的主导品类将是
  <b>{esc(CATEGORY_NAMES.get(next_cat, '汉堡主食'))}</b>，
  深夜订单预计 {fmt_int(int(tod['深夜食堂'] * 1.1) + 1)} 单。
  最新心头好是 <b>{esc(top_now)}</b>——建议继续专情，或者大胆变心，胃的旅程本来就没有 KPI。</div>""")

    body = f"""
<div class="wrap">
  <div class="awning" style="background:{awning_css(size=30)}"></div>
  <div class="page-head reveal">
    <div class="kicker">TASTE EVOLUTION</div>
    <h1>{esc(title)}</h1>
    <div class="sub">{esc(meta.get('user_alias', '你'))} · 摄入物质与口味偏好变化全记录</div>
  </div>
  {''.join(f'<div class="reveal">{s}</div>' for s in secs)}
  <div style="text-align:center;margin-top:36px">{pixel_divider_svg(30, 7)}</div>
  <div style="text-align:center;margin-top:18px">{love_it_banner()}</div>
  {footer_note(data)}
</div>"""
    decor = bg_decor(sprites=("px-fries.png", "px-burger.png", "px-cola.png", "px-clown.png"))
    return page_shell(title, body, extra_css=TASTE_CSS, decor=decor)


def main():
    ap = argparse.ArgumentParser(description="口味进化图渲染器")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="我的口味进化史")
    args = ap.parse_args()
    data = load_data(args.data)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(data, args.title), encoding="utf-8")
    print(f"口味进化图已生成 -> {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
