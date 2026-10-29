"""Reddit collage for the world: reddit/rocks_beneath_world.png (2400 by 3000).
Run from reddit/ with FONT_DIR set: python3 collage_world.py
Uses the world page tiles in data/world (zoom-5 pixels), reprojected to Equal Earth."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figlib import *
from matplotlib.patches import Rectangle

BG2 = "#F7F3EA"; ACC = "#B8432A"; GREY = h2rgb("#D9D3C6")
plt.rcParams.update({"savefig.facecolor": BG2, "figure.facecolor": BG2, "axes.facecolor": BG2})

# ---------- the grid ----------
D = os.path.join(DATA, "world"); N = 16 * 512
key = np.zeros((N, N), np.uint16); hill = np.ones((N, N), np.float32)
for f in os.listdir(D):
    if f.startswith("w_"):
        x, y = map(int, f[2:-4].split("_")); a = np.asarray(Image.open(os.path.join(D, f))).astype(np.uint16)
        key[y * 512:(y + 1) * 512, x * 512:(x + 1) * 512] = a[..., 0] + a[..., 1] * 256
    elif f.startswith("h_"):
        x, y = map(int, f[2:-4].split("_"))
        hill[y * 512:(y + 1) * 512, x * 512:(x + 1) * 512] = np.asarray(Image.open(os.path.join(D, f)).convert("L").resize((512, 512), Image.BILINEAR)).astype(np.float32) / 255

# ---------- Equal Earth inverse ----------
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796; M = math.sqrt(3) / 2
def ee_fwd(lon, lat):
    p = np.arcsin(M * np.sin(np.radians(lat))); p2 = p * p; p6 = p2 ** 3
    return np.radians(lon) * np.cos(p) / (M * (A1 + 3 * A2 * p2 + p6 * (7 * A3 + 9 * A4 * p2))), p * (A1 + A2 * p2 + p6 * (A3 + A4 * p2))
XM = ee_fwd(np.array(180.), np.array(0.))[0]; YM = ee_fwd(np.array(0.), np.array(90.))[1]
def ee_grid(W, lat_top=84, lat_bot=-60):
    yt = ee_fwd(np.array(0.), np.array(lat_top))[1]; yb = ee_fwd(np.array(0.), np.array(lat_bot))[1]
    H = int(round(W * (yt - yb) / (2 * XM)))
    xs = np.linspace(-XM, XM, W); ys = np.linspace(yt, yb, H)
    X, Y = np.meshgrid(xs, ys)
    p = Y.copy()
    for _ in range(12):
        p2 = p * p; p6 = p2 ** 3
        f = p * (A1 + A2 * p2 + p6 * (A3 + A4 * p2)) - Y
        fp = A1 + 3 * A2 * p2 + p6 * (7 * A3 + 9 * A4 * p2)
        p = p - f / fp
    p2 = p * p; p6 = p2 ** 3
    lat = np.degrees(np.arcsin(np.clip(np.sin(p) / M, -1, 1)))
    lon = np.degrees(X * M * (A1 + 3 * A2 * p2 + p6 * (7 * A3 + 9 * A4 * p2)) / np.cos(p))
    inside = np.abs(lon) <= 180
    lr = np.radians(np.clip(lat, -85, 85))
    px = np.clip(((lon + 180) / 360 * N).astype(int), 0, N - 1)
    py = np.clip(((1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / np.pi) / 2 * N).astype(int), 0, N - 1)
    return px, py, inside

WU = json.load(open(os.path.join(DATA, "units_world_page.json"), encoding="utf-8"))
NU = len(WU["n"]) + 1
per = np.full(NU, -1); ice = np.zeros(NU, bool)
per[1:] = WU["p"]; ice[1:] = WU["i"]
LICS = world_lut("ics")
ERA_OF = np.array([-1] + [["CZ", "MZ", "PZ", "PC"].index(PERIODS[q][5]) if q >= 0 else -1 for q in WU["p"]])

def render(W, mode="ics", era=None, k=0.55):
    px, py, inside = ee_grid(W)
    kk = key[py, px]; hh = hill[py, px]
    if mode == "ics":
        rgb = LICS[kk]
    else:
        e = ERA_OF[kk]
        rgb = np.where((e == era)[..., None], LICS[kk], GREY)
        rgb = np.where((ice[kk])[..., None], h2rgb("#ECF1F4"), rgb)
    rgb = shade(rgb, hh, k)
    land = (kk > 0) & inside
    out = np.ones(rgb.shape) * h2rgb(BG2)
    oc = h2rgb("#E6EDF0")  # ocean inside the map outline
    out[inside] = oc
    out[land] = rgb[land]
    return out

# ---------- figure ----------
fig = plt.figure(figsize=(12, 15), dpi=200)
fig.text(0.04, 0.972, "How old is the ground under your feet?", fontproperties=DISP, fontsize=38, color=FG, va="top")
fig.text(0.04, 0.925, "Every rock unit on Macrostrat's geological map of the world, coloured by the period it formed in.\nPink is older than 1.6 billion years; yellow is younger than 23 million.",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.35)

big = render(2300)
ax = fig.add_axes([0.02, 0.525, 0.96, 0.37]); ax.imshow(big, interpolation="lanczos"); ax.set_axis_off()

# labels on the big map: every label sits on open sea (or the paper outside the map), with a leader line to its place
YT = ee_fwd(np.array(0.), np.array(84.))[1]; YB = ee_fwd(np.array(0.), np.array(-60.))[1]
def topx(W, H, lon, lat):
    x, y = ee_fwd(np.array(float(lon)), np.array(float(lat)))
    return float((x + XM) / (2 * XM) * W), float((YT - y) / (YT - YB) * H)
def lab(ax, W, H, lon, lat, text, tlon, tlat, ha="left"):
    X, Y = topx(W, H, lon, lat); TX, TY = topx(W, H, tlon, tlat)
    dx, dy = X - TX, Y - TY
    rel = ((1.0 if dx > 0 else 0.0), 0.5) if abs(dx) > abs(dy) * 1.2 else (0.5, (0.0 if dy > 0 else 1.0))
    ax.annotate(text, xy=(X, Y), xytext=(TX, TY), family=MONO, fontsize=9.5, color=FG, ha=ha, va="center", linespacing=1.25,
                arrowprops=dict(arrowstyle="-", color=FG, lw=.75, shrinkA=3, shrinkB=1, relpos=rel), bbox=dict(facecolor="#E6EDF0", edgecolor="none", pad=2.5))
H0, W0 = big.shape[:2]
lab(ax, W0, H0, -82, 57, "Canadian Shield:\n52% Precambrian", -150, 32, "center")
lab(ax, W0, H0, 20, 64, "Scandinavia\nand Finland:\n86% Precambrian", -40, 34, "center")
lab(ax, W0, H0, 38, 8, "East African\nRift lavas", 73, -6, "center")
lab(ax, W0, H0, -69, -18, "The Andes", -105, -22, "center")
lab(ax, W0, H0, -58, -8, "Amazonian Craton", -17, -24, "center")
lab(ax, W0, H0, 119, -24, "Pilbara and Yilgarn:\nover 3 billion years", 82, -38, "center")

# full key: every period, its age range and its share of the land
shares = R["world_period_share"]
fig.text(0.04, 0.505, "KEY: GEOLOGICAL PERIODS (INTERNATIONAL COLOURS), WITH EACH PERIOD'S SHARE OF THE WORLD'S DATED LAND", family=MONO, fontsize=9.5, color=MUT)
kx = fig.add_axes([0.04, 0.39, 0.93, 0.11]); kx.set_axis_off(); kx.set_xlim(0, 4); kx.set_ylim(-1.0, 5)
order = list(PERIODS)  # youngest first, as in the time scale
def rng(p):
    a, b = p[2], p[3]
    f = lambda v: "today" if v == 0 else (f"{v/1000:g} bn" if v >= 1000 else f"{v:g}")
    return f"{f(a)} to {f(b)} Myr ago" if b else f"last {a:g} Myr"
for i, p in enumerate(order):
    col, row = i // 4, i % 4
    y = 4.4 - row * 1.25
    kx.add_patch(Rectangle((col + 0.0, y - 0.38), 0.11, 0.76, facecolor=p[4], edgecolor="#00000030", lw=.5))
    kx.text(col + 0.15, y + 0.2, p[1], family=SER, fontsize=11, color=FG, va="center")
    kx.text(col + 0.15, y - 0.32, rng(p), family=MONO, fontsize=8, color=MUT, va="center")
    kx.text(col + 0.93, y + 0.2, f"{shares[p[0]]:.1f}%", family=MONO, fontsize=9.5, color=FG, va="center", ha="right")
kx.add_patch(Rectangle((1.0, -0.95), 0.11, 0.5, facecolor="#ECF1F4", edgecolor="#00000030", lw=.5))
kx.text(1.15, -0.7, "Ice sheet (not dated)", family=SER, fontsize=10, color=FG, va="center")
kx.add_patch(Rectangle((0.0, -0.95), 0.11, 0.5, facecolor="#E6EDF0", edgecolor="#00000030", lw=.5))
kx.text(0.15, -0.7, "Sea", family=SER, fontsize=10, color=FG, va="center")

# four eras
eras = [(3, "PRECAMBRIAN", "older than 539 million years", "PC"), (2, "PALAEOZOIC", "539 to 252 million years", "PZ"),
        (1, "MESOZOIC", "252 to 66 million years", "MZ"), (0, "CENOZOIC", "the last 66 million years", "CZ")]
pos = [(0.04, 0.205), (0.36, 0.205), (0.04, 0.055), (0.36, 0.055)]
for (ei, name, sub, ek), (x0, y0) in zip(eras, pos):
    a = fig.add_axes([x0, y0, 0.3, 0.125]); a.imshow(render(900, "era", ei), interpolation="lanczos"); a.set_axis_off()
    fig.text(x0 + 0.005, y0 + 0.133, f"{name}  {R['world_era_share'][ek]:.0f}%", family=MONO, fontsize=10.5, color=FG, fontweight="medium")
    fig.text(x0 + 0.005, y0 + 0.127, sub, family=SER, fontsize=10, color=MUT, va="top")

# shields bar chart
bx = fig.add_axes([0.78, 0.16, 0.19, 0.18])
items = sorted([(k.replace(" (Norway, Sweden, Finland)", "").replace("Fennoscandia", "Scandinavia and Finland").replace(" (Macrostrat)", "").replace(" (continent)", ""), v)
                for k, v in R["shields"].items()], key=lambda t: t[1])
bx.barh(range(len(items)), [v for _, v in items], color=[PCOL["A"] if v >= 40 else "#E8A0C0" for _, v in items], height=.7)
bx.set_yticks(range(len(items))); bx.set_yticklabels([n for n, _ in items], fontsize=10, color=FG)
for i, (_, v) in enumerate(items): bx.text(v + 1.5, i, f"{v:.0f}%", va="center", family=MONO, fontsize=9.5, color=FG)
bx.set_xlim(0, 100); bx.set_xticks([]); bx.spines["bottom"].set_visible(False); bx.spines["left"].set_visible(False); bx.tick_params(length=0)
fig.text(0.69, 0.35, "HOW MUCH OF EACH PLACE IS\nPRECAMBRIAN ROCK", family=MONO, fontsize=10, color=MUT, va="bottom", linespacing=1.3)

# big numbers
fig.text(0.68, 0.335 + 0.10, "", fontsize=1)
notes = [(f"{R['world_era_share']['PC']:.1f}%", "of the world's dated land is\nolder than 539 million years"),
         (f"{R['young_volcanic']['quaternary_km2']/1000:.0f}k km²", "of lava and ash younger than\n2.6 million years")]
for (bigs, small), y in zip(notes, [0.125, 0.08]):
    fig.text(0.68, y + 0.02, bigs, fontproperties=DISP, fontsize=24, color=ACC, va="top")
    fig.text(0.84, y + 0.016, small, family=SER, fontsize=10.5, color=FG, va="top", linespacing=1.25)

fig.text(0.04, 0.012, "Data: Macrostrat world geological map (carto tiles, zoom 4), compiled from regional maps of North America, Europe, Africa, Australia, the Arctic\n"
         "and a generalised geology of the world (CC BY 4.0); AWS Terrain Tiles for shading. Shares are of dated, ice-free land. Equal Earth projection.\n"
         "Analysis and chart: Tristan Hotham, with Python, NumPy and matplotlib. Interactive map: maps.tristanhotham.com/rocks-beneath", family=MONO, fontsize=8.6, color=MUT, linespacing=1.4)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rocks_beneath_world.png"), dpi=200)
print("ok")
