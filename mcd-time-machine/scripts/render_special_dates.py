# -*- coding: utf-8 -*-
"""特殊日期回忆专题渲染器（麦当劳门票小票 + 邮戳 + 拍立得风格）。
用法:
  python render_special_dates.py --data normalized.json --out special.html \
      [--topics "first,late-night,holiday,custom"] [--date 2026-05-20] \
      [--title "特殊日期回忆"] [--cards topics.json]

--cards JSON（文案由 AI 按情感生成，或用户情感选择驱动，结构同心情卡片）:
  [{"topic": "first", "emotion": "nostalgic", "main": "...", "sub": "...", "notes": ["..."]}]
省略 --cards 时按各主题自动生成模板文案。
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (PHOTO_FOR, SPRITE_FOR, all_orders, categorize, esc, fmt_int,
                    fmt_money, footer_note, is_late_night, item_counts,
                    latest_late_night, load_data, page_shell, photo_card,
                    sprite_tag)
from pixel_art import (arches_svg, awning_css, bg_decor, barcode_css,
                       confetti_svg, love_it_banner, moon_svg,
                       pixel_divider_svg, pixel_icon, stamp)

# 公历固定节日 + 2025-2027 农历节日（农历日期每年不同，可按需补充）
HOLIDAYS = {
    "2025-01-01": "元旦", "2025-01-29": "春节", "2025-02-14": "情人节",
    "2025-04-04": "清明节", "2025-05-01": "劳动节", "2025-05-31": "端午节",
    "2025-06-01": "儿童节", "2025-10-01": "国庆节", "2025-10-06": "中秋节",
    "2025-11-11": "双十一", "2025-12-25": "圣诞节",
    "2026-01-01": "元旦", "2026-02-14": "情人节", "2026-02-17": "春节",
    "2026-04-05": "清明节", "2026-05-01": "劳动节", "2026-06-19": "端午节",
    "2026-09-25": "中秋节", "2026-10-01": "国庆节", "2026-11-11": "双十一",
    "2026-12-25": "圣诞节",
    "2027-01-01": "元旦", "2027-02-06": "春节", "2027-02-14": "情人节",
    "2027-04-05": "清明节", "2027-05-01": "劳动节", "2027-06-09": "端午节",
    "2027-09-15": "中秋节", "2027-10-01": "国庆节", "2027-11-11": "双十一",
    "2027-12-25": "圣诞节",
}

TOPIC_STYLE = {
    "first":      {"name": "一切的开始", "emoji": "🌱", "accent": "#FFC72C",
                   "band": "linear-gradient(135deg,#FFC72C,#FFE9B8)",
                   "sprite": "px-burger.png", "icon": "combo"},
    "late-night": {"name": "深夜食堂", "emoji": "🌙", "accent": "#3E5BA9",
                   "band": "linear-gradient(135deg,#2B3A67,#4A5B8C)",
                   "sprite": "px-cola.png", "icon": "drink"},
    "holiday":    {"name": "节假日专辑", "emoji": "🎊", "accent": "#DA291C",
                   "band": "linear-gradient(135deg,#DA291C,#FF5A4E)",
                   "sprite": "px-clown.png", "icon": "burger"},
    "custom":     {"name": "自定义纪念日", "emoji": "📌", "accent": "#0E9F6E",
                   "band": "linear-gradient(135deg,#06D6A0,#7CB342)",
                   "sprite": "px-fries.png", "icon": "fries"},
}

SPECIAL_CSS = """
body{background:linear-gradient(180deg,#17120C 0%,#241A12 55%,#17120C 100%);color:#FFF6E0}
.wrap{max-width:840px}
/* ---- 门票小票 ---- */
.ticket{background:#FFFDF6;color:var(--ink);border:4px solid var(--ink);
border-radius:18px;box-shadow:10px 10px 0 var(--ink);margin:26px 0;
position:relative;overflow:hidden}
.ticket .band{color:#fff;padding:16px 24px;display:flex;align-items:center;gap:14px;
border-bottom:4px solid var(--ink);position:relative}
.ticket .band .emoji{font-size:30px}
.ticket .band .name{font-size:22px;font-weight:900;flex:1;text-shadow:2px 2px 0 rgba(0,0,0,.25)}
.ticket .band .date{font-family:'Press Start 2P',monospace;font-size:11px;
background:rgba(255,255,255,.92);color:var(--ink);padding:6px 10px;border:3px solid var(--ink);
border-radius:8px;box-shadow:3px 3px 0 var(--ink);white-space:nowrap}
.ticket .band .peek{position:absolute;right:110px;bottom:-8px;width:64px;opacity:.95;
filter:drop-shadow(2px 2px 0 rgba(43,20,8,.3))}
.ticket-body{padding:24px}
.ticket-foot{border-top:3px dashed var(--ink);margin-top:18px;padding:14px 24px 18px;
display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.ticket-foot .barcode{width:180px;height:34px}
.ticket-foot .serial{font-family:'Press Start 2P',monospace;font-size:10px;
color:#8A6A3B;letter-spacing:.1em}
.topic-quote{font-size:19px;font-weight:900;line-height:1.9;margin:4px 0 6px}
.topic-sub{font-size:14px;color:#7A5A36;line-height:1.9;font-weight:600}
.topic-notes{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.topic-notes span{font-size:12px;font-weight:800;padding:6px 11px;border-radius:8px;
background:var(--cream);border:2.5px solid var(--ink);box-shadow:2px 2px 0 var(--ink)}
.mini-stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:18px}
.mini{flex:1;min-width:110px;background:#fff;border:3px solid var(--ink);border-radius:12px;
padding:13px 10px;text-align:center;box-shadow:3px 3px 0 var(--ink)}
.mini .v{font-size:16px;font-weight:900;color:var(--red);
font-family:'Press Start 2P',monospace;line-height:1.5}
.mini .k{font-size:11.5px;color:#8A6A3B;margin-top:6px;font-weight:800}
.order-line{display:flex;gap:12px;align-items:baseline;padding:9px 2px;
border-bottom:2px dotted rgba(43,20,8,.16);font-size:14px}
.order-line:last-child{border-bottom:none}
.order-line .t{color:var(--red);font-weight:900;font-variant-numeric:tabular-nums;
flex:none;font-family:'Press Start 2P',monospace;font-size:10.5px}
.order-line .i{flex:1;font-weight:600}
.order-line .p{flex:none;font-weight:900}
.holiday-row{margin:12px 0;padding:13px 16px;border-radius:12px;background:#fff;
border:3px solid var(--ink);box-shadow:3px 3px 0 var(--ink)}
.holiday-row .h{font-size:15px;font-weight:900}
.holiday-row .h .d{color:var(--red);margin-right:8px;font-family:'Press Start 2P',monospace;
font-size:11px}
.holiday-row .meta{font-size:13px;color:#7A5A36;margin-top:5px;font-weight:600}
.empty{margin:12px 0;font-size:13.5px;color:#8A6A3B;line-height:1.9}
.photo-flex{display:flex;gap:22px;align-items:center;flex-wrap:wrap;margin:8px 0}
.photo-flex .polaroid{flex:1;min-width:200px;max-width:260px}
.stamp{position:absolute;right:22px;bottom:64px}
"""


def ticket(topic_key, date_label, inner, foot_serial):
    st = TOPIC_STYLE[topic_key]
    return f"""
<div class="ticket reveal">
  <div class="band" style="background:{st['band']}">
    <span class="emoji">{st['emoji']}</span>
    <span class="name">{esc(st['name'])}</span>
    <span class="date pxf">{esc(date_label)}</span>
    {sprite_tag(st['sprite'], cls="peek")}
  </div>
  <div class="ticket-body">{inner}</div>
  <div class="ticket-foot">
    <span class="serial">NO.{esc(foot_serial)}</span>
    <span style="font-size:11px;font-weight:800;color:#8A6A3B">MCD TIME MACHINE · 回忆存档</span>
    <span class="barcode" style="background:{barcode_css()}"></span>
  </div>
</div>"""


def order_lines(orders):
    out = []
    for o in orders[:8]:
        items = "、".join(str(i.get("name", "")) for i in o.get("items", [])[:3])
        out.append(f'<div class="order-line"><span class="t">{esc(o.get("date", ""))} '
                   f'{esc(o.get("time", ""))}</span>'
                   f'<span class="i">{esc(items)}</span>'
                   f'<span class="p">{fmt_money(o.get("total", 0))}</span></div>')
    if len(orders) > 8:
        out.append(f'<div class="empty">……等共 {len(orders)} 单</div>')
    return "".join(out)


def topic_first(data, card):
    orders = sorted(all_orders(data), key=lambda o: o.get("date", ""))
    if not orders:
        return None
    first = orders[0]
    try:
        days = (date.today() - date.fromisoformat(first["date"])).days
    except ValueError:
        days = 0
    items = "、".join(str(i.get("name", "")) for i in first.get("items", [])[:3]) or "一份开心"
    first_cat = categorize((first.get("items") or [{}])[0].get("name", ""))
    main = card.get("main") or (f"{first.get('date', '')}，一切从这顿饭开始。"
                                f"那一天你还不知道，接下来会爱上这里 {len(orders)} 次。")
    sub = card.get("sub") or "所有的无数次，都源于第一次"
    notes = card.get("notes") or [f"首单门店 {first.get('store', '麦麦餐厅')}",
                                  f"相识第 {days} 天", f"首单餐品 {items}"]
    photo = photo_card(PHOTO_FOR.get(first_cat, "ph-bigmac.jpg"),
                       caption=f"DAY 1 · {esc(items[:12])}", tilt="-3deg")
    inner = f"""
  <div class="photo-flex">
    <div style="flex:1.25;min-width:230px">
      <div class="topic-quote">{esc(main)}</div>
      <div class="topic-sub">{esc(sub)} · {esc(items)} · {fmt_money(first.get('total', 0))}</div>
      <div class="mini-stats">
        <div class="mini"><div class="v">{days}</div><div class="k">相识天数</div></div>
        <div class="mini"><div class="v">{len(orders)}</div><div class="k">总订单</div></div>
        <div class="mini"><div class="v">{fmt_money(first.get('total', 0))}</div><div class="k">首单金额</div></div>
      </div>
    </div>
    {photo}
  </div>
  <div class="topic-notes">{''.join(f'<span>{esc(n)}</span>' for n in notes)}</div>
  {stamp('DAY 1')}"""
    return ticket("first", esc(first.get("date", "")), inner,
                  f"FIRST-{esc(first.get('date', '').replace('-', ''))}")


def topic_late_night(data, card):
    late = [o for o in all_orders(data) if is_late_night(o)]
    if not late:
        inner = f"""
  <div class="empty">这一年你没有在深夜下单——早睡的人，运气都不会太差。
  麦麦的深夜灯，留给下次需要的你。</div>
  {photo_card("ph-cola.jpg", caption="深夜食堂 · 缺席的一次", tilt="2deg")}"""
        return ticket("late-night", "22:00 — 04:59", inner, "LATE-000")
    latest = latest_late_night(late)
    top = item_counts({"orders": late}).most_common(2)
    avg = sum(float(o.get("total", 0) or 0) for o in late) / len(late)
    main = card.get("main") or (f"{len(late)} 个深夜，麦麦都醒着。"
                                f"最晚的一次是 {latest.get('time', '')}，你点了"
                                f"{(latest.get('items') or [{}])[0].get('name', '麦乐鸡')}。")
    sub = card.get("sub") or "城市的深夜食堂，为你留了一盏灯"
    notes = card.get("notes") or [f"深夜订单 {len(late)} 单",
                                  f"最晚 {latest.get('date', '')} {latest.get('time', '')}",
                                  f"深夜挚爱 {top[0][0] if top else '--'} ×{top[0][1] if top else 0}"]
    fries_photo = photo_card("ph-fries.jpg",
                             caption=f"深夜挚爱 · {esc(top[0][0]) if top else '薯条'}",
                             tilt="-2deg")
    inner = f"""
  <div class="photo-flex">
    <div style="flex:1.25;min-width:230px">
      <div class="topic-quote">{esc(main)}</div>
      <div class="topic-sub">{esc(sub)}</div>
      <div class="mini-stats">
        <div class="mini"><div class="v">{len(late)}</div><div class="k">深夜订单</div></div>
        <div class="mini"><div class="v">{esc(latest.get('time', ''))}</div><div class="k">最晚一单</div></div>
        <div class="mini"><div class="v">{fmt_money(avg)}</div><div class="k">深夜均价</div></div>
      </div>
    </div>
    {fries_photo}
  </div>
  <div style="margin-top:16px">{order_lines(sorted(late, key=lambda o: (o.get('date', ''), o.get('time', '')), reverse=True)[:4])}</div>
  <div class="topic-notes">{''.join(f'<span>{esc(n)}</span>' for n in notes)}</div>
  <div style="position:absolute;right:18px;top:14px;width:56px;opacity:.9">{moon_svg()}</div>"""
    return ticket("late-night", "22:00 — 04:59", inner, f"LATE-{len(late):03d}")


def topic_holiday(data, card):
    orders = all_orders(data)
    by_date = {}
    for o in orders:
        by_date.setdefault(o.get("date", ""), []).append(o)
    rows = []
    for d, name in sorted(HOLIDAYS.items()):
        if d in by_date:
            os_ = by_date[d]
            items = "、".join(str(i.get("name", "")) for i in os_[0].get("items", [])[:2])
            rows.append(f'<div class="holiday-row"><div class="h"><span class="d">{d[5:]}</span>'
                        f'{esc(name)}</div><div class="meta">{esc(items)} · '
                        f'{fmt_money(os_[0].get("total", 0))}</div></div>')
    campaigns = "".join(
        f'<div class="holiday-row"><div class="h"><span class="d">{esc(str(c.get("date", ""))[5:])}</span>'
        f'{esc(c.get("title", "麦当劳活动"))}</div>'
        f'<div class="meta">来自活动日历 · {esc(c.get("status", ""))}</div></div>'
        for c in (data.get("campaigns") or [])[:6])
    body_rows = "".join(rows) if rows else ('<div class="empty">节日当天你没有下单——'
                                            '节日快乐，但麦麦也在等你。</div>')
    main = card.get("main") or "过节的日子，胃也有它的仪式感。"
    photo = photo_card("ph-restaurant.jpg", caption="节日里的麦麦餐厅", tilt="2deg")
    inner = f"""
  <div class="topic-quote">{esc(main)}</div>
  <div class="topic-sub">{esc(card.get('sub') or '元旦、春节、情人节、劳动节、端午、中秋、国庆、圣诞、双十一——那些有名字的日子里，你都吃了什么')}</div>
  <div class="photo-flex" style="margin-top:14px">
    <div style="flex:1.3;min-width:230px">{body_rows}</div>
    {photo}
  </div>
  {f'<div style="margin-top:14px"><div style="font-size:14px;font-weight:900;margin-bottom:6px">📅 同期活动日历</div>{campaigns}</div>' if campaigns else ''}
  <div style="position:absolute;inset:0;pointer-events:none;opacity:.5">{confetti_svg()}</div>"""
    return ticket("holiday", "HOLIDAY ALBUM", inner, f"HOLI-{len(rows):03d}")


def topic_custom(data, card, day):
    if not day:
        return None
    orders = all_orders(data)
    exact = [o for o in orders if o.get("date") == day]
    near = []
    if not exact:
        try:
            d0 = date.fromisoformat(day)
        except ValueError:
            return None
        for o in orders:
            try:
                if abs((date.fromisoformat(o["date"]) - d0).days) <= 3:
                    near.append(o)
            except (ValueError, KeyError):
                pass
    chosen = exact or near
    photo_name = PHOTO_FOR.get(
        categorize((chosen[0].get("items") or [{}])[0].get("name", "")) if chosen else "store",
        "ph-bigmac.jpg")
    photo = photo_card(photo_name, caption=f"纪念日 · {esc(day[5:])}", tilt="3deg")
    if not chosen:
        inner = f"""
  <div class="topic-quote">{esc(day)}，一个属于你的特别日子。</div>
  <div class="topic-sub">这一天（及前后 3 天）没有找到麦麦订单。也许那天你吃了别的——
    没关系，回忆不拘泥于一家餐厅。</div>
  {photo}
  {stamp(esc(day[5:].replace('-', '.')), color='#0E9F6E')}"""
        return ticket("custom", esc(day), inner, f"CUST-{esc(day.replace('-', ''))}")
    label = "当天的订单" if exact else "前后 3 天内的订单"
    items = "、".join(str(i.get("name", "")) for i in chosen[0].get("items", [])[:3])
    main = card.get("main") or (f"{esc(day)}，一个属于你的特别日子。"
                                f"这一天有 {len(chosen)} 单麦麦陪你度过。")
    inner = f"""
  <div class="photo-flex">
    <div style="flex:1.25;min-width:230px">
      <div class="topic-quote">{esc(main)}</div>
      <div class="topic-sub">{esc(card.get('sub') or '生日、纪念日、或者只是一个普通的今天——')}{esc(label)}：{esc(items)}</div>
    </div>
    {photo}
  </div>
  <div style="margin-top:14px">{order_lines(chosen)}</div>
  <div class="topic-notes">{''.join(f'<span>{esc(n)}</span>' for n in (card.get('notes') or [f'{len(chosen)} 单回忆']))}</div>
  {stamp(esc(day[5:].replace('-', '.')), color='#0E9F6E')}"""
    return ticket("custom", esc(day), inner, f"CUST-{esc(day.replace('-', ''))}")


def build(data, title, topics, day, cards_by_topic):
    blocks = []
    for t in topics:
        card = cards_by_topic.get(t, {})
        if t == "first":
            b = topic_first(data, card)
        elif t == "late-night":
            b = topic_late_night(data, card)
        elif t == "holiday":
            b = topic_holiday(data, card)
        elif t == "custom":
            b = topic_custom(data, card, day)
        else:
            b = None
        if b:
            blocks.append(b)
    if not blocks:
        blocks.append('<div class="empty" style="color:#FFF6E0;padding:40px 0">'
                      '没有可生成的专题，请检查 --topics 与数据。</div>')
    meta = data.get("meta") or {}
    body = f"""
<div class="wrap">
  <div class="awning" style="background:{awning_css(size=30)}"></div>
  <div class="page-head reveal" style="padding:40px 0 8px">
    <div class="kicker">SPECIAL DATES</div>
    <h1>{esc(title)}</h1>
    <div class="sub">{esc(meta.get('user_alias', '你'))} ·
      那些值得被记住的日子，麦麦都在场</div>
    <div style="margin-top:18px">{love_it_banner()}</div>
  </div>
  {''.join(blocks)}
  <div style="text-align:center;margin-top:36px">{pixel_divider_svg(30, 7)}</div>
  {footer_note(data)}
</div>"""
    decor = bg_decor(arches_color="#FFC72C", arches_opacity=0.05,
                     sprite_opacity=0.12)
    return page_shell(title, body, extra_css=SPECIAL_CSS,
                      theme_bg="#17120C", decor=decor)


def main():
    ap = argparse.ArgumentParser(description="特殊日期回忆专题渲染器")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="特殊日期回忆")
    ap.add_argument("--topics", default="first,late-night,holiday,custom",
                    help="逗号分隔: first,late-night,holiday,custom")
    ap.add_argument("--date", default="", help="自定义纪念日 YYYY-MM-DD")
    ap.add_argument("--cards", help="文案 JSON（按 topic 提供主副文案）")
    args = ap.parse_args()

    data = load_data(args.data)
    topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    cards_by_topic = {}
    if args.cards:
        for c in json.loads(Path(args.cards).read_text(encoding="utf-8")):
            cards_by_topic[c.get("topic", "")] = c
    if "custom" in topics and not args.date:
        print("提示：未提供 --date，跳过自定义纪念日专题。", file=sys.stderr)
        topics = [t for t in topics if t != "custom"]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(data, args.title, topics, args.date, cards_by_topic),
                   encoding="utf-8")
    print(f"特殊日期专题已生成 -> {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
