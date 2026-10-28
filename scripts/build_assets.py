"""Copy Pressure Racing designs from D:\\Pressure into assets/, as web-sized PNGs.

Originals are only read, never written. Run from the repo root:
    py scripts/build_assets.py
"""
import os
from PIL import Image, ImageSequence

SRC = r"D:\Pressure"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

PACK = r"Pressure Racing\Pressure Racing Logo Pack"
LOGOSS = r"Pressure Racing\Pressure Racing LLC\Pressure Logoss"
STORE = r"pressureracing (2)\pressureracing\pressureracing\storefront\public\brand"
WEB = r"Website Pictures New"

# (output path, source path, max long edge)
ASSETS = [
    # primary marks
    ("logos/pr-monogram-pink.png", rf"{PACK}\PR_logo_outline_blackwhitepink.png", 512),
    ("logos/pr-monogram-white.png", rf"{PACK}\PR_logo_outline_white.png", 512),
    ("logos/pr-monogram-black.png", rf"{LOGOSS}\PR Logo (Outline)\PR_logo.png", 512),
    ("logos/pr-wordmark-pink.png", rf"{PACK}\PressureRacing_logo_outline_blackwhitepink.png", 900),
    ("logos/pr-wordmark-white.png", rf"{PACK}\PressureRacing_logo_white.png", 900),
    ("logos/pr-wordmark-black.png", rf"{LOGOSS}\Pressure Racing OG Logo (Outline)\PR_logType pink star.png", 900),
    ("logos/pr-circle-white.png", r"Final Logo\Square Logo\Square Logo.png", 432),
    ("logos/pr-circle-black.png", r"Final Logo\Square Logo\Square Logo Black.png", 432),
    ("logos/pr-lockup-white.png", r"Final Logo\Deccal\Decal White.png", 864),
    ("logos/pr-lockup-black.png", r"Final Logo\Deccal\Decal Black.png", 864),
    ("logos/pr-crosshair-pink.png", rf"{LOGOSS}\CrossHair\Cross Hair New 3.0.png", 512),
    ("logos/pr-crosshair-black.png", rf"{LOGOSS}\CrossHair\Cross Hair Decal New.png", 512),
    ("logos/pr-factory-white.png", rf"{STORE}\pressure-factory-racing.png", 900),
    ("logos/pr-factory-black.png", r"Decal Designs New\Pressure Racing Factory\Factory.png", 900),
    ("logos/pr-worldwide-white.png", r"Decal Designs New\WorldWide 2\WorldWide_2.png", 512),
    ("logos/pr-worldwide-black.png", rf"{LOGOSS}\PR WorldWide\PressureWorld 2.png", 512),
    ("logos/pr-star-pink.png", rf"{LOGOSS}\PR Logo\star rounded.png", 128),
    # decal artwork (transparent)
    ("decals/cursive-pressure-white.png", r"Decal Designs New\Cursive Pressure! 2\Cursive_2.png", 900),
    ("decals/dah-bih-gah-white.png", r"Decal Designs New\Dah Bih Gah!\dahbihgah_stacked.png", 600),
    ("decals/larp-white.png", r"Decal Designs New\larp\larp.png", 600),
    ("decals/low-cortisol-white.png", r"Decal Designs New\Low Cortisol\low_cortisol.png", 600),
    ("decals/worldwide-bubble-white.png", r"Decal Designs New\WorldWide Bubble\WorldWide_Bubble.png", 600),
    ("decals/flame-black.png", r"Decal Designs New\Pressure Racing Flame\Flame.png", 900),
    ("decals/collegiate-black.png", r"Decal Designs New\Collegiate Banner\CollegiateBanner.png", 900),
    ("decals/gothic-black.png", r"Decal Designs New\Gothic Banner\Gothic.png", 900),
    ("decals/russian-pink.png", r"Decal Designs New\Russian\Russian_Pink.png", 900),
    ("decals/jack-o-lantern.png", r"Decal Designs New\Jack o Lantern\Jack o Lantern.png", 600),
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
    ("merch/mystery-box.png", rf"{WEB}\Mystery Boxes\Stage 1.png", 800),
    ("merch/check-engine-3-inch.png", rf"{WEB}\CEL 3 Inch\Yellow.png", 800),
]

MAX_BYTES = 500 * 1024


def save_png(im, path):
    """Save as optimized PNG; fall back to a 256-colour palette if still over budget."""
    im.save(path, optimize=True)
    if os.path.getsize(path) > MAX_BYTES:
        q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        q.save(path, optimize=True)


def build_static():
    for rel, src, edge in ASSETS:
        dst = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with Image.open(os.path.join(SRC, src)) as im:
            im = im.convert("RGBA")
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
CHALK = (242, 240, 236)


def build_dark_variants():
    """Dark-mode copies: near-black linework becomes chalk so it reads on GitHub's dark theme."""
    for src, dst in [("logos/pr-crosshair-pink.png", "logos/pr-crosshair-pink-dark.png")]:
        im = Image.open(os.path.join(OUT, src)).convert("RGBA")
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a and max(r, g, b) < 90:
                    px[x, y] = CHALK + (a,)
        save_png(im, os.path.join(OUT, dst))
        print(f"{dst:42s} (dark variant)")


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
    build_dark_variants()
    # 2 of 3 frames at 420px lands ~900 KB, safely under GitHub's 1 MB avatar cap
    build_avatar(size=420, step=1.5, colors=48)
