"""Reddit collage: reddit/rocks_beneath.png (2400 by 3000). Run from reddit/: python3 collage.py"""
import os, sys, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figlib import *
from matplotlib.patches import Rectangle

BG2 = "#F7F3EA"; ACC = "#B8432A"
plt.rcParams.update({"savefig.facecolor": BG2, "figure.facecolor": BG2, "axes.facecolor": BG2})
fig = plt.figure(figsize=(12, 15), dpi=200)
fig.text(0.04, 0.968, "What lies beneath Britain?", fontproperties=DISP, fontsize=48, color=FG, va="top")
fig.text(0.04, 0.913, "Every bedrock unit of the British and Irish geological surveys' national maps, in colours\nsampled from the classic 1969 Geological Map of the British Islands. Plus the world.",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.35)

# big map
bed, sup, hill, x0, y0, z = load_uk("full")
ax = fig.add_axes([0.0, 0.29, 0.6, 0.6])
mapax(ax, uk_rgba(bed, hill, "c69", k=.5), x0, y0, z)
xa, ya = merc(-10.7, 60.95, z); xb, yb = merc(2.0, 49.85, z)
ax.set_xlim(xa, xb); ax.set_ylim(yb, ya)
for nm, lon, lat, dx, dy, ha in (("Lewisian gneiss\n3,200 million years", -6.6, 58.0, -60, -260, "center"), ("London Clay\n55 million years", -0.1, 51.5, 60, 230, "left"),
                                  ("Coal Measures", -1.45, 53.5, 300, -40, "left"), ("Chalk", 0.6, 52.65, 200, -60, "left")):
    x, y = merc(lon, lat, z)
    ax.annotate(nm, xy=(x, y), xytext=(x + dx, y + dy), family=MONO, fontsize=10, color=FG, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=FG, lw=.8), bbox=dict(facecolor=BG2, edgecolor="none", alpha=.8, pad=1.5))

# key strip
keys = ["NQ", "PG", "CH", "WE", "OL", "LI", "KE", "BU", "ML", "CM", "MG", "CL", "OR2", "SI", "OD", "TO", "DU", "MO", "LW", "VT", "IA"]
lab = {c[0]: c[1] for c in C1969}
short = {"NQ": "Pliocene, Pleistocene", "PG": "Palaeogene", "OL": "Oolite", "LI": "Lias", "KE": "Keuper Marl", "BU": "Bunter Sandstone", "OR2": "Old Red Sandstone",
         "TO": "Torridonian", "DU": "Dalradian", "VT": "Tertiary lavas", "IA": "Granites", "MG": "Millstone Grit", "CL": "Carboniferous Limestone"}
kx = fig.add_axes([0.6, 0.555, 0.38, 0.3]); kx.set_axis_off(); kx.set_xlim(0, 1); kx.set_ylim(0, len(keys))
kx.text(0, len(keys) + 0.3, "THE 1969 COLOURS, YOUNGEST FIRST", family=MONO, fontsize=10, color=MUT)
for i, k in enumerate(keys):
    y = len(keys) - 1 - i
    kx.add_patch(Rectangle((0, y + 0.12), 0.09, 0.76, facecolor=C69COL[k], edgecolor="#00000030", lw=.5))
    kx.text(0.12, y + 0.5, short.get(k, lab[k]), fontsize=11, color=FG, va="center")
    kx.text(1, y + 0.5, f"{R['uk_1969_share']['isles'][k]:.1f}%", family=MONO, fontsize=10, color=MUT, va="center", ha="right")

# big numbers
tx = fig.add_axes([0.6, 0.29, 0.38, 0.25]); tx.set_axis_off()
notes = [(f"{R['uk_top']['period_pct']:.1f}%", "of Great Britain is Carboniferous,\nmore than any other period"),
         (f"{R['coal']['ratio_towns_to_land']:.1f}×", f"Coal Measures cover {R['coal']['gb_pct']:.1f}% of the land\nbut carry {R['coal']['os_towns_on_cm_pct']:.1f}% of its towns"),
         (f"{R['superficial']['gb_pct']:.0f}%", f"of Great Britain lies under ice-age\ndeposits; till alone is {R['superficial']['pct_till']:.0f}%")]
for (big, small), y in zip(notes, [1.0, 0.64, 0.28]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=30, color=ACC, va="top", transform=tx.transAxes)
    tx.text(0.42, y - 0.02, small, family=SER, fontsize=12, color=FG, va="top", transform=tx.transAxes, linespacing=1.25)

# transect
rows = list(csv.DictReader(open(os.path.join(DATA, "transect_lakes_london.csv"), encoding="utf-8")))
km = float(rows[-1]["km"])
a = fig.add_axes([0.07, 0.075, 0.5, 0.15])
for r in rows:
    if r["max_age_ma"] in ("", "nan"):
        continue
    a.add_patch(Rectangle((float(r["km"]), 20), 1.02, float(r["max_age_ma"]) - 20, facecolor=C69COL[r["class_1969"]], edgecolor="none"))
a.set_yscale("log"); a.set_ylim(20, 1000); a.set_xlim(0, km)
a.set_yticks([30, 100, 300]); a.set_yticklabels(["30", "100", "300"], family=MONO, fontsize=10)
a.set_xticks([0, 100, 200, 300]); a.set_xticklabels(["0", "100", "200", "300 km"], family=MONO, fontsize=10)
a.minorticks_off()
a.text(0, 1.36, "THE LAYER CAKE", transform=a.transAxes, family=MONO, fontsize=10, color=MUT)
a.text(0, 1.06, f"Age of the rock (million years) every km from Scafell Pike to London.\nRank correlation {R['transect']['lakes_london']['rho']:.2f}".replace("-", "−"),
       transform=a.transAxes, family=SER, fontsize=11.5, color=FG, va="bottom")

# world
key, hw = load_world()
w = fig.add_axes([0.6, 0.06, 0.39, 0.19])
mapax(w, world_rgba(key, hw, "c69", k=.4), 0, 0, 3)
_, yt = merc(0, 78, 3); _, ybm = merc(0, -56, 3); w.set_xlim(0, 2048); w.set_ylim(ybm, yt)
w.text(0, 1.36, "THE WORLD, SAME COLOURS", transform=w.transAxes, family=MONO, fontsize=10, color=MUT)
w.text(0, 1.04, f"{R['world_era_share']['PC']:.1f}% of dated land is Precambrian;\nScandinavia {R['shields']['Fennoscandia (Norway, Sweden, Finland)']:.0f}%, Canada {R['shields']['Canada']:.0f}%",
       transform=w.transAxes, family=SER, fontsize=11.5, color=FG, va="bottom")

fig.text(0.04, 0.012, "Data: BGS Geology 625k (DiGMapGB-625), contains British Geological Survey materials © UKRI 2026 (OGL); Geological Survey Ireland 1:500k\n"
         "(CC BY 4.0); Macrostrat (CC BY 4.0); AWS Terrain Tiles. Colours sampled from the 1969 map's index (map not reproduced). Web Mercator.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.", family=MONO, fontsize=9, color=MUT, linespacing=1.4)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rocks_beneath.png"), dpi=200)
print("ok")
