# -*- coding: utf-8 -*-
"""情感语录卡片渲染器（麦当劳收藏卡风格）。
用法:
  python render_mood_cards.py --data normalized.json --out cards.html \
      [--title "麦麦心情卡片"] [--cards cards.json]

--cards JSON 结构（Claude 按 references/emotion-map.md 生成文案后写入）:
  [{"emotion": "healing", "main": "主文案 20-60 字",
    "sub": "副文案 8-16 字", "notes": ["数据注脚1", "数据注脚2"]}]
省略 --cards 时进入模板兜底模式（基于真实统计数据生成 3 张卡片）。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (EMOTIONS, all_orders, emotion_of, esc, fmt_int, fmt_money,
                    footer_note, is_late_night, item_counts,
                    page_shell, store_counts, sprite_tag)
from pixel_art import (awning_css, bg_decor, love_it_banner,
                       pixel_divider_svg)

CARD_CSS = """
.grid{display:flex;flex-wrap:wrap;gap:30px;justify-content:center;margin-top:34px}
.mood-card{position:relative;width:322px;min-height:430px;border:4px solid var(--ink);
border-radius:18px;padding:0 0 20px;display:flex;flex-direction:column;overflow:hidden;
box-shadow:10px 10px 0 var(--ink);transition:transform .35s ease;background:#fff}
.mood-card:hover{transform:translate(-3px,-3px);box-shadow:14px 14px 0 var(--ink)}
.mood-card .top-awning{height:16px;border-bottom:4px solid var(--ink)}
.mood-card .body{padding:20px 22px 0;display:flex;flex-direction:column;flex:1;
position:relative;z-index:1}
.mood-card .emotion-tag{align-self:flex-start;font-size:13px;font-weight:900;
letter-spacing:.12em;padding:6px 13px;border:3px solid var(--ink);border-radius:99px;
box-shadow:3px 3px 0 var(--ink);background:#fff}
.mood-card .emos{font-size:27px;margin-top:16px;letter-spacing:5px}
.mood-card .main{font-size:22px;font-weight:900;line-height:1.62;margin-top:14px;flex:1}
.mood-card .sub{font-size:14.5px;font-weight:700;margin-top:12px}
.mood-card .notes{display:flex;flex-wrap:wrap;gap:7px;margin-top:16px;position:relative;
z-index:1;padding:0 22px}
.mood-card .notes span{font-size:11.5px;padding:5px 10px;border-radius:8px;
font-weight:800;border:2.5px solid var(--ink);background:#fff;
box-shadow:2px 2px 0 var(--ink)}
.mood-card .card-foot{margin-top:16px;padding:0 22px;display:flex;align-items:center;
justify-content:space-between;gap:10px;position:relative;z-index:1}
.mood-card .card-foot .loveit{padding:4px 10px;box-shadow:3px 3px 0 var(--ink)}
.mood-card .card-foot .loveit-t{font-size:10px;letter-spacing:.12em}
.mood-card .card-foot .loveit-m{font-size:12px}
.mood-card .peek{position:absolute;right:-10px;bottom:44px;width:104px;opacity:.95;
filter:drop-shadow(3px 3px 0 rgba(43,20,8,.3));z-index:0}
.mood-card .confetti{position:absolute;inset:0;z-index:0}
.mood-card .starburst{position:absolute;left:-24px;top:52px;font-size:34px;opacity:.8;
animation:bob 3s ease-in-out infinite}
"""

# 每张卡片角落探头的像素精灵（按情感轮换）
_PEEK = {
    "healing": "px-fries.png", "happy": "px-burger.png", "melancholy": "px-cola.png",
    "lonely": "px-cola.png", "passion": "px-burger.png", "chill": "px-fries.png",
    "sweet": "px-cola.png", "nostalgic": "px-clown.png", "grateful": "px-clown.png",
    "rebel": "px-fries.png",
}


def auto_cards(data: dict) -> list:
    """无 --cards 时的模板兜底：基于统计数据生成 3 张不同情感卡片。"""
    orders = all_orders(data)
    summary = data.get("summary") or {}
    late = [o for o in orders if is_late_night(o)]
    items = item_counts(data)
    stores = store_counts(data)
    top_item, top_n = items.most_common(1)[0] if items else ("麦乐鸡", 0)
    top_store, store_n = stores.most_common(1)[0] if stores else ("麦麦餐厅", 0)
    latest_late = max((o.get("time", "") for o in late), default="--:--")

    return [
        {"emotion": "healing",
         "main": f"今年有 {len(late)} 个深夜，是{top_item}陪你走过的。",
         "sub": "辛苦了，先吃饭",
         "notes": [f"深夜订单 {len(late)} 单", f"最晚一单 {latest_late}",
                   f"#{summary.get('year', '')} 干饭人"]},
        {"emotion": "happy",
         "main": f"{fmt_int(summary.get('total_orders', len(orders)))} 单、"
                 f"{fmt_money(summary.get('total_spend', 0))}，快乐是有证据的！",
         "sub": "麦门信徒，年度实锤",
         "notes": [f"本命之选 {top_item} ×{top_n}",
                   f"常去据点 {top_store}"]},
        {"emotion": "rebel",
         "main": f"{latest_late} 的{top_item}怎么了？规则就是用来打破的。",
         "sub": "理直气壮，吃得开心",
         "notes": ["凌晨进食协会荣誉会员", f"{top_store} 常驻选手"]},
    ]


def render_card(card: dict) -> str:
    e = emotion_of(card.get("emotion", "healing"))
    key = card.get("emotion", "healing")
    notes = "".join(f"<span>{esc(n)}</span>" for n in card.get("notes", []))
    emos = "".join(e["emoji"][:3])
    peek = sprite_tag(_PEEK.get(key, "px-fries.png"), cls="peek")
    awning_top = (f'<div class="top-awning" style="background:'
                  f'{awning_css(size=22)}"></div>')
    return f"""
<div class="mood-card reveal" style="background:{e['bg']};color:{e['text']}">
  {awning_top}
  <div class="body">
    <span class="emotion-tag" style="background:{e['chip']}">今天的心情 · {esc(e['name'])}</span>
    <div class="emos">{emos}</div>
    <div class="main">{esc(card.get('main', ''))}</div>
    <div class="sub" style="color:{e['sub']}">{esc(card.get('sub', ''))}</div>
  </div>
  <div class="notes">{notes}</div>
  <div class="card-foot">
    {love_it_banner()}
    <span style="font-size:10px;font-weight:900;letter-spacing:.15em;opacity:.7">NO.{key[:3].upper()}</span>
  </div>
  {peek}
</div>"""


def build(data: dict, cards: list, title: str) -> str:
    body = f"""
<div class="wrap">
  <div class="awning" style="background:{awning_css(size=30)}"></div>
  <div class="page-head reveal">
    <div class="kicker">MOOD CARDS</div>
    <h1>{esc(title)}</h1>
    <div class="sub">选一种心情，让 {esc((data.get('meta') or {}).get('user_alias', '你'))}
      的麦麦数据说句话</div>
  </div>
  <div class="grid">{''.join(render_card(c) for c in cards)}</div>
  <div style="text-align:center;margin-top:36px">{pixel_divider_svg(30, 7)}</div>
  {footer_note(data)}
</div>"""
    decor = bg_decor(sprites=("px-clown.png", "px-fries.png", "px-burger.png", "px-cola.png"))
    return page_shell(title, body, extra_css=CARD_CSS, decor=decor)


def main():
    ap = argparse.ArgumentParser(description="麦麦情感语录卡片渲染器")
    ap.add_argument("--data", required=True, help="规范化数据 JSON（normalized.json）")
    ap.add_argument("--out", required=True, help="输出 HTML 路径")
    ap.add_argument("--title", default="麦麦心情卡片")
    ap.add_argument("--cards", help="文案 JSON：情感+主副文案+注脚（缺省走模板兜底）")
    args = ap.parse_args()

    from common import load_data
    data = load_data(args.data)
    if args.cards:
        cards = json.loads(Path(args.cards).read_text(encoding="utf-8"))
        if isinstance(cards, dict):
            cards = [cards]
    else:
        cards = auto_cards(data)
    if not cards:
        print("错误：cards 为空", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(data, cards, args.title), encoding="utf-8")
    print(f"已生成 {len(cards)} 张心情卡片 -> {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
