"""Copy Pressure Racing designs from D:\\Pressure into assets/, as web-sized PNGs.

Originals are only read, never written. Run from the repo root:
    py scripts/build_assets.py

Excluded on purpose: the circle "PR" mark and every file that contains it
(Final Logo\\Square Logo, Final Logo\\Deccal, Pressure Racing-01 lockups).
"""
import io
import os
import urllib.request
from PIL import Image, ImageDraw, ImageSequence

SRC = r"D:\Pressure"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

PACK = r"Pressure Racing\Pressure Racing Logo Pack"
LOGOSS = r"Pressure Racing\Pressure Racing LLC\Pressure Logoss"
STORE = r"pressureracing (2)\pressureracing\pressureracing\storefront\public\brand"
WEB = r"Website Pictures New"

# How a source is turned white: None = already white, "fill" = every opaque pixel white,
# "invert" = black linework white while keeping two-tone detail.
# (output path, source path, max long edge, whitening)
ASSETS = [
    # primary marks, all white
    ("logos/pr-monogram-white.png", rf"{LOGOSS}\PR Logo\PR_star_white.png", 512, "fill"),
    ("logos/pr-monogram-outline-white.png", rf"{PACK}\PR_logo_outline_white.png", 512, None),
    ("logos/pr-wordmark-white.png", rf"{PACK}\PressureRacing_logo_white.png", 900, None),
    ("logos/pr-crosshair-white.png", rf"{LOGOSS}\CrossHair\Cross Hair New 3.0.png", 512, "fill"),
    ("logos/pr-factory-white.png", rf"{STORE}\pressure-factory-racing.png", 900, None),
    ("logos/pr-worldwide-white.png", r"Decal Designs New\WorldWide 2\WorldWide_2.png", 512, None),
    ("logos/pr-star-pink.png", rf"{LOGOSS}\PR Logo\star rounded.png", 128, None),  # accent glyph, not a logo
    # decal artwork (transparent), all white
    ("decals/cursive-pressure-white.png", r"Decal Designs New\Cursive Pressure! 2\Cursive_2.png", 900, None),
    ("decals/dah-bih-gah-white.png", r"Decal Designs New\Dah Bih Gah!\dahbihgah_stacked.png", 600, None),
    ("decals/larp-white.png", r"Decal Designs New\larp\larp.png", 600, None),
    ("decals/low-cortisol-white.png", r"Decal Designs New\Low Cortisol\low_cortisol.png", 600, None),
    ("decals/worldwide-bubble-white.png", r"Decal Designs New\WorldWide Bubble\WorldWide_Bubble.png", 600, None),
    ("decals/flame-white.png", r"Decal Designs New\Pressure Racing Flame\Flame.png", 900, "invert"),
    ("decals/collegiate-white.png", r"Decal Designs New\Collegiate Banner\CollegiateBanner.png", 900, "invert"),
    ("decals/gothic-white.png", r"Decal Designs New\Gothic Banner\Gothic.png", 900, "invert"),
    ("decals/russian-white.png", r"Decal Designs New\Russian\Russian_White.png", 900, None),
    # product shots, as listed on the store
    ("merch/pr-12-inch.png", rf"{WEB}\PR 12 Inch\Black.png", 800),
    ("merch/pr-12-inch-chrome.png", rf"{WEB}\PR 12 Inch Chrome\Chrome.png", 800),
    ("merch/crosshair-20-inch.png", rf"{WEB}\CrossHair 20 Inch\Black.png", 800),
    ("merch/worldwide-12-inch.png", rf"{WEB}\WorldWide 12 Inch\Black + Black Stars.png", 800),
    ("merch/flame-7-inch.png", rf"{WEB}\Flame 7 Inch\All.png", 800),
    ("merch/factory-7-inch.png", rf"{WEB}\Factory 7 Inch\All.png", 800),
    ("merch/collegiate-30-inch.png", rf"{WEB}\Collegiate Banner 30 Inch\All.png", 800),
    ("merch/gothic-30-inch.png", rf"{WEB}\Gothic Banner 30 Inch\All.png", 800),
    ("merch/dah-bih-gah-7-inch.png", rf"{WEB}\DahBihGah! 7 Inch\All.png", 800),
    ("merch/larp.png", rf"{WEB}\Larp!\All.png", 800),
    ("merch/low-cortisol-7-inch.png", rf"{WEB}\Low Cortisol 7 Inch\All.png", 800),
    ("merch/lighter-3-inch.png", rf"{WEB}\Lighter 3 Inch\All.png", 800),
    ("merch/russian-7-inch.png", rf"{WEB}\Russian 7\All.png", 800),
    ("merch/url-30-inch.png", rf"{WEB}\URL Decal 30 Inch\All.png", 800),
    ("merch/og-banner.png", rf"{WEB}\OG\All.png", 800),
    ("merch/decal-pack.png", rf"{WEB}\Decal Pack\Decal Pack.png", 800),
]

# Active clothing on pressureracing.com (Shopify product images), shown in "The Brand".
CDN = "https://cdn.shopify.com/s/files/1/0679/4556/2331/files/"
SHOP = [
    ("merch/halloween-tee-black.png", CDN + "Pressure_Pumpkin_Black_Tee_Product_4096px.png?v=1793010930&width=1000"),
    ("merch/flame-tee-white.png", CDN + "Pressure_Racing_White_Tee_Product_4096px.png?v=1793010930&width=1000"),
    ("merch/og-hoodie-grey-pink.png", CDN + "Pressure_Racing_Gray_Hoodie_Product_4096px.png?v=1793010240&width=1000"),
]

# README logo grid: white marks on an ink tile, so they read on GitHub's light theme too.
TILES = ["pr-monogram-white", "pr-crosshair-white", "pr-wordmark-white", "pr-worldwide-white", "pr-factory-white"]
TILE = (600, 440)  # 2x for sharp display at 300x220

MAX_BYTES = 500 * 1024


def save_png(im, path):
    """Save as optimized PNG; fall back to a 256-colour palette if still over budget."""
    im.save(path, optimize=True)
    if os.path.getsize(path) > MAX_BYTES:
        q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        q.save(path, optimize=True)


def whiten(im, how):
    if how == "fill":
        white = Image.new("RGBA", im.size, (255, 255, 255, 255))
        white.putalpha(im.getchannel("A"))
        return white
    if how == "invert":
        r, g, b, a = im.split()
        inv = Image.merge("RGB", (r, g, b)).point(lambda v: 255 - v)
        inv.putalpha(a)
        return inv
    return im


def build_static():
    for rel, src, edge, *how in ASSETS:
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with Image.open(os.path.join(SRC, src)) as im:
            im = whiten(im.convert("RGBA"), how[0] if how else None)
            bbox = im.getchannel("A").getbbox()
            if bbox and bbox != (0, 0, im.width, im.height):
                pad = max(4, int(max(im.size) * 0.01))
                bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                        min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad))
                im = im.crop(bbox)
            im.thumbnail((edge, edge), Image.Resampling.LANCZOS)
            save_png(im, dst)
        print(f"{rel:42s} {im.width}x{im.height}  {os.path.getsize(dst) // 1024} KB")


INK = (10, 11, 15)
PLATE = (42, 47, 62)


def build_shop():
    for rel, url in SHOP:
        dst = os.path.join(OUT, rel)
        with urllib.request.urlopen(url, timeout=60) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
        im.thumbnail((400, 400), Image.Resampling.LANCZOS)  # shown at 180px; 2x for retina, light on page weight
        save_png(im, dst)
        print(f"{rel:42s} {im.width}x{im.height}  {os.path.getsize(dst) // 1024} KB")


def tile_base():
    w, h = TILE
    t = Image.new("RGBA", TILE, (0, 0, 0, 0))
    ImageDraw.Draw(t).rounded_rectangle([1, 1, w - 2, h - 2], radius=28, fill=INK, outline=PLATE, width=3)
    return t


def build_tiles():
    os.makedirs(os.path.join(OUT, "logos", "tiles"), exist_ok=True)
    w, h = TILE
    for name in TILES:
        logo = Image.open(os.path.join(OUT, "logos", f"{name}.png")).convert("RGBA")
        logo.thumbnail((int(w * 0.72), int(h * 0.62)), Image.Resampling.LANCZOS)
        t = tile_base()
        t.alpha_composite(logo, ((w - logo.width) // 2, (h - logo.height) // 2))
        dst = os.path.join(OUT, "logos", "tiles", f"{name}.png")
        save_png(t, dst)
        print(f"tiles/{name}.png  {os.path.getsize(dst) // 1024} KB")


def build_avatar(size=500, logo_h=0.64, step=1, colors=128):
    """Square, ink-backed avatar GIF from the spinning PR logo, safe for a circle crop."""
    src = os.path.join(SRC, PACK, "PR_Spinning.gif")
    dst = os.path.join(OUT, "avatar", "pr-avatar-spin.gif")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with Image.open(src) as im:
        frames = [f.convert("RGBA") for f in ImageSequence.Iterator(im)]
        dur = im.info.get("duration", 30)
    # union of the logo's bounds across the spin, so it never shifts or clips
    box = None
    for f in frames:
        b = f.getchannel("A").getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    scale = size * logo_h / (box[3] - box[1])
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    out = []
    # step may be fractional (1.5 = keep 2 of every 3 frames) to trade smoothness for size
    picks = [frames[round(i * step)] for i in range(int(len(frames) / step))]
    for f in picks:
        f = f.resize((round(f.width * scale), round(f.height * scale)), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", (size, size), INK + (255,))
        bg.alpha_composite(f, (round(size / 2 - cx * scale), round(size / 2 - cy * scale)))
        out.append(bg.convert("RGB"))
    # one shared palette keeps the loop flicker-free and the file small
    sample = out[:: max(1, len(out) // 8)]
    strip = Image.new("RGB", (size, size * len(sample)))
    for i, s in enumerate(sample):
        strip.paste(s, (0, i * size))
    pal = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    q = [o.quantize(palette=pal, dither=Image.Dither.NONE) for o in out]
    ms = round(dur * len(frames) / len(q), -1)  # GIF delays are stored in 10ms units
    q[0].save(dst, save_all=True, append_images=q[1:], duration=ms, loop=0, optimize=True, disposal=1)
    print(f"avatar: {size}px, {len(q)} frames @ {ms}ms  {os.path.getsize(dst) // 1024} KB")
    return dst


if __name__ == "__main__":
    build_static()
    build_shop()
    build_tiles()
    # 2 of 3 frames at 420px lands ~900 KB, safely under GitHub's 1 MB avatar cap
    build_avatar(size=420, step=1.5, colors=48)
