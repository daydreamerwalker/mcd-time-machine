# -*- coding: utf-8 -*-
"""mcd-time-machine 共享模块：设计令牌、像素字体、图片加载、SVG 图表、数据聚合。
视觉规范：麦当劳经典红黄 + 8-bit 像素 + 硬阴影贴纸风（去玻璃拟态）。
被四个渲染器与 pixel_art.py 导入。仅标准库。
"""
import base64
import html
import math
from collections import Counter, defaultdict
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS = SKILL_ROOT / "assets"
IMAGE_DIR = ASSETS / "images"
FONT_FILE = ASSETS / "fonts" / "PressStart2P-latin.woff2"

# ---------------------------------------------------------------- 品牌令牌

BRAND_RED = "#DA291C"
BRAND_DARK_RED = "#A81E15"
BRAND_YELLOW = "#FFC72C"
BRAND_CREAM = "#FFF6E0"
BRAND_PAPER = "#FBF3E2"
INK = "#2B1408"          # 暖黑（描边/文字）
INK_SOFT = "#6B4A2A"     # 暖棕（次级文字）
PAPER_DARK = "#1A0B06"   # 深色章节底
FONT_STACK = ('"PingFang SC","Hiragino Sans GB","Microsoft YaHei",'
              '"Noto Sans SC",system-ui,-apple-system,sans-serif')

# 图片资源映射：品类 -> 实物图 / 像素精灵
PHOTO_FOR = {
    "burger": "ph-bigmac.jpg", "fries": "ph-fries.jpg", "drink": "ph-cola.jpg",
    "dessert": "ph-sundae.jpg", "chicken": "ph-nuggets.jpg",
    "breakfast": "ph-bigmac.jpg", "combo": "ph-nuggets.jpg",
    "store": "ph-restaurant.jpg", "other": "ph-restaurant.jpg",
}
SPRITE_FOR = {
    "fries": "px-fries.png", "burger": "px-burger.png", "drink": "px-cola.png",
    "clown": "px-clown.png",
}

# ---------------------------------------------------------------- 基础工具


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fmt_int(n) -> str:
    try:
        return f"{int(round(float(n))):,}"
    except (TypeError, ValueError):
        return "0"


def fmt_money(n) -> str:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return "¥0"
    if v == int(v):
        return f"¥{int(v):,}"
    return f"¥{v:,.2f}"


def fmt_wan(n, unit="") -> str:
    try:
        v = float(n)
    except (TypeError, ValueError):
        return "0" + unit
    if abs(v) >= 10000:
        s = f"{v / 10000:.1f}".rstrip("0").rstrip(".")
        return s + "万" + unit
    return f"{int(v):,}" + unit


def minutes_of(time_str) -> int:
    try:
        h, m = str(time_str).split(":")[:2]
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return -1


def is_late_night(order) -> bool:
    """22:00-04:59 视为深夜订单。"""
    t = minutes_of(order.get("time", ""))
    return t >= 22 * 60 or (0 <= t < 5 * 60)


def late_night_rank(time_str) -> int:
    """深夜时刻排序键：以 22:00 为原点，02:47 比 23:50 更晚。"""
    t = minutes_of(time_str)
    if t < 0:
        return -1
    return (t - 22 * 60) % (24 * 60)


def latest_late_night(orders):
    """深夜订单中时刻最晚的一单（02:47 优先于 23:50），并列时取日期更近的。"""
    late = [o for o in orders if is_late_night(o)]
    if not late:
        return None
    return max(late, key=lambda o: (late_night_rank(o.get("time", "")),
                                    o.get("date", "")))


def month_key(date_str) -> str:
    return str(date_str)[:7]


def month_label(key: str, with_year=True) -> str:
    y, m = key.split("-")
    if with_year and m == "01":
        return f"{y[2:]}年1月"
    return f"{int(m)}月"


def nice_ceil(v: float) -> float:
    if v <= 0:
        return 1.0
    exp = 10 ** math.floor(math.log10(v))
    m = v / exp
    for nice in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m <= nice:
            return nice * exp
    return 10 * exp


# ---------------------------------------------------------------- 品类映射

CATEGORY_RULES = [
    ("breakfast", ["早餐", "猪柳蛋", "扒饼", "热香饼", "早安", "麦满分"]),
    ("burger", ["堡", "汉堡", "巨无霸", "吉士", "不素之霸", "麦香鱼"]),
    ("chicken", ["麦乐鸡", "鸡翅", "鸡腿", "鸡块", "炸鸡", "脆汁鸡"]),
    ("fries", ["薯条", "薯格", "薯饼"]),
    ("dessert", ["甜筒", "冰淇淋", "圣代", "派", "蛋挞", "麦旋风", "蛋糕", "麦芽"]),
    ("drink", ["可乐", "雪碧", "咖啡", "拿铁", "美式", "奶茶", "果汁",
               "气泡水", "牛奶", "豆浆", "麦炫酷", "冰沙"]),
    ("combo", ["套餐", "乐园餐", "家庭桶", "分享盒"]),
]
CATEGORY_NAMES = {
    "burger": "汉堡主食", "chicken": "炸鸡小食", "fries": "薯条薯格",
    "drink": "饮品", "dessert": "甜点冰淇淋", "breakfast": "早餐",
    "combo": "套餐分享", "other": "其他",
}
CATEGORY_EMOJI = {
    "burger": "🍔", "chicken": "🍗", "fries": "🍟", "drink": "🥤",
    "dessert": "🍦", "breakfast": "🌅", "combo": "🎁", "other": "✨",
}
CATEGORY_COLORS = {
    "burger": "#DA291C", "chicken": "#F49B3C", "fries": "#FFC72C",
    "drink": "#3E7CB1", "dessert": "#E5608A", "breakfast": "#7CB342",
    "combo": "#7B2FBE", "other": "#8D7B68",
}


def categorize(name: str) -> str:
    for cat, kws in CATEGORY_RULES:
        if any(k in str(name) for k in kws):
            return cat
    return "other"


# ---------------------------------------------------------------- 情感调色板

EMOTIONS = {
    "healing":   {"name": "治愈", "emoji": ["🌙", "🍟", "🧸"],
                  "bg": "linear-gradient(160deg,#FFC72C 0%,#FFE9B8 55%,#FFF6E0 100%)",
                  "text": "#4A2C0F", "sub": "#8A6A3B", "chip": "rgba(74,44,15,.10)"},
    "happy":     {"name": "开心", "emoji": ["🎉", "🍔", "✨"],
                  "bg": "linear-gradient(160deg,#DA291C 0%,#FF5A4E 55%,#FFC72C 100%)",
                  "text": "#FFFFFF", "sub": "#FFE9D6", "chip": "rgba(255,255,255,.18)"},
    "melancholy": {"name": "emo", "emoji": ["🌧️", "🥤", "💧"],
                  "bg": "linear-gradient(160deg,#8A9BA8 0%,#B9C6CF 55%,#E8ECEF 100%)",
                  "text": "#3B4650", "sub": "#5D6B77", "chip": "rgba(59,70,80,.12)"},
    "lonely":    {"name": "孤独", "emoji": ["🚶", "🌃", "🍟"],
                  "bg": "linear-gradient(160deg,#2B2D42 0%,#4A5068 55%,#8D99AE 100%)",
                  "text": "#EDF2F4", "sub": "#B8C4CE", "chip": "rgba(237,242,244,.14)"},
    "passion":   {"name": "热血", "emoji": ["🔥", "💪", "⚡"],
                  "bg": "linear-gradient(160deg,#E63946 0%,#B0232F 55%,#1D1D1D 100%)",
                  "text": "#FFFFFF", "sub": "#FFD9D9", "chip": "rgba(255,255,255,.16)"},
    "chill":     {"name": "摆烂", "emoji": ["🛋️", "😴", "🥱"],
                  "bg": "linear-gradient(160deg,#A8C686 0%,#C9DDB4 55%,#F5F1E8 100%)",
                  "text": "#3D5229", "sub": "#6B8550", "chip": "rgba(61,82,41,.12)"},
    "sweet":     {"name": "甜蜜", "emoji": ["💕", "🍦", "🥰"],
                  "bg": "linear-gradient(160deg,#FFB3C6 0%,#FFD3DE 55%,#FFF0F3 100%)",
                  "text": "#A4133C", "sub": "#C96B86", "chip": "rgba(164,19,60,.10)"},
    "nostalgic": {"name": "怀旧", "emoji": ["📻", "🕰️", "🍦"],
                  "bg": "linear-gradient(160deg,#D9B382 0%,#E8CDA9 55%,#F4E8D8 100%)",
                  "text": "#6B4226", "sub": "#93704B", "chip": "rgba(107,66,38,.12)"},
    "grateful":  {"name": "感恩", "emoji": ["🙏", "💛", "🧡"],
                  "bg": "linear-gradient(160deg,#F4A261 0%,#F9C89B 55%,#FDF6EC 100%)",
                  "text": "#5C3D1E", "sub": "#96683F", "chip": "rgba(92,61,30,.12)"},
    "rebel":     {"name": "叛逆", "emoji": ["😈", "🃏", "🚀"],
                  "bg": "linear-gradient(160deg,#7B2FBE 0%,#9D4EDD 45%,#06D6A0 100%)",
                  "text": "#FFFFFF", "sub": "#E9DDFA", "chip": "rgba(255,255,255,.18)"},
}


def emotion_of(key: str) -> dict:
    return EMOTIONS.get(key, EMOTIONS["healing"])


# ---------------------------------------------------------------- 图片 / 字体加载

_URI_CACHE = {}


def _b64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def img_uri(name: str) -> str:
    """assets/images/<name> -> base64 data URI；不存在返回 ''。"""
    if name in _URI_CACHE:
        return _URI_CACHE[name]
    p = IMAGE_DIR / name
    suffix = p.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    uri = f"data:{mime};base64,{_b64(p)}" if p.exists() else ""
    _URI_CACHE[name] = uri
    return uri


def sprite_tag(name: str, cls="", style="") -> str:
    """像素精灵 <img>（assets/images 缺失时返回空字符串，装饰自动降级）。"""
    uri = img_uri(name)
    if not uri:
        return ""
    return (f'<img src="{uri}" class="sprite {cls}" alt="" aria-hidden="true" '
            f'style="{style}" loading="eager">')


def photo_tag(name: str, cls="", alt="") -> str:
    uri = img_uri(name)
    if not uri:
        return ""
    return f'<img src="{uri}" class="photo {cls}" alt="{esc(alt)}" loading="eager">'


def photo_card(name: str, caption="", tilt="-2deg", cls="") -> str:
    """拍立得相纸卡：白框 + 硬阴影 + 倾斜 + caption。图片缺失时返回空。"""
    if not img_uri(name):
        return ""
    return (f'<figure class="polaroid {cls}" style="transform:rotate({tilt})">'
            f'<div class="polaroid-img">{photo_tag(name)}</div>'
            f'{f"<figcaption>{esc(caption)}</figcaption>" if caption else ""}'
            f'</figure>')


def pixel_font_css() -> str:
    """Press Start 2P（latin 子集，base64 内联，离线可用）。"""
    b64 = _b64(FONT_FILE)
    if not b64:
        return ".pxf{font-family:ui-monospace,Consolas,monospace;font-weight:700}"
    return (f"@font-face{{font-family:'Press Start 2P';font-style:normal;"
            f"font-weight:400;font-display:swap;src:url(data:font/woff2;base64,{b64}) "
            f"format('woff2')}}\n"
            f".pxf{{font-family:'Press Start 2P',ui-monospace,Consolas,monospace}}")


# ---------------------------------------------------------------- 营养兜底库

# 常见餐品营养参考值（kcal / 蛋白质g / 脂肪g / 碳水g / 钠mg）。
# 仅当订单餐品未显式携带营养字段、且 list-nutrition-foods 匹配失败时兜底使用；
# 精确值以麦当劳官方营养信息为准。
NUTRITION_DB = {
    "巨无霸": (520, 27, 28, 45, 1050), "双层吉士汉堡": (450, 23, 24, 38, 900),
    "麦辣鸡腿堡": (510, 25, 26, 50, 1080), "麦香鱼": (380, 18, 17, 44, 700),
    "板烧鸡腿堡": (430, 24, 17, 48, 860), "不素之霸": (560, 28, 30, 46, 1150),
    "麦乐鸡": (230, 12, 13, 18, 520), "薯条": (320, 4, 15, 43, 260),
    "薯格": (300, 4, 14, 40, 320), "甜筒": (150, 4, 5, 23, 60),
    "麦旋风": (330, 8, 10, 52, 130), "麦辣鸡翅": (260, 16, 16, 12, 620),
    "可乐": (180, 0, 0, 45, 20), "咖啡": (120, 6, 6, 12, 60),
    "玉米杯": (140, 5, 2, 28, 180), "猪柳蛋麦满分": (410, 19, 18, 42, 780),
    "培根蔬萃双层牛堡": (610, 32, 34, 46, 1180), "脆汁鸡腿": (420, 24, 24, 22, 780),
    "奥利奥麦旋风": (360, 8, 12, 55, 150), "香芋派": (260, 2, 12, 37, 120),
    "菠萝派": (250, 2, 11, 36, 110), "奶茶": (220, 3, 6, 38, 45),
    "拿铁": (190, 10, 8, 20, 90), "美式咖啡": (15, 1, 0, 2, 10),
    "阳光橙": (160, 1, 0, 39, 15), "牛奶": (130, 8, 5, 12, 90),
}


def item_nutrition(item: dict) -> dict:
    """返回单件餐品营养 {'calories':..,'protein':..,'fat':..,'carb':..,'sodium':..}，
    显式字段优先，其次 NUTRITION_DB 模糊匹配，都没有则全 0。"""
    keys = ("calories", "protein", "fat", "carb", "sodium")
    if all(item.get(k) is not None for k in keys):
        return {k: float(item[k]) for k in keys}
    name = str(item.get("name", ""))
    for db_name, vals in NUTRITION_DB.items():
        if db_name in name or name in db_name:
            return dict(zip(keys, (float(v) for v in vals)))
    return {k: 0.0 for k in keys}


# ---------------------------------------------------------------- SVG 图表

LIGHT_CHART_THEME = {"grid": "rgba(120,90,60,.18)", "label": "#A08C6D",
                     "dot": "#FFFFFF", "num": INK, "sub": "#A09482"}
DARK_CHART_THEME = {"grid": "rgba(255,255,255,.13)", "label": "#C9B896",
                    "dot": "#1A0B06", "num": "#FFF6E0", "sub": "#C9B896"}


def svg_line_chart(series, labels, width=720, height=280,
                   pad_l=52, pad_r=16, pad_t=34, pad_b=34, y_unit="",
                   theme=None):
    """series: [{"name": str, "color": str, "values": [num,...]}], labels: [str,...]"""
    theme = theme or LIGHT_CHART_THEME
    if not labels:
        return ""
    all_vals = [v for s in series for v in s["values"] if isinstance(v, (int, float))]
    ymax = nice_ceil(max(all_vals) * 1.1) if all_vals else 1.0
    n = len(labels)
    iw, ih = width - pad_l - pad_r, height - pad_t - pad_b
    x = lambda i: pad_l + (iw * i / max(n - 1, 1))
    y = lambda v: pad_t + ih - (v / ymax) * ih

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" '
             f'xmlns="http://www.w3.org/2000/svg" role="img">']
    for k in range(6):
        v = ymax * k / 5
        yy = y(v)
        parts.append(f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width-pad_r}" y2="{yy:.1f}" '
                     f'stroke="{theme["grid"]}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{yy+4:.1f}" text-anchor="end" '
                     f'class="axis-label" fill="{theme["label"]}" font-size="11">'
                     f'{fmt_wan(v)}{y_unit}</text>')
    step = max(1, math.ceil(n / 9))
    for i in range(0, n, step):
        parts.append(f'<text x="{x(i):.1f}" y="{height-10}" text-anchor="middle" '
                     f'class="axis-label" fill="{theme["label"]}" font-size="11">'
                     f'{esc(labels[i])}</text>')
    for s in series:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(s["values"]))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{s["color"]}" '
                     f'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
        for i, v in enumerate(s["values"]):
            parts.append(f'<rect x="{x(i)-3.4:.1f}" y="{y(v)-3.4:.1f}" width="6.8" '
                         f'height="6.8" fill="{s["color"]}" stroke="{theme["dot"]}" '
                         f'stroke-width="1.4"/>')
    parts.append("</svg>")
    return "".join(parts)


def svg_stacked_bars(rows, width=720, height=300, pad_l=48, pad_r=14,
                     pad_t=26, pad_b=40, theme=None):
    """rows: [{"label": str, "segments": [{"value": num, "color": str, "name": str}]}]
    百分比堆叠柱状图（像素风格：段间留缝）。"""
    theme = theme or LIGHT_CHART_THEME
    if not rows:
        return ""
    iw, ih = width - pad_l - pad_r, height - pad_t - pad_b
    n = len(rows)
    bw = min(64, iw / n * 0.56)
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" '
             f'xmlns="http://www.w3.org/2000/svg">']
    for k in range(6):
        yy = pad_t + ih - ih * k / 5
        parts.append(f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width-pad_r}" y2="{yy:.1f}" '
                     f'stroke="{theme["grid"]}"/>')
        parts.append(f'<text x="{pad_l-8}" y="{yy+4:.1f}" text-anchor="end" '
                     f'class="axis-label" fill="{theme["label"]}" font-size="11">'
                     f'{k*20}%</text>')
    for ri, row in enumerate(rows):
        total = sum(s["value"] for s in row["segments"]) or 1
        x = pad_l + iw * (ri + .5) / n - bw / 2
        y_cursor = pad_t + ih
        for seg in row["segments"]:
            frac = seg["value"] / total
            bh = max(0.0, frac * ih - 2)
            y_cursor -= frac * ih
            parts.append(f'<rect x="{x:.1f}" y="{y_cursor:.1f}" width="{bw:.1f}" '
                         f'height="{bh:.1f}" fill="{seg["color"]}"/>')
            if frac >= 0.12:
                parts.append(f'<text x="{x+bw/2:.1f}" y="{y_cursor+frac*ih/2+4:.1f}" '
                             f'text-anchor="middle" font-size="10.5" font-weight="700" '
                             f'fill="#fff">{seg["name"]}</text>')
        parts.append(f'<text x="{x+bw/2:.1f}" y="{height-14}" text-anchor="middle" '
                     f'class="axis-label" fill="{theme["label"]}" font-size="11.5">'
                     f'{esc(row["label"])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_donut(items, size=230, thickness=34, center_top="", center_bottom="",
              theme=None):
    """items: [{"label": str, "value": num, "color": str}] -> SVG 环形图"""
    theme = theme or LIGHT_CHART_THEME
    total = sum(max(0, float(i["value"])) for i in items) or 1.0
    r = (size - thickness) / 2
    cx = cy = size / 2
    circ = 2 * math.pi * r
    parts = [f'<svg viewBox="0 0 {size} {size}" class="donut" '
             f'xmlns="http://www.w3.org/2000/svg" role="img">']
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                 f'stroke="{theme["grid"]}" stroke-width="{thickness}"/>')
    offset = 0.0
    for it in items:
        frac = max(0.0, float(it["value"])) / total
        if frac <= 0:
            continue
        seg = frac * circ
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{it["color"]}" '
            f'stroke-width="{thickness}" stroke-dasharray="{seg:.2f} {circ-seg:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += seg
    if center_top:
        parts.append(f'<text x="{cx}" y="{cy-2}" text-anchor="middle" class="donut-num" '
                     f'fill="{theme["num"]}">{esc(center_top)}</text>')
    if center_bottom:
        parts.append(f'<text x="{cx}" y="{cy+20}" text-anchor="middle" class="donut-sub" '
                     f'fill="{theme["sub"]}">{esc(center_bottom)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def html_bars(items, max_value=None, unit="", color=None):
    """items: [{"label": str, "value": num, "note": str(optional)}] -> HTML 横向条形"""
    if max_value is None:
        max_value = max([float(i["value"]) for i in items] + [1]) or 1
    rows = []
    for i, it in enumerate(items):
        v = float(it["value"])
        pct = max(2.0, v / max_value * 100)
        c = it.get("color") or (color or BRAND_RED if i % 2 == 0 else BRAND_YELLOW)
        note = f'<span class="bar-note">{esc(it["note"])}</span>' if it.get("note") else ""
        rows.append(
            f'<div class="bar-row"><span class="bar-label">{esc(it["label"])}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{pct:.1f}%;'
            f'background:{c}"></span></span>'
            f'<span class="bar-value">{esc(it.get("display", fmt_int(v)))}'
            f'{esc(unit)}</span>{note}</div>')
    return f'<div class="bars">{"".join(rows)}</div>'


# ---------------------------------------------------------------- 数据聚合


def load_data(path: str) -> dict:
    import json
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"数据文件不存在: {path}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def all_orders(data: dict) -> list:
    return list(data.get("orders") or [])


def item_counts(data: dict):
    c = Counter()
    for o in all_orders(data):
        for it in o.get("items", []):
            c[str(it.get("name", "未知"))] += int(it.get("qty", 1) or 1)
    return c


def category_counts(data: dict):
    c = Counter()
    for o in all_orders(data):
        for it in o.get("items", []):
            c[categorize(it.get("name", ""))] += int(it.get("qty", 1) or 1)
    return c


def store_counts(data: dict):
    c = Counter()
    for o in all_orders(data):
        s = (o.get("store") or "").strip()
        if s:
            c[s] += 1
    return c


def monthly_series(data: dict):
    """-> (labels, spend_series, order_series) 按月份升序"""
    spend = defaultdict(float)
    cnt = defaultdict(int)
    for o in all_orders(data):
        k = month_key(o.get("date", ""))
        if len(k) == 7:
            spend[k] += float(o.get("total", 0) or 0)
            cnt[k] += 1
    keys = sorted(set(spend) | set(cnt))
    labels = [month_label(k) for k in keys]
    return labels, [round(spend[k], 2) for k in keys], [cnt[k] for k in keys]


def personality(summary: dict, cats: Counter, late_night: int,
                coupon_saved: float, breakfast: int) -> str:
    total = sum(cats.values()) or 1
    top_cat, top_n = (cats.most_common(1)[0] if cats else ("other", 0))
    if late_night >= 10:
        return "深夜食堂常客"
    if coupon_saved >= 200:
        return "麦麦省锦鲤"
    if breakfast >= 5:
        return "清晨自律人"
    if top_cat == "burger" and top_n / total >= 0.4:
        return "堡族战神"
    if top_cat == "fries" and top_n / total >= 0.25:
        return "薯条永动机"
    if top_cat == "drink" and top_n / total >= 0.3:
        return "液体面包品鉴师"
    if top_cat in ("chicken", "dessert") and top_n / total >= 0.3:
        return "快乐炸鸡收藏家"
    if top_cat == "combo":
        return "分享型干饭人"
    return "麦门全勤生"


def quarterly_persona(cats: Counter) -> str:
    """季度粒度口味人格：阈值比年度更灵敏，用于进化时间线。"""
    total = sum(cats.values()) or 1
    top = cats.most_common(2)
    t1, n1 = top[0] if top else ("other", 0)
    t2, n2 = top[1] if len(top) > 1 else ("other", 0)
    s1, s2 = n1 / total, n2 / total
    if t1 == "drink" and s1 >= 0.25:
        return "液体面包品鉴师"
    if t1 == "burger" and s1 >= 0.25:
        return "堡族战神"
    if t1 in ("chicken", "dessert") and s1 >= 0.25:
        return "快乐炸鸡收藏家"
    if t1 == "fries" and s1 >= 0.18:
        return "薯条永动机"
    if t1 == "breakfast" and s1 >= 0.12:
        return "清晨自律人"
    if s1 + s2 >= 0.45 and {t1, t2} <= {"chicken", "dessert"}:
        return "甜辣双修信徒"
    return "麦门全勤生"


# ---------------------------------------------------------------- 页面骨架

BASE_CSS = f"""
:root{{
  --red:{BRAND_RED}; --dark-red:{BRAND_DARK_RED}; --yellow:{BRAND_YELLOW};
  --cream:{BRAND_CREAM}; --paper:{BRAND_PAPER}; --ink:{INK}; --ink-soft:{INK_SOFT};
}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{font-family:{FONT_STACK};background:var(--paper);color:var(--ink);
-webkit-font-smoothing:antialiased;overflow-x:hidden}}
img{{max-width:100%;display:block}}
.pxf{{font-family:'Press Start 2P',ui-monospace,Consolas,monospace}}
.wrap{{max-width:880px;margin:0 auto;padding:0 16px 60px;position:relative;z-index:1}}
.bg-decor{{position:fixed;inset:0;z-index:0;pointer-events:none}}

/* ---- 页面头部 ---- */
.page-head{{text-align:center;padding:44px 0 10px;position:relative}}
.page-head .kicker{{display:inline-block;font-size:11px;letter-spacing:.3em;
color:#fff;background:var(--red);padding:6px 14px;border:3px solid var(--ink);
box-shadow:4px 4px 0 var(--ink);margin-bottom:16px;font-weight:700}}
.page-head h1{{font-size:34px;font-weight:900;letter-spacing:.02em;
text-shadow:3px 3px 0 var(--yellow),6px 6px 0 var(--ink);line-height:1.3}}
.page-head .sub{{margin-top:16px;font-size:14px;color:var(--ink-soft);font-weight:600}}

/* ---- 贴纸卡（硬阴影，去玻璃拟态） ---- */
.card{{background:#fff;border:3px solid var(--ink);border-radius:14px;
padding:22px;margin:16px 0;box-shadow:6px 6px 0 var(--ink);position:relative}}
.card-yellow{{background:var(--yellow)}}
.card-red{{background:var(--red);color:#fff}}
.card-red .bar-label,.card-red .ch-sub{{color:#FFE9D6}}
.card-cream{{background:var(--cream)}}

/* ---- 章节标题 ---- */
.ch-no{{display:inline-block;font-size:11px;letter-spacing:.25em;color:#fff;
background:var(--red);border:3px solid var(--ink);padding:5px 12px;
box-shadow:3px 3px 0 var(--ink);font-weight:800;margin-bottom:14px}}
.ch-title{{font-size:28px;font-weight:900;line-height:1.35;margin-bottom:8px;
text-shadow:2px 2px 0 var(--yellow)}}
.ch-title .hl{{color:var(--red);text-shadow:2px 2px 0 var(--ink)}}
.ch-sub{{font-size:14px;color:var(--ink-soft);margin-bottom:20px;line-height:1.85;
font-weight:500}}

/* ---- 数据块 ---- */
.stat-row{{display:flex;flex-wrap:wrap;gap:14px;margin:14px 0}}
.stat{{flex:1;min-width:132px;background:var(--cream);border:3px solid var(--ink);
border-radius:12px;padding:16px 12px;text-align:center;box-shadow:4px 4px 0 var(--ink)}}
.stat .num{{font-size:22px;font-weight:800;color:var(--red);
font-family:'Press Start 2P',ui-monospace,monospace;line-height:1.5;
word-break:break-all}}
.stat .lbl{{font-size:12.5px;color:var(--ink-soft);margin-top:8px;font-weight:700}}
.big-quote{{font-size:23px;font-weight:900;line-height:1.75;margin:6px 0}}
.big-quote .hl{{color:var(--red);text-shadow:1px 1px 0 var(--yellow)}}

/* ---- 排行榜 ---- */
.rank-row{{display:flex;align-items:center;gap:14px;padding:12px 4px;
border-bottom:3px dotted rgba(43,20,8,.14)}}
.rank-row:last-child{{border-bottom:none}}
.rank-no{{width:36px;height:36px;flex:none;border-radius:10px;display:flex;
align-items:center;justify-content:center;font-weight:800;font-size:14px;
background:var(--yellow);color:var(--ink);border:3px solid var(--ink);
font-family:'Press Start 2P',monospace}}
.rank-body{{flex:1;min-width:0}}
.rank-name{{font-size:16px;font-weight:800;white-space:nowrap;overflow:hidden;
text-overflow:ellipsis}}
.rank-meta{{font-size:12px;color:var(--ink-soft);margin-top:3px;font-weight:600}}
.rank-num{{font-size:14px;font-weight:800;color:var(--red);
font-family:'Press Start 2P',monospace}}

/* ---- 条形图 ---- */
.bars{{display:flex;flex-direction:column;gap:10px}}
.bar-row{{display:flex;align-items:center;gap:10px;font-size:14px}}
.bar-label{{width:96px;flex:none;color:var(--ink-soft);text-align:right;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:700}}
.bar-track{{flex:1;height:16px;background:rgba(43,20,8,.07);
border:2px solid var(--ink);border-radius:99px;overflow:hidden}}
.bar-fill{{display:block;height:100%;border-right:2px solid var(--ink)}}
.bar-value{{width:88px;flex:none;font-weight:800;font-variant-numeric:tabular-nums;
font-family:'Press Start 2P',monospace;font-size:11px}}
.bar-note{{font-size:12px;color:var(--ink-soft);font-weight:600}}

/* ---- 图表 ---- */
.chart{{width:100%;height:auto;display:block}}
.axis-label{{font-size:11px;font-weight:600}}
.donut-num{{font-size:24px;font-weight:800;font-family:'Press Start 2P',monospace}}
.donut-sub{{font-size:12px;font-weight:600}}
.legend{{display:flex;flex-wrap:wrap;gap:10px 18px;justify-content:center;
margin-top:12px;font-size:13px;color:var(--ink-soft);font-weight:700}}
.legend i{{display:inline-block;width:11px;height:11px;border:2px solid var(--ink);
margin-right:6px;vertical-align:-1px}}

/* ---- 麦当劳元素 ---- */
.awning{{height:18px;border-top:3px solid var(--ink);border-bottom:3px solid var(--ink)}}
.checker{{height:16px;border-top:3px solid var(--ink);border-bottom:3px solid var(--ink)}}
.loveit{{display:inline-flex;align-items:center;gap:10px;background:var(--yellow);
border:3px solid var(--ink);box-shadow:4px 4px 0 var(--ink);padding:6px 14px;
border-radius:99px}}
.loveit-m{{font-family:'Press Start 2P',monospace;font-weight:800;color:var(--red);
font-size:15px}}
.loveit-t{{font-size:12px;font-weight:900;letter-spacing:.18em;color:var(--ink)}}
.sprite{{image-rendering:pixelated;height:auto}}
.px-icon{{image-rendering:pixelated;width:44px;height:auto;flex:none}}
.polaroid{{background:#fff;border:3px solid var(--ink);border-radius:6px;
padding:10px 10px 6px;box-shadow:6px 6px 0 var(--ink);display:inline-block}}
.polaroid-img{{border:2px solid var(--ink);overflow:hidden;background:#fff}}
.polaroid-img .photo{{width:100%;height:auto}}
.polaroid figcaption{{font-size:13px;font-weight:800;text-align:center;
padding:8px 4px 4px;color:var(--ink)}}
.stamp{{display:inline-flex;align-items:center;justify-content:center;
border:3px dashed var(--stamp-color);color:var(--stamp-color);border-radius:50%;
font-weight:900;letter-spacing:.1em;transform:rotate(-14deg);opacity:.85;
text-align:center;line-height:1.25;padding:6px;flex:none}}
.parade{{display:flex;justify-content:center;align-items:flex-end;gap:6px;
flex-wrap:wrap}}
.parade-item{{height:74px;width:auto;filter:drop-shadow(3px 3px 0 rgba(43,20,8,.35));
animation:bob 2.4s ease-in-out infinite}}
.parade-item:nth-child(2n){{animation-delay:.4s}}
.parade-item:nth-child(3n){{animation-delay:.8s}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-7px)}}}}
.scanlines{{position:absolute;inset:0;pointer-events:none;opacity:.5;
background:repeating-linear-gradient(0deg,rgba(0,0,0,.10) 0 1px,transparent 1px 4px)}}
.tag{{display:inline-block;font-size:13px;font-weight:800;padding:7px 13px;
border-radius:99px;background:var(--cream);color:var(--ink);
border:3px solid var(--ink);box-shadow:3px 3px 0 var(--ink);margin:4px 6px 4px 0}}
.tag-red{{background:var(--red);color:#fff}}
.tag-yellow{{background:var(--yellow)}}

/* ---- 页脚 ---- */
.footer{{text-align:center;margin-top:44px;font-size:12px;color:var(--ink-soft);
line-height:2;font-weight:600}}
.footer .fx{{font-family:'Press Start 2P',monospace;color:var(--red);
letter-spacing:.2em;font-size:10px;display:block;margin-bottom:8px}}

/* ---- 滚动显现 ---- */
.reveal{{opacity:0;transform:translateY(18px);transition:all .6s cubic-bezier(.2,.7,.3,1)}}
.reveal.on{{opacity:1;transform:none}}
@media print{{ .reveal{{opacity:1;transform:none}} }}
"""

REVEAL_JS = """
<script>
document.addEventListener('DOMContentLoaded',function(){
  var io=new IntersectionObserver(function(es){es.forEach(function(e){
    if(e.isIntersecting){e.target.classList.add('on');io.unobserve(e.target);}});},
    {threshold:.10});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
});
</script>
"""


def page_shell(title: str, body: str, extra_css: str = "",
               theme_bg: str = BRAND_PAPER, decor: str = "") -> str:
    """decor: 固定背景装饰层 HTML（金拱门纹理/像素精灵等）。"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>{pixel_font_css()}
{BASE_CSS}
{extra_css}</style>
</head>
<body>
{decor}
{body}
{REVEAL_JS}
</body>
</html>"""


def footer_note(data: dict, extra: str = "") -> str:
    meta = data.get("meta") or {}
    src = meta.get("data_source", "mcd-mcp")
    alias = esc(meta.get("user_alias", "麦门信徒"))
    return (f'<div class="footer"><span class="fx">MCD TIME MACHINE</span>'
            f'由「麦麦时光机」生成 · 数据来源：{esc(src)} · {alias} 的专属回忆<br>{extra}'
            f'餐品信息以麦当劳官方渠道实时结果为准 · 本项目为参赛作品，非麦当劳官方产品</div>')
