"""Drawing helpers for the header, the paper and blog figures and the Reddit collage (matplotlib).

Reads only the published files in data/: the page rasters (data/uk, data/world), the unit tables and results.json.
Fonts: FONT_DIR holding Fraunces, Source Serif 4 and IBM Plex Mono (github.com/google/fonts); otherwise defaults.
"""
import csv, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
DISP = None
if os.path.isdir(FD):
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
        if os.path.exists(os.path.join(FD, f)):
            fm.fontManager.addfont(os.path.join(FD, f))
    DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE, SEA = "#F6F2E8", "#22201C", "#68625A", "#DDD5C3", "#F6F2E8"
RED, BLUE = "#B8432A", "#04609A"
plt.rcParams.update({"font.family": SER, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.facecolor": BG, "figure.facecolor": BG, "axes.facecolor": BG})
R = json.load(open(os.path.join(DATA, "results.json")))
UK = {int(r["id"]): r for r in csv.DictReader(open(os.path.join(DATA, "units_uk.csv"), encoding="utf-8"))}
NU = max(UK) + 1
C69COL = {c[0]: c[2] for c in C1969}
PCOL = {p[0]: p[4] for p in PERIODS}
RCOL = {r[0]: r[2] for r in ROCK}
SCOL = [s[2] for s in SUPER]
UKMETA = {"z": 9}


def h2rgb(h):
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], float) / 255


AGE_STOPS = [(0.5, "#FFF6C2"), (5, "#FCE08A"), (30, "#F9B95A"), (100, "#EE8A3A"), (250, "#D9573A"), (450, "#B23B5A"), (800, "#7E3B7E"), (1600, "#4D3A84"), (3200, "#232050")]


def age_rgb(ma):
    x = math.log10(max(0.5, ma))
    for k in range(1, len(AGE_STOPS)):
        a, b = math.log10(AGE_STOPS[k - 1][0]), math.log10(AGE_STOPS[k][0])
        if x <= b or k == len(AGE_STOPS) - 1:
            f = max(0, min(1, (x - a) / (b - a)))
            return h2rgb(AGE_STOPS[k - 1][1]) * (1 - f) + h2rgb(AGE_STOPS[k][1]) * f


def uk_lut(pal):
    L = np.ones((NU, 3))
    for i, u in UK.items():
        if pal == "c69":
            L[i] = h2rgb(C69COL[u["class_1969"]])
        elif pal == "ics":
            L[i] = h2rgb(PCOL[u["period"]]) if u["period"] else h2rgb("#C8C4BC")
        elif pal == "rock":
            L[i] = h2rgb(RCOL[u["rock_type"]])
        else:
            L[i] = age_rgb(float(u["max_age_ma"])) if u["max_age_ma"] else h2rgb("#C8C4BC")
    return L


def load_uk(level="overview"):
    """Returns (bed, sup, hill, px0, py0, zoom) for the British Isles grid."""
    d = os.path.join(DATA, "uk")
    if level == "overview":
        a = np.asarray(Image.open(os.path.join(d, "overview.png"))).astype(np.int64)
        h = np.asarray(Image.open(os.path.join(d, "overview_h.jpg")).convert("L")).astype(float) / 255
        meta = json.load(open(os.path.join(d, "meta.json")))
        return a[..., 0] + a[..., 1] * 256, a[..., 2], h, meta["gx0"] / 4, meta["gy0"] / 4, 7
    # full zoom-9 mosaic from the chunks, halved to zoom 8
    files = [f for f in os.listdir(d) if f.startswith("u_")]
    xs = [int(f.split("_")[1]) for f in files]; ys = [int(f.split("_")[2].split(".")[0]) for f in files]
    x0, y0 = min(xs), min(ys); W = (max(xs) - x0 + 1) * 256; H = (max(ys) - y0 + 1) * 256
    bed = np.zeros((H, W), np.int64); sup = np.zeros((H, W), np.int64); hill = np.ones((H, W))
    for f, tx, ty in zip(files, xs, ys):
        a = np.asarray(Image.open(os.path.join(d, f))).astype(np.int64)[1::2, 1::2]
        bed[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = a[..., 0] + a[..., 1] * 256
        sup[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = a[..., 2]
        hf = os.path.join(d, f.replace("u_", "h_").replace(".png", ".jpg"))
        hill[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = np.asarray(Image.open(hf).convert("L")).astype(float) / 255
    return bed, sup, hill, x0 * 256, y0 * 256, 8


def shade(rgb, hill, k=0.5):
    f = 1 - k * (1 - hill[..., None]) * 0.9
    return np.clip(rgb * f, 0, 1)


def uk_rgba(bed, hill, pal="c69", k=0.5, sup=None, supk=0.0, bg=BG, mask=None):
    L = uk_lut(pal)
    rgb = L[np.clip(bed, 0, NU - 1)]
    if sup is not None and supk > 0:
        S = np.vstack([np.ones(3)] + [h2rgb(c) for c in SCOL])
        on = sup > 0
        rgb[on] = rgb[on] * (1 - supk) + S[sup[on]] * supk
    rgb = shade(rgb, hill, k)
    a = (bed > 0).astype(float)
    if mask is not None:
        rgb[~mask & (bed > 0)] = rgb[~mask & (bed > 0)] * 0.15 + h2rgb("#DCD6CA") * 0.85
    return np.dstack([rgb, a])


def merc(lon, lat, z):
    return lonlat_to_px(lon, lat, z)


def mapax(ax, rgba, x0, y0, z, pad=0):
    h, w = rgba.shape[:2]
    ax.imshow(rgba, extent=(x0, x0 + w, y0 + h, y0), interpolation="nearest")
    ax.set_xlim(x0 - pad, x0 + w + pad); ax.set_ylim(y0 + h + pad, y0 - pad)
    ax.set_axis_off(); ax.set_aspect("equal")


def load_world():
    d = os.path.join(DATA, "world")
    a = np.asarray(Image.open(os.path.join(d, "overview.png"))).astype(np.int64)
    h = np.asarray(Image.open(os.path.join(d, "overview_h.jpg")).convert("L")).astype(float) / 255
    return a[..., 0] + a[..., 1] * 256, h


WU = None


def world_lut(pal):
    global WU
    if WU is None:
        WU = json.load(open(os.path.join(DATA, "units_world_page.json"), encoding="utf-8"))
    n = len(WU["n"]) + 1
    L = np.ones((n, 3))
    for i in range(n - 1):
        if WU["i"][i]:
            L[i + 1] = h2rgb("#ECF1F4"); continue
        if pal == "c69":
            L[i + 1] = h2rgb(C1969[WU["c"][i]][2])
        elif pal == "ics":
            L[i + 1] = h2rgb(PERIODS[WU["p"][i]][4]) if WU["p"][i] >= 0 else h2rgb("#C8C4BC")
        elif pal == "rock":
            L[i + 1] = h2rgb(ROCK[WU["r"][i]][2])
        else:
            L[i + 1] = age_rgb(WU["x"][i]) if WU["x"][i] is not None else h2rgb("#C8C4BC")
    return L


def world_rgba(key, hill, pal="ics", k=0.45):
    L = world_lut(pal)
    rgb = shade(L[key], hill, k)
    return np.dstack([rgb, (key > 0).astype(float)])


def note(fig, x, y, s, size=10, color=MUT, **kw):
    fig.text(x, y, s, family=MONO, fontsize=size, color=color, **kw)
