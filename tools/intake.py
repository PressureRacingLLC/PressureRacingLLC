"""PR intake animation: a spinning compressor wheel pulls the PR logo in, boosts, and spits it back out.

Original artwork, drawn from assets/logos/pr-monogram-white.png. Run from the repo root:
    py tools/intake.py            -> assets/animations/pr-intake.gif
    py tools/intake.py --preview  -> also writes a contact sheet of sample frames

Tweak the TIMELINE / LOOK constants below; everything else follows from them.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "assets", "logos", "pr-monogram-white.png")
OUT = os.path.join(ROOT, "assets", "animations", "pr-intake.gif")

# --- canvas / timing ---------------------------------------------------------
W, H = 800, 330
FPS = 25                      # GIF stores delays in 10ms steps, so 25fps = 40ms exactly
SECONDS = 3.2
FRAMES = round(FPS * SECONDS)
SS = 2                        # supersampling for the vector parts
COLORS = 96                   # shared palette size

# --- look --------------------------------------------------------------------
INK = (10, 11, 15)
GROUND = (22, 25, 35)
PLATE = (42, 47, 62)
PLATE_HI = (58, 65, 82)
FLARE = (248, 0, 224)
CHALK = (242, 240, 236)
DIM = (168, 175, 196)
CX, CY = W / 2, H / 2
WHEEL_R = 100                 # compressor wheel radius
BLADES = 7                    # full blades (plus as many splitters)
LOGO_H = 190                  # logo height at rest
STREAKS = 34

# --- timeline (fractions of the loop) ----------------------------------------
IDLE, SUCK, BOOST, POP = 0.16, 0.56, 0.68, 0.84


def clamp(x):
    return max(0.0, min(1.0, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back_out(x, s=2.2):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


def state(t):
    """Logo scale, swirl (radians), wheel speed and flash strength at loop time t in [0, 1)."""
    if t < IDLE:
        return dict(scale=1.0, swirl=0.0, speed=0.35, flash=0.0)
    if t < SUCK:
        p = (t - IDLE) / (SUCK - IDLE)
        e = p ** 2.1
        return dict(scale=1 - e, swirl=6.0 * e, speed=0.35 + 1.9 * smooth(p), flash=0.0)
    if t < BOOST:
        p = (t - SUCK) / (BOOST - SUCK)
        return dict(scale=0.0, swirl=0.0, speed=2.25, flash=math.sin(math.pi * p), boost=p)
    if t < POP:
        p = (t - BOOST) / (POP - BOOST)
        return dict(scale=back_out(p), swirl=-1.4 * (1 - smooth(p)), speed=2.25 - 1.6 * smooth(p), flash=0.0)
    p = (t - POP) / (1 - POP)
    return dict(scale=1.0, swirl=0.0, speed=0.65 - 0.3 * smooth(p), flash=0.0)


def wheel_angles():
    """Integrate wheel speed, then scale so one loop is a whole number of blade pitches (seamless)."""
    raw, a = [], 0.0
    for i in range(FRAMES):
        raw.append(a)
        a += state(i / FRAMES)["speed"] * 0.11
    pitch = 2 * math.pi / BLADES
    k = a / (round(a / pitch) * pitch)
    return [x / k for x in raw]


# --- static layers ------------------------------------------------------------

def backdrop():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - CX) / (W * 0.55)) ** 2 + ((y - CY) / (H * 0.9)) ** 2)
    t = np.clip(1 - d, 0, 1)[..., None]
    img = np.array(INK) * (1 - t) + np.array(GROUND) * t
    bg = Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(bg, "RGBA")
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=PLATE + (34,))
    for y in range(0, H, 40):
        d.line([(0, y), (W, y)], fill=PLATE + (34,))
    # compressor housing: shroud rings and the volute scroll
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    g = ImageDraw.Draw(big)
    c = (CX * SS, CY * SS)
    for r, w, col in [(WHEEL_R + 10, 5, PLATE_HI), (WHEEL_R + 22, 2, PLATE), (WHEEL_R + 54, 2, PLATE)]:
        g.ellipse([c[0] - r * SS, c[1] - r * SS, c[0] + r * SS, c[1] + r * SS], outline=col + (255,), width=w * SS)
    pts = []
    for i in range(121):
        a = -math.pi / 2 + i / 120 * 2 * math.pi
        r = WHEEL_R + 24 + 26 * i / 120
        pts.append((c[0] + math.cos(a) * r * SS, c[1] + math.sin(a) * r * SS))
    g.line(pts, fill=PLATE_HI + (255,), width=3 * SS, joint="curve")
    bg.alpha_composite(big.resize((W, H), Image.Resampling.LANCZOS))
    return bg


def load_logo():
    im = Image.open(LOGO).convert("RGBA")
    return im.resize((round(im.width * LOGO_H / im.height), LOGO_H), Image.Resampling.LANCZOS)


# --- per-frame layers ---------------------------------------------------------

def draw_wheel(g, angle, speed):
    c = (CX * SS, CY * SS)
    hub = 26

    def blade(base, start, thick, col):
        left, right = [], []
        for i in range(13):
            r = start + (WHEEL_R - start) * i / 12
            sweep = base + 0.95 * ((r - hub) / (WHEEL_R - hub)) ** 1.3  # backswept blade
            dt = thick * (1 - 0.55 * i / 12) / r
            left.append((c[0] + math.cos(sweep - dt) * r * SS, c[1] + math.sin(sweep - dt) * r * SS))
            right.append((c[0] + math.cos(sweep + dt) * r * SS, c[1] + math.sin(sweep + dt) * r * SS))
        g.polygon(left + right[::-1], fill=col)

    ghosts = [(0.0, 255)] + ([(-0.07, 90), (-0.14, 45)] if speed > 1.2 else [])
    pitch = 2 * math.pi / BLADES
    for off, alpha in ghosts[::-1]:
        for k in range(BLADES):
            blade(angle + off + k * pitch, hub, 7, PLATE_HI + (alpha,))
            blade(angle + off + k * pitch + pitch / 2, 58, 5, PLATE + (alpha,))
    r = hub * SS
    g.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=DIM + (255,))
    r = 10 * SS
    g.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=INK + (255,))
    r = 4 * SS
    g.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=FLARE + (255,))


def streak_seeds():
    rnd = random.Random(42)
    return [(rnd.random(), rnd.random() * 2 * math.pi, rnd.choice([1, 1, 2]), i % 3 == 0) for i in range(STREAKS)]


def draw_streaks(g, t, intensity, seeds):
    """Air spiralling into the inducer. Each streak loops a whole number of times per cycle."""
    rmax, rmin = W * 0.62, WHEEL_R * 0.45
    for phase, a0, laps, pink in seeds:
        u = (phase + t * laps) % 1.0
        pts = []
        for j in range(8):
            v = max(0.0, u - j * 0.018 * (0.6 + intensity))
            r = rmin + (rmax - rmin) * (1 - v) ** 1.6
            a = a0 + 3.2 * v
            pts.append((CX * SS + math.cos(a) * r * SS, CY * SS + math.sin(a) * r * 0.62 * SS))
        fade = math.sin(math.pi * u)
        alpha = int(255 * fade * (0.25 + 0.75 * intensity))
        col = (FLARE if pink else CHALK) + (alpha,)
        g.line(pts, fill=col, width=(3 if pink else 2) * SS, joint="curve")


def swirl(logo_layer, amount):
    """Twist the logo around the centre; strongest in the middle, none at the edge."""
    if abs(amount) < 1e-3:
        return logo_layer
    arr = np.asarray(logo_layer, dtype=np.float32)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = x - CX, y - CY
    r = np.sqrt(dx * dx + dy * dy)
    R = LOGO_H * 0.75
    k = np.clip(1 - r / R, 0, 1) ** 2 * amount
    cos, sin = np.cos(k), np.sin(k)
    sx = CX + dx * cos - dy * sin
    sy = CY + dx * sin + dy * cos
    x0 = np.clip(np.floor(sx).astype(int), 0, W - 2)
    y0 = np.clip(np.floor(sy).astype(int), 0, H - 2)
    fx = np.clip(sx - x0, 0, 1)[..., None]
    fy = np.clip(sy - y0, 0, 1)[..., None]
    out = (arr[y0, x0] * (1 - fx) * (1 - fy) + arr[y0, x0 + 1] * fx * (1 - fy)
           + arr[y0 + 1, x0] * (1 - fx) * fy + arr[y0 + 1, x0 + 1] * fx * fy)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def logo_layer(logo, s):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if s <= 0.01:
        return layer
    w, h = max(1, round(logo.width * s)), max(1, round(logo.height * s))
    layer.alpha_composite(logo.resize((w, h), Image.Resampling.LANCZOS), (round(CX - w / 2), round(CY - h / 2)))
    return layer


def glow_of(layer, strength):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * strength))
    g = Image.new("RGBA", layer.size, FLARE + (0,))
    g.putalpha(a)
    return g


_YX = np.mgrid[0:H, 0:W].astype(np.float32)
_R = np.sqrt((_YX[1] - CX) ** 2 + (_YX[0] - CY) ** 2)
_A = np.arctan2(_YX[0] - CY, _YX[1] - CX)


def flash_layer(f, p):
    """Boost: a white-hot core, a magenta shockwave and radial spikes. f = strength, p = progress."""
    if f <= 0:
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))
    core = np.exp(-(_R / (26 + 70 * f)) ** 2) * f
    ring_r = 40 + 330 * p
    ring = np.exp(-((_R - ring_r) / 7) ** 2) * (1 - p)
    spikes = (np.cos(_A * 14) ** 24) * np.exp(-(_R / (90 + 160 * p))) * f * np.clip((_R - 30) / 40, 0, 1)
    rgb = np.zeros((H, W, 3), np.float32)
    a = np.clip(core + ring + spikes * 0.8, 0, 1)
    for i in range(3):
        rgb[..., i] = (CHALK[i] * core + FLARE[i] * ring + FLARE[i] * spikes * 0.8) / np.maximum(core + ring + spikes * 0.8, 1e-4)
    out = np.dstack([rgb, a * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def render():
    bg = backdrop()
    logo = load_logo()
    seeds = streak_seeds()
    angles = wheel_angles()
    frames = []
    for i in range(FRAMES):
        t = i / FRAMES
        st = state(t)
        frame = bg.copy()
        vec = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        g = ImageDraw.Draw(vec)
        intensity = clamp((st["speed"] - 0.35) / 1.9)
        draw_streaks(g, t, intensity, seeds)
        draw_wheel(g, angles[i], st["speed"])
        frame.alpha_composite(vec.resize((W, H), Image.Resampling.LANCZOS))
        lay = swirl(logo_layer(logo, st["scale"]), st["swirl"])
        frame.alpha_composite(glow_of(lay, 0.35))
        frame.alpha_composite(lay)
        frame.alpha_composite(flash_layer(st["flash"], st.get("boost", 0.0)))
        frames.append(frame.convert("RGB"))
    return frames


def save(frames):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sample = frames[:: max(1, len(frames) // 10)]
    strip = Image.new("RGB", (W, H * len(sample)))
    for i, s in enumerate(sample):
        strip.paste(s, (0, i * H))
    pal = strip.quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(OUT, save_all=True, append_images=q[1:], duration=round(1000 / FPS), loop=0, optimize=True, disposal=1)
    print(f"{os.path.relpath(OUT, ROOT)}: {W}x{H}, {len(q)} frames @ {FPS}fps, {os.path.getsize(OUT) / 1024:.0f} KB")


def preview(frames, path):
    picks = [0, int(FRAMES * 0.3), int(FRAMES * 0.45), int(FRAMES * 0.53), int(FRAMES * 0.6),
             int(FRAMES * 0.7), int(FRAMES * 0.76), int(FRAMES * 0.9)]
    tw, th = W // 2, H // 2
    sheet = Image.new("RGB", (tw * 2, th * 4), INK)
    for k, i in enumerate(picks):
        sheet.paste(frames[i].resize((tw, th), Image.Resampling.LANCZOS), ((k % 2) * tw, (k // 2) * th))
    sheet.save(path)
    print("preview:", path)


if __name__ == "__main__":
    fr = render()
    save(fr)
    if "--preview" in sys.argv:
        preview(fr, sys.argv[sys.argv.index("--preview") + 1] if len(sys.argv) > sys.argv.index("--preview") + 1
                else os.path.join(ROOT, "intake-preview.png"))
