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

# labels on the big map
def lab(ax, W, H, lon, lat, text, dx, dy, ha="left"):
    x, y = ee_fwd(np.array(float(lon)), np.array(float(lat)))
    yt = ee_fwd(np.array(0.), np.array(84.))[1]; yb = ee_fwd(np.array(0.), np.array(-60.))[1]
    X = (x + XM) / (2 * XM) * W; Y = (yt - y) / (yt - yb) * H
    ax.annotate(text, xy=(X, Y), xytext=(X + dx, Y + dy), family=MONO, fontsize=9.5, color=FG, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=FG, lw=.7), bbox=dict(facecolor=BG2, edgecolor="none", alpha=.85, pad=1.4))
H0, W0 = big.shape[:2]
lab(ax, W0, H0, 22, 63, "Baltic Shield: 86% Precambrian", 330, -40)
lab(ax, W0, H0, -88, 60, "Canadian Shield", -420, 60)
lab(ax, W0, H0, 39, 9, "East African Rift lavas", 260, 40)
lab(ax, W0, H0, -19, 64.8, "Iceland: young lava", -150, 130, "right")
lab(ax, W0, H0, 119, -23, "Pilbara and Yilgarn:\n3 billion years", -420, 120, "right")
lab(ax, W0, H0, 87, 29, "Himalaya", 120, -160)

# period key strip
kx = fig.add_axes([0.04, 0.475, 0.92, 0.03]); kx.set_axis_off(); kx.set_xlim(0, 1); kx.set_ylim(0, 1)
shares = R["world_period_share"]; tot = sum(shares[p[0]] for p in PERIODS)
x = 0
for p in reversed(PERIODS):
    w = shares[p[0]] / tot
    kx.add_patch(Rectangle((x, 0), w, 1, facecolor=p[4], edgecolor=BG2, lw=1.2))
    if w > 0.03: kx.text(x + w / 2, 0.5, p[1] if w > 0.075 else p[0], ha="center", va="center", family=MONO, fontsize=8.5, color=FG)
    x += w
fig.text(0.04, 0.513, "SHARE OF THE WORLD'S DATED LAND BY PERIOD, OLDEST ON THE LEFT", family=MONO, fontsize=10, color=MUT)

# four eras
eras = [(3, "PRECAMBRIAN", "older than 539 million years", "PC"), (2, "PALAEOZOIC", "539 to 252 million years", "PZ"),
        (1, "MESOZOIC", "252 to 66 million years", "MZ"), (0, "CENOZOIC", "the last 66 million years", "CZ")]
pos = [(0.04, 0.27), (0.36, 0.27), (0.04, 0.10), (0.36, 0.10)]
for (ei, name, sub, ek), (x0, y0) in zip(eras, pos):
    a = fig.add_axes([x0, y0, 0.3, 0.14]); a.imshow(render(900, "era", ei), interpolation="lanczos"); a.set_axis_off()
    fig.text(x0 + 0.005, y0 + 0.148, f"{name}  {R['world_era_share'][ek]:.0f}%", family=MONO, fontsize=10.5, color=FG, fontweight="medium")
    fig.text(x0 + 0.005, y0 + 0.141, sub, family=SER, fontsize=10, color=MUT, va="top")

# shields bar chart
bx = fig.add_axes([0.73, 0.175, 0.24, 0.215])
items = sorted([(k.replace(" (Norway, Sweden, Finland)", "").replace("Fennoscandia", "Scandinavia and Finland").replace(" (Macrostrat)", "").replace(" (continent)", ""), v)
                for k, v in R["shields"].items()], key=lambda t: t[1])
bx.barh(range(len(items)), [v for _, v in items], color=[PCOL["A"] if v >= 40 else "#E8A0C0" for _, v in items], height=.7)
bx.set_yticks(range(len(items))); bx.set_yticklabels([n for n, _ in items], fontsize=10.5)
for i, (_, v) in enumerate(items): bx.text(v + 1.5, i, f"{v:.0f}%", va="center", family=MONO, fontsize=9.5, color=FG)
bx.set_xlim(0, 100); bx.set_xticks([]); bx.spines["bottom"].set_visible(False); bx.spines["left"].set_visible(False); bx.tick_params(length=0)
fig.text(0.68, 0.405, "HOW MUCH OF EACH PLACE IS\nPRECAMBRIAN ROCK", family=MONO, fontsize=10, color=MUT, va="bottom", linespacing=1.3)

# big numbers
fig.text(0.68, 0.335 + 0.10, "", fontsize=1)
notes = [(f"{R['world_era_share']['PC']:.1f}%", "of the world's dated land is\nolder than 539 million years"),
         (f"{R['young_volcanic']['quaternary_km2']/1000:.0f}k km²", "of lava and ash younger than\n2.6 million years")]
for (bigs, small), y in zip(notes, [0.135, 0.085]):
    fig.text(0.68, y + 0.02, bigs, fontproperties=DISP, fontsize=24, color=ACC, va="top")
    fig.text(0.84, y + 0.016, small, family=SER, fontsize=10.5, color=FG, va="top", linespacing=1.25)

fig.text(0.04, 0.012, "Data: Macrostrat world geological map (carto tiles, zoom 4), compiled from regional maps of North America, Europe, Africa, Australia, the Arctic\n"
         "and a generalised geology of the world (CC BY 4.0); AWS Terrain Tiles for shading. Shares are of dated, ice-free land. Equal Earth projection.\n"
         "Analysis and chart: Tristan Hotham, with Python, NumPy and matplotlib. Interactive map: maps.tristanhotham.com/rocks-beneath", family=MONO, fontsize=8.6, color=MUT, linespacing=1.4)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rocks_beneath_world.png"), dpi=200)
print("ok")
