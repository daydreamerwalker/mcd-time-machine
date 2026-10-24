# -*- coding: utf-8 -*-
"""麦当劳视觉素材库：纯 SVG 像素画 + CSS 图案。
全部为代码生成的原创矢量图形（金拱门造型、像素餐品图标、雨棚条纹、
棋盘格、条码、彩带、像素分隔条等），不依赖任何外部图片。
"""
from common import esc

# ---------------------------------------------------------------- 像素图标

_ICON_PALETTE = {
    "B": "#D88A2B", "s": "#F6E7C8", "L": "#7CB342", "C": "#FFC72C",
    "P": "#7A4A21", "R": "#DA291C", "W": "#FFFFFF", "K": "#2B1408",
    "Y": "#FFC72C", "G": "#9E9E9E", "O": "#F49B3C", "M": "#C62828",
    "T": "#8D5A2B", "E": "#F5C169", "V": "#B3452E",
}

_ICONS = {
    "burger": [
        "....BBBBBB....",
        "...BssssssB...",
        "..BssBssBssB..",
        ".BBBBBBBBBBBB.",
        ".LLLLLLLLLLLL.",
        ".CCCCCCCCCCCC.",
        ".PPPPPPPPPPPP.",
        ".BBBBBBBBBBBB.",
        "..BBBBBBBBBB..",
    ],
    "fries": [
        "..Y.Y.Y.Y.Y...",
        ".Y.Y.Y.Y.Y.Y..",
        "..Y.Y.Y.Y.Y...",
        ".RRRRRRRRRRRR.",
        ".RWWWWWWWWWWR.",
        ".RWKKKKKKKWWR.",
        ".RWKKKKKKKWWR.",
        ".RRRRRRRRRRRR.",
        "..RRRRRRRRRR..",
    ],
    "drink": [
        "....WWWWWW....",
        "...WKKKKKKW...",
        "...WKKKKKKW...",
        "..RRRRRRRRRR..",
        "..RWWWWWWWWR..",
        "..RWWRRRRWWR..",
        "..RWWRRRRWWR..",
        "..RWWRRRRWWR..",
        "..RRRRRRRRRR..",
    ],
    "dessert": [
        ".....WWWW.....",
        "....WYYYYW....",
        "...WYYYYYYW...",
        "..WWWWWWWWWW..",
        "..WYYYYYYYYW..",
        "...WWWWWWWW...",
        "....TTTTTT....",
        ".....TTTT.....",
        "......TT......",
    ],
    "chicken": [
        "....OOOOOO....",
        "..OOYYYYYYOO..",
        ".OYYYYYYYYYYO.",
        "OYYYEYYYYYEYYO",
        "OYYYYYYYYYYYYO",
        ".OYYYYYYYYYYO.",
        "..OOYYYYYYOO..",
        "....OOOOOO....",
    ],
    "breakfast": [
        "..WWWWWWWWWW..",
        "..WEEEEEEEEW..",
        "..WEYYYYYYEW..",
        "..WWWWWWWWWW..",
        "...TTTTTTTT...",
        "...TTTTTTTT...",
        "....TTTTTT....",
    ],
    "combo": [
        "..RRRRRRRRRR..",
        "..RYYYYYYYYR..",
        "..RYKKKKKKYR..",
        "..RRRRRRRRRR..",
        "...RRRRRRRR...",
        "...RYYYYYYR...",
        "...RRRRRRRR...",
    ],
    "other": [
        ".....YY.......",
        ".....YY.......",
        "....YYYY......",
        "YYYYYYYYYYYYYY",
        "....YYYY......",
        ".....YY.......",
        ".....YY.......",
    ],
}

CAT_ICON_KEY = {
    "burger": "burger", "fries": "fries", "drink": "drink", "dessert": "dessert",
    "chicken": "chicken", "breakfast": "breakfast", "combo": "combo",
    "other": "other",
}


def pixel_icon(cat: str, scale: int = 5) -> str:
    """分类像素图标 -> SVG 字符串（透明背景）。"""
    rows = _ICONS.get(CAT_ICON_KEY.get(cat, "other"), _ICONS["other"])
    h = len(rows)
    w = max(len(r) for r in rows)
    rects = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = _ICON_PALETTE.get(ch)
            if color:
                rects.append(f'<rect x="{x*scale}" y="{y*scale}" width="{scale}" '
                             f'height="{scale}" fill="{color}"/>')
    return (f'<svg viewBox="0 0 {w*scale} {h*scale}" class="px-icon" '
            f'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'{"".join(rects)}</svg>')


# ---------------------------------------------------------------- 金拱门

def arches_svg(color: str = "#FFC72C", width: int = 100, opacity: float = 1.0) -> str:
    """金拱门 M 造型（粗描边路径，原创矢量近似）。"""
    return (f'<svg viewBox="0 0 100 96" width="{width}" class="arches" '
            f'xmlns="http://www.w3.org/2000/svg" aria-label="M" '
            f'style="opacity:{opacity}">'
            f'<path d="M12,96 V52 A19,19 0 0 1 50,52 V66 V52 '
            f'A19,19 0 0 1 88,52 V96" fill="none" stroke="{color}" '
            f'stroke-width="17" stroke-linejoin="miter" '
            f'stroke-linecap="butt"/></svg>')


def arches_pattern_svg(color: str = "#FFC72C", opacity: float = 0.06) -> str:
    """背景用重复金拱门纹理（绝对定位铺满）。"""
    cell = 190
    cols, rows = 8, 10
    cells = []
    for r in range(rows):
        for c in range(cols):
            x = c * cell + (cell // 2 if r % 2 else 0)
            y = r * cell
            cells.append(f'<g transform="translate({x},{y}) scale(1.15)" '
                         f'opacity="{opacity}">'
                         f'<path d="M12,96 V52 A19,19 0 0 1 50,52 V66 V52 '
                         f'A19,19 0 0 1 88,52 V96" fill="none" stroke="{color}" '
                         f'stroke-width="17"/></g>')
    return (f'<svg viewBox="0 0 {cols*cell} {rows*cell}" preserveAspectRatio="xMidYMid slice" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none">'
            f'{"".join(cells)}</svg>')


# ---------------------------------------------------------------- CSS 图案

def awning_css(colors=("#DA291C", "#FFC72C"), size=26, angle=45) -> str:
    """雨棚斜纹：repeating-linear-gradient。"""
    c1, c2 = colors
    return (f"repeating-linear-gradient({angle}deg, {c1} 0 {size//2}px, "
            f"{c2} {size//2}px {size}px)")


def checker_css(cell=28, c1="#F6EFE2", c2="#2B1408") -> str:
    """麦当劳经典棋格地面。"""
    return (f"conic-gradient({c1} 25%, {c2} 25% 50%, {c1} 50% 75%, {c2} 75%) "
            f"0 0/{cell}px {cell}px")


def barcode_css(color="#2B1408", h=34) -> str:
    """小票条码（不规则条纹）。"""
    return (f"repeating-linear-gradient(90deg, {color} 0 2px, transparent 2px 5px, "
            f"{color} 5px 6px, transparent 6px 11px, {color} 11px 14px, "
            f"transparent 14px 17px) center/{100}% {h}px no-repeat")


def pixel_divider_svg(n=24, px=8, colors=("#DA291C", "#FFC72C")) -> str:
    """红黄像素方块分隔条。"""
    rects = []
    for i in range(n):
        rects.append(f'<rect x="{i*px}" y="0" width="{px}" height="{px}" '
                     f'fill="{colors[i % 2]}"/>')
    return (f'<svg viewBox="0 0 {n*px} {px}" class="px-divider" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:{px}px;display:block">{"".join(rects)}</svg>')


def confetti_svg(seed_colors=("#DA291C", "#FFC72C", "#FFFFFF", "#7CB342")) -> str:
    """节日彩带像素（固定伪随机布局，保证可复现）。"""
    import random
    rng = random.Random(1024)
    rects = []
    for _ in range(60):
        x, y = rng.randint(0, 96), rng.randint(0, 30)
        s = rng.choice([1, 1, 2])
        rects.append(f'<rect x="{x*10}" y="{y*10}" width="{s*10}" height="{s*10}" '
                     f'fill="{rng.choice(seed_colors)}" opacity="{rng.uniform(.5, 1):.2f}"/>')
    return (f'<svg viewBox="0 0 960 300" preserveAspectRatio="xMidYMid slice" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none">'
            f'{"".join(rects)}</svg>')


def moon_svg(color="#FFD97A") -> str:
    """深夜月亮 + 星星像素。"""
    rects = []
    moon = ["..XX..", ".XXXX.", "XXXXXX", "XXXXXX", ".XXXX.", "..XX.."]
    for y, row in enumerate(moon):
        for x, ch in enumerate(row):
            if ch == "X":
                rects.append(f'<rect x="{x*8}" y="{y*8}" width="8" height="8" fill="{color}"/>')
    for sx, sy in [(58, 6), (64, 18), (52, 24), (68, 34)]:
        rects.append(f'<rect x="{sx*8}" y="{sy*8}" width="8" height="8" fill="#FFFFFF"/>')
    return (f'<svg viewBox="0 0 620 320" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:100%">{"".join(rects)}</svg>')


# ---------------------------------------------------------------- 组合装饰

def sprite_parade(sprites: list, cls="") -> str:
    """一排像素精灵（封面游行）。"""
    from common import sprite_tag
    return f'<div class="parade {cls}">' + "".join(
        sprite_tag(s, cls="parade-item") for s in sprites) + "</div>"


def stamp(text: str, color="#DA291C", size=86) -> str:
    """圆形邮戳（已打卡/DAY 1）。"""
    return (f'<span class="stamp" style="--stamp-color:{color};width:{size}px;'
            f'height:{size}px;font-size:{max(10, size//6)}px">{esc(text)}</span>')


def love_it_banner(cls="") -> str:
    """I'M LOVIN' IT 像素横幅。"""
    return (f'<div class="loveit {cls}"><span class="loveit-m">M</span>'
            f'<span class="loveit-t">I\'M LOVIN\' IT</span></div>')


def bg_decor(arches_color="#DA291C", arches_opacity=0.055,
             sprites=("px-fries.png", "px-burger.png", "px-cola.png", "px-clown.png"),
             sprite_opacity=0.13) -> str:
    """固定背景装饰层：金拱门纹理 + 四角像素精灵（低透明度）。"""
    from common import sprite_tag
    corners = [
        ("left:-46px;top:12%;width:170px;transform:rotate(-8deg)"),
        ("right:-40px;top:6%;width:150px;transform:rotate(10deg)"),
        ("left:-30px;bottom:6%;width:190px;transform:rotate(6deg)"),
        ("right:-52px;bottom:14%;width:160px;transform:rotate(-6deg)"),
    ]
    imgs = "".join(
        sprite_tag(name, cls="bg-sprite",
                   style=f"position:absolute;{pos};opacity:{sprite_opacity}")
        for name, pos in zip(sprites, corners) if name)
    return (f'<div class="bg-decor" aria-hidden="true">'
            f'{arches_pattern_svg(arches_color, arches_opacity)}{imgs}</div>')
