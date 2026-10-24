# -*- coding: utf-8 -*-
"""素材预处理工具：去右下角水印、像素图抠透明背景、统一压缩尺寸。
用法: python prepare_assets.py <images_dir>
依赖: Pillow（仅开发/更新素材时需要；Skill 运行时不需要此脚本）。
水印处理原理：用左下角同高度区域水平镜像覆盖右下角（食品图背景平滑，不可见接缝）。
"""
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("需要 Pillow: pip install pillow")

SENTINEL = (255, 0, 254)  # 临时标记色（避免与素材常见色碰撞）

SPRITES = {
    "8_bit_pixel_art_sprite_of_a_cu_2026-10-24T04-45-40.png": "px-fries.png",
    "8_bit_pixel_art_sprite_of_a_cu_2026-10-24T04-45-43.png": "px-burger.png",
    "8_bit_pixel_art_sprite_of_a_cu_2026-10-24T04-45-45.png": "px-cola.png",
    "8_bit_pixel_art_sprite_of_a_fr_2026-10-24T04-45-39.png": "px-clown.png",
}
PHOTOS = {
    "professional_commercial_food_p_2026-10-24T04-45-44.png": "ph-bigmac.jpg",
    "professional_commercial_food_p_2026-10-24T04-46-29.png": "ph-fries.jpg",
    "professional_commercial_food_p_2026-10-24T04-46-32.png": "ph-cola.jpg",
    "professional_commercial_food_p_2026-10-24T04-46-27.png": "ph-sundae.jpg",
    "professional_commercial_food_p_2026-10-24T04-46-28.png": "ph-nuggets.jpg",
    "professional_architectural_pho_2026-10-24T04-46-34.png": "ph-restaurant.jpg",
}


def strip_watermark(im, fx=0.15, fy=0.055):
    w, h = im.size
    cw, ch = max(8, int(w * fx)), max(8, int(h * fy))
    x0, y0 = w - cw, h - ch
    sx0 = max(0, x0 - cw)
    sample = im.crop((sx0, y0, sx0 + cw, h)).transpose(Image.FLIP_LEFT_RIGHT)
    im.paste(sample, (x0, y0))
    return im


def sprite_to_transparent(src, dst):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    im = strip_watermark(im, 0.17, 0.08)
    seeds = [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2),
             (w // 2, 1), (w // 2, h - 2), (1, h // 2), (w - 2, h // 2),
             (w // 4, h // 4), (3 * w // 4, 3 * h // 4)]
    for s in seeds:
        try:
            ImageDraw.floodfill(im, s, SENTINEL, thresh=45)
        except Exception:
            pass
    rgba = im.convert("RGBA")
    datas = list(rgba.getdata())
    out = [(0, 0, 0, 0) if (abs(r - SENTINEL[0]) < 10 and abs(g - SENTINEL[1]) < 10
                            and abs(b - SENTINEL[2]) < 10) else (r, g, b, a)
           for (r, g, b, a) in datas]
    rgba.putdata(out)
    bbox = rgba.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    rgba.thumbnail((512, 512), Image.NEAREST)
    rgba.save(dst, optimize=True)
    return rgba.size


def photo_compress(src, dst, max_side=760):
    im = Image.open(src).convert("RGB")
    im = strip_watermark(im, 0.15, 0.055)
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    im.save(dst, "JPEG", quality=80, optimize=True, progressive=True)
    return im.size


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    for src, dst in SPRITES.items():
        p = os.path.join(d, src)
        if os.path.exists(p):
            print("sprite", dst, sprite_to_transparent(p, os.path.join(d, dst)))
            os.remove(p)
    for src, dst in PHOTOS.items():
        p = os.path.join(d, src)
        if os.path.exists(p):
            print("photo ", dst, photo_compress(p, os.path.join(d, dst)))
            os.remove(p)
    print("done")


if __name__ == "__main__":
    main()
