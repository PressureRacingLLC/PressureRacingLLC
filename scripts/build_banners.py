"""Header and footer banners, composited from the logo PNGs in assets/logos.

Run after build_assets.py:
    py scripts/build_banners.py
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageSequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
FONTS = r"D:\Pressure\Game Files\helicopter-pressure\node_modules\@fontsource-variable"

# pressureracing.com tokens
INK = (10, 11, 15)
GROUND = (22, 25, 35)
PLATE = (42, 47, 62)
FLARE = (248, 0, 224)
CHALK = (242, 240, 236)
CHALK_DIM = (168, 175, 196)


def font(name, size, weight):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    f.set_variation_by_name(weight)
    return f


def logo(rel, height=None, width=None):
    im = Image.open(os.path.join(A, rel)).convert("RGBA")
    if height:
        return im.resize((round(im.width * height / im.height), height), Image.Resampling.LANCZOS)
    return im.resize((width, round(im.height * width / im.width)), Image.Resampling.LANCZOS)


def tracked(draw, xy, text, f, fill, track):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + track
    return x


def tracked_width(draw, text, f, track):
    return sum(draw.textlength(ch, font=f) for ch in text) + track * (len(text) - 1)


def backdrop(w, h, seed):
    """Ink-to-ground fade, a faint telemetry grid and diagonal speed lines."""
    bg = Image.new("RGB", (w, h), INK)
    px = bg.load()
    for y in range(h):
        for x in range(0, w):
            t = (x / w) * 0.55 + (y / h) * 0.45
            px[x, y] = tuple(round(INK[i] + (GROUND[i] - INK[i]) * t) for i in range(3))
    d = ImageDraw.Draw(bg, "RGBA")
    for x in range(0, w, 40):
        d.line([(x, 0), (x, h)], fill=PLATE + (38,))
    for y in range(0, h, 40):
        d.line([(0, y), (w, y)], fill=PLATE + (38,))
    rnd = random.Random(seed)
    for _ in range(18):
        x = rnd.randint(-200, w)
        ln = rnd.randint(120, 420)
        a = rnd.randint(18, 50)
        y = rnd.randint(0, h)
        d.line([(x, y), (x + ln, y - ln * 0.18)], fill=CHALK + (a,), width=rnd.choice([1, 1, 2]))
    return bg


def glow(base, center, radius, color, strength):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=color + (strength,))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius * 0.6)))


def stars(base, spots):
    star = Image.open(os.path.join(A, "logos/pr-star-pink.png")).convert("RGBA")
    for x, y, s in spots:
        st = star.resize((s, round(star.height * s / star.width)), Image.Resampling.LANCZOS)
        base.alpha_composite(st, (x - s // 2, y - st.height // 2))


def stripe(d, w, y):
    d.rectangle([0, y, w, y + 6], fill=FLARE)
    d.rectangle([0, y + 12, w, y + 13], fill=CHALK_DIM)


def header():
    w, h = 1600, 440
    im = backdrop(w, h, 7).convert("RGBA")
    glow(im, (330, 215), 230, FLARE, 70)
    mono = logo("logos/pr-monogram-pink.png", height=300)
    im.alpha_composite(mono, (330 - mono.width // 2, 70))
    word = logo("logos/pr-wordmark-white.png", width=880)
    top = 84
    im.alpha_composite(word, (600, top))
    d = ImageDraw.Draw(im)
    tag = font("archivo/files/archivo-latin-wght-normal.woff2", 34, b"Bold")
    tracked(d, (612, top + word.height + 30), "AUTOMOTIVE RACING BRAND", tag, CHALK_DIM, 7)
    meta = font("martian-mono/files/martian-mono-latin-wght-normal.woff2", 18, b"Medium")
    tracked(d, (614, top + word.height + 88), "PRESSURERACING.COM", meta, FLARE, 4)
    stars(im, [(1500, 70, 34), (1540, 118, 18), (560, 360, 22), (1450, 350, 14)])
    stripe(d, w, h - 22)
    im.convert("RGB").save(os.path.join(A, "banners/pr-header.png"), optimize=True)


def footer():
    w, h = 1600, 240
    im = backdrop(w, h, 11).convert("RGBA")
    d = ImageDraw.Draw(im)
    stripe(d, w, 8)
    glow(im, (w // 2, 120), 160, FLARE, 40)
    word = logo("logos/pr-wordmark-white.png", width=520)
    im.alpha_composite(word, ((w - word.width) // 2, 60))
    meta = font("martian-mono/files/martian-mono-latin-wght-normal.woff2", 18, b"Medium")
    line = "PRESSURERACING.COM"
    tw = tracked_width(d, line, meta, 5)
    tracked(d, ((w - tw) // 2, 60 + word.height + 30), line, meta, CHALK_DIM, 5)
    im.convert("RGB").save(os.path.join(A, "banners/pr-footer.png"), optimize=True)


def readme_spin(size=220):
    """Transparent spinning PR for the README logo grid (the avatar has an ink fill)."""
    src = r"D:\Pressure\Pressure Racing\Pressure Racing Logo Pack\PR_Spinning.gif"
    with Image.open(src) as g:
        frames = [f.convert("RGBA") for f in ImageSequence.Iterator(g)]
        dur = g.info.get("duration", 30)
    box = (148, 100, 853, 935)  # union of the logo across all frames
    scale = size * 0.92 / (box[3] - box[1])
    out = []
    for f in frames[::2]:
        f = f.resize((round(f.width * scale), round(f.height * scale)), Image.Resampling.LANCZOS)
        c = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        cx, cy = (box[0] + box[2]) / 2 * scale, (box[1] + box[3]) / 2 * scale
        c.alpha_composite(f, (round(size / 2 - cx), round(size / 2 - cy)))
        # GIF has 1-bit alpha: snap so edges stay crisp on both light and dark pages
        a = c.getchannel("A").point(lambda v: 255 if v > 110 else 0)
        c.putalpha(a)
        out.append(c)
    q = []
    for c in out:
        p = c.convert("RGB").quantize(colors=63, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pal = p.getpalette()[: 63 * 3] + [0, 0, 0]
        p.putpalette(pal)
        mask = c.getchannel("A").point(lambda v: 0 if v else 255)
        p.paste(63, mask=mask)
        q.append(p)
    dst = os.path.join(A, "logos/pr-spin.gif")
    q[0].save(dst, save_all=True, append_images=q[1:], duration=dur * 2, loop=0,
              transparency=63, disposal=2, optimize=False)
    print("pr-spin.gif", len(q), "frames", os.path.getsize(dst) // 1024, "KB")


if __name__ == "__main__":
    os.makedirs(os.path.join(A, "banners"), exist_ok=True)
    header()
    footer()
    readme_spin()
    for n in ("pr-header.png", "pr-footer.png"):
        print(n, os.path.getsize(os.path.join(A, "banners", n)) // 1024, "KB")
