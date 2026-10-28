"""Static figures for the blog (release/blog/b_*.png, 1520 px wide) and the paper (release/paper/fig_*.png).
Run: FONT_DIR=/path/to/fonts python3 code/07_figures.py
"""
import shutil
from figlib import *
from matplotlib.patches import Rectangle

BLOG = os.path.join(ROOT, "release", "blog"); PAPER = os.path.join(ROOT, "release", "paper")
os.makedirs(BLOG, exist_ok=True); os.makedirs(PAPER, exist_ok=True)
DPI = 200
W_IN = 1520 / DPI


def save(fig, name, paper=None):
    fig.savefig(os.path.join(BLOG, name), dpi=DPI)
    if paper:
        shutil.copy(os.path.join(BLOG, name), os.path.join(PAPER, paper))
    plt.close(fig)
    print(name)


bedF, supF, hillF, xF, yF, zF = load_uk("full")
xa, ya = merc(-10.7, 60.95, zF); xb, yb = merc(2.0, 49.85, zF)

# 1. the British Isles in the 1969 colours, with a key -----------------------------------------
fig = plt.figure(figsize=(W_IN, W_IN * 1.22))
ax = fig.add_axes([0.0, 0.0, 0.62, 1.0])
mapax(ax, uk_rgba(bedF, hillF, "c69", k=.5), xF, yF, zF)
ax.set_xlim(xa, xb); ax.set_ylim(yb, ya)
sh = R["uk_1969_share"]["isles"]
lx, ly = 0.6, 0.975
grp = None
for c in C1969:
    if c[0] == "XX":
        continue
    if c[3] != grp:
        grp = c[3]
        fig.text(lx, ly, {"sed": "SEDIMENTARY, YOUNGEST FIRST", "meta": "METAMORPHIC", "ign": "IGNEOUS"}[grp], family=MONO, fontsize=7.5, color=MUT, va="top")
        ly -= 0.017
    fig.patches.append(Rectangle((lx, ly - 0.0115), 0.03, 0.0115, transform=fig.transFigure, facecolor=c[2], edgecolor="#00000033", lw=.4))
    lab = c[1].replace(" (Upper Jurassic clays and limestones)", "").replace(" (Middle Jurassic)", "").replace(" (Mercia Mudstone)", "").replace(" (Sherwood Sandstone)", "")
    lab = lab.replace(" (dolerite, gabbro, serpentine)", "").replace(" (granite, diorite, felsite)", "").replace("Volcanic rocks: ", "Volcanic: ")
    fig.text(lx + 0.038, ly - 0.0058, lab, fontsize=8.2, color=FG, va="center")
    fig.text(0.985, ly - 0.0058, f"{sh[c[0]]:.1f}%", family=MONO, fontsize=7.2, color=MUT, va="center", ha="right")
    ly -= 0.0198
fig.text(lx, ly - 0.01, "Share of the land of the British Isles.\nColours sampled from the index of the\n1969 Geological Map of the British Islands.\nBGS 625k and GSI 500k bedrock.", family=MONO, fontsize=7, color=MUT, va="top", linespacing=1.4)
save(fig, "b_map1969.png", "fig_map1969.png")

# 2. four colourings -------------------------------------------------------------------------
bed, sup, hill, x0, y0, z = load_uk("overview")
xa7, ya7 = merc(-10.7, 60.95, z); xb7, yb7 = merc(2.0, 49.85, z)
fig, axs = plt.subplots(1, 4, figsize=(W_IN, W_IN * 0.47))
fig.subplots_adjust(left=0.005, right=0.995, top=0.93, bottom=0.01, wspace=0.02)
for a, (pal, t) in zip(axs, [("c69", "1969 survey"), ("ics", "Periods (ICS colours)"), ("rock", "Rock type"), ("age", "Age (oldest age)")]):
    mapax(a, uk_rgba(bed, hill, pal, k=.35), x0, y0, z)
    a.set_xlim(xa7, xb7); a.set_ylim(yb7, ya7)
    a.text(0.5, 1.03, t, transform=a.transAxes, ha="center", va="bottom", family=MONO, fontsize=10, color=FG)
save(fig, "b_palettes.png", "fig_palettes.png")

# 3. transects --------------------------------------------------------------------------------
def tr(name):
    rows = list(csv.DictReader(open(os.path.join(DATA, "transect_%s.csv" % name), encoding="utf-8")))
    return rows


fig, axs = plt.subplots(2, 1, figsize=(W_IN, W_IN * 0.62))
fig.subplots_adjust(left=0.085, right=0.985, top=0.95, bottom=0.08, hspace=0.42)
for a, (name, a0, b0) in zip(axs, [("lakes_london", "Scafell Pike", "London"), ("anglesey_london", "Holyhead", "London")]):
    rows = tr(name); km = float(rows[-1]["km"])
    for r in rows:
        if not r["max_age_ma"] or r["max_age_ma"] == "nan":
            continue
        x = float(r["km"]); v = float(r["max_age_ma"])
        a.add_patch(Rectangle((x, 20), 1.02, v - 20, facecolor=C69COL[r["class_1969"]], edgecolor="none"))
    a.set_yscale("log"); a.set_ylim(20, 3500); a.set_xlim(0, km)
    a.set_yticks([30, 100, 300, 1000, 3000]); a.set_yticklabels(["30", "100", "300", "1,000", "3,000"], family=MONO, fontsize=9)
    a.tick_params(axis="x", labelsize=9)
    for lab in a.get_xticklabels():
        lab.set_family(MONO)
    a.set_ylabel("million years", family=MONO, fontsize=9, color=MUT)
    a.text(0, 1.04, f"{a0} to {b0}, {R['transect'][name]['km']} km; rank correlation of distance and age {R['transect'][name]['rho']:.2f}".replace("-", "−"),
           transform=a.transAxes, family=MONO, fontsize=9.5, color=FG)
    a.text(1, -0.2, "km from " + a0, transform=a.transAxes, ha="right", family=MONO, fontsize=8.5, color=MUT)
    # name the big steps: the longest run of each class, if at least 8 km long
    pts = [(float(r["km"]), r["class_1969"], float(r["max_age_ma"])) for r in rows if r["max_age_ma"] not in ("", "nan")]
    runs = []
    for x, c, v in pts:
        if runs and runs[-1][0] == c and x - runs[-1][2] <= 2.5:
            runs[-1][2] = x; runs[-1][3] = max(runs[-1][3], v)
        else:
            runs.append([c, x, x, v])
    placed = []
    for key, label in (("CL", "Carboniferous\nLimestone"), ("CM", "Coal\nMeasures"), ("KE", "Mercia\nMudstone"), ("LI", "Lias"), ("OL", "Oolite"), ("CH", "Chalk"), ("PG", "London\nClay")):
        rr = [r for r in runs if r[0] == key and r[2] - r[1] >= 8]
        if not rr:
            continue
        r = max(rr, key=lambda r: r[2] - r[1]); mid = min(max((r[1] + r[2]) / 2, 0.04 * km), 0.96 * km)
        hw = max(len(t) for t in label.split("\n")) * km / 240 + 3
        nl = label.count("\n") + 1
        y = max(v for x, c, v in pts if abs(x - mid) <= hw) * 1.15
        while any(mid - hw < b and mid + hw > a_ and y < yy * 1.6 ** p and y * 1.6 ** nl > yy for a_, b, yy, p in placed):
            y *= 1.5
        placed.append((mid - hw, mid + hw, y, nl))
        a.text(mid, y, label, ha="center", va="bottom", fontsize=7.6, color=FG, family=MONO, linespacing=1.0)
save(fig, "b_transect.png", "fig_transect.png")

# 4. shares by period ---------------------------------------------------------------------------
cols = [("Great Britain", R["uk_period_share"]["gb"]), ("Ireland (island)", R["uk_period_share"]["ireland"]), ("World, dated land", R["world_period_share"])]
fig, axs = plt.subplots(1, 3, figsize=(W_IN, W_IN * 0.62), sharey=True)
fig.subplots_adjust(left=0.17, right=0.985, top=0.92, bottom=0.06, wspace=0.12)
ys = np.arange(len(PERIODS))
for a, (t, d) in zip(axs, cols):
    v = [d[p[0]] for p in PERIODS]
    a.barh(ys, v, color=[p[4] for p in PERIODS], edgecolor="#00000030", height=0.72)
    for y, x in zip(ys, v):
        if x >= 0.05:
            a.text(x + 0.8, y, f"{x:.1f}%", va="center", family=MONO, fontsize=8, color=MUT)
    a.set_title(t, family=MONO, fontsize=10, color=FG, loc="left")
    a.set_xlim(0, max(v) * 1.3); a.invert_yaxis() if a is axs[0] else None
    a.set_xticks([]); a.spines["bottom"].set_visible(False)
axs[0].set_yticks(ys); axs[0].set_yticklabels([p[1] for p in PERIODS], fontsize=9.5)
save(fig, "b_shares.png", "fig_shares.png")

# 5. coal measures and towns ----------------------------------------------------------------------
cm_ids = [i for i, u in UK.items() if u["class_1969"] == "CM"]
on = np.isin(bedF, cm_ids)
rg = uk_rgba(bedF, hillF, "c69", k=.35)
rgb = rg[..., :3].copy()
fade = (bedF > 0) & ~on
rgb[fade] = rgb[fade] * 0.25 + h2rgb("#E4DED2") * 0.75
fig = plt.figure(figsize=(W_IN, W_IN * 1.05))
ax = fig.add_axes([0, 0, 1, 1])
mapax(ax, np.dstack([rgb, rg[..., 3]]), xF, yF, zF)
xa2, ya2 = merc(-5.4, 56.3, zF); xb2, yb2 = merc(0.6, 51.2, zF)
ax.set_xlim(xa2, xb2); ax.set_ylim(yb2, ya2)
towns = list(csv.DictReader(open(os.path.join(DATA, "towns_on_coal_measures.csv"), encoding="utf-8")))
px = [merc(float(t["lon"]), float(t["lat"]), zF) for t in towns]
ax.scatter([p[0] for p in px], [p[1] for p in px], s=10, color="#111", edgecolor="white", linewidth=.5, zorder=3)
for nm in ("Sheffield", "Leeds", "Swansea", "Wigan", "Barnsley", "Wolverhampton", "Stoke-on-Trent", "Merthyr Tydfil", "Wakefield", "Newcastle upon Tyne", "Motherwell", "Wrexham"):
    t = [t for t in towns if t["name"] == nm]
    if t:
        x, y = merc(float(t[0]["lon"]), float(t[0]["lat"]), zF)
        ax.text(x + 6, y - 4, nm, family=MONO, fontsize=8, color=FG, zorder=4, bbox=dict(facecolor=BG, edgecolor="none", alpha=.75, pad=1))
ax.text(0.03, 0.47, f"Coal Measures (grey) cover\n{R['coal']['gb_pct']:.1f}% of Great Britain;\n{R['coal']['os_towns_on_cm']} of {R['coal']['os_towns']:,} OS cities\nand towns (dots) stand on them.",
        transform=ax.transAxes, family=MONO, fontsize=9, color=FG, va="bottom", bbox=dict(facecolor=BG, edgecolor=RULE, pad=5), linespacing=1.4)
save(fig, "b_coal.png", "fig_coal.png")

# 6. superficial deposits ------------------------------------------------------------------------
gsi_ids = [i for i, u in UK.items() if u["source"] == "GSI"]
gbmask = (bedF > 0) & ~np.isin(bedF, gsi_ids)
S = np.vstack([np.ones(3)] + [h2rgb(c) for c in SCOL])
rgb = np.where((supF > 0)[..., None], S[np.clip(supF, 0, len(SCOL))], h2rgb("#E9E4D9"))
rgb = shade(rgb, hillF, .35)
fig = plt.figure(figsize=(W_IN, W_IN * 1.05))
ax = fig.add_axes([0, 0, 0.6, 1])
mapax(ax, np.dstack([rgb, gbmask.astype(float)]), xF, yF, zF)
xa3, ya3 = merc(-8.3, 60.95, zF); xb3, yb3 = merc(2.0, 49.85, zF)
ax.set_xlim(xa3, xb3); ax.set_ylim(yb3, ya3)
bx = fig.add_axes([0.66, 0.3, 0.27, 0.6])
ks = sorted(SUPER, key=lambda s: -R["superficial"]["pct_" + s[0]])
vals = [R["superficial"]["pct_" + s[0]] for s in ks]
bx.barh(np.arange(len(ks)), vals, color=[s[2] for s in ks], edgecolor="#00000030")
bx.set_yticks(np.arange(len(ks))); bx.set_yticklabels([s[1].replace(" (boulder clay)", "\n(boulder clay)").replace(" of uncertain origin", "\nof uncertain origin").replace(" (shelly sands)", "") for s in ks], fontsize=8.5)
bx.invert_yaxis(); bx.set_xticks([]); bx.spines["bottom"].set_visible(False); bx.set_xlim(0, max(vals) * 1.28)
for y, v in enumerate(vals):
    bx.text(v + 0.4, y, f"{v:.1f}%", va="center", family=MONO, fontsize=8, color=MUT)
fig.text(0.5, 0.93, f"{R['superficial']['gb_pct']:.1f}% of Great Britain's mapped land\nis under superficial deposits.", family=MONO, fontsize=9, color=FG, va="bottom")
fig.text(0.5, 0.24, "Grey: bedrock at the surface, or no deposit\nat this scale. Shares are for Great Britain;\nthe map also shows Northern Ireland.", family=MONO, fontsize=8, color=MUT, va="top")
save(fig, "b_superficial.png")

# 7. the world -------------------------------------------------------------------------------------
key, hw = load_world()
rg = world_rgba(key, hw, "ics", k=.4)
fig = plt.figure(figsize=(W_IN, W_IN * 0.92))
ax = fig.add_axes([0.0, 0.33, 1.0, 0.67])
mapax(ax, rg, 0, 0, 3)
_, ytop = merc(0, 80, 3); _, ybot = merc(0, -58, 3)
ax.set_xlim(0, 2048); ax.set_ylim(ybot, ytop)
lg = fig.add_axes([0.02, 0.285, 0.96, 0.03]); lg.set_axis_off()
for k, p in enumerate(PERIODS):
    lg.add_patch(Rectangle((k / len(PERIODS), 0.35), 1 / len(PERIODS) - 0.004, 0.65, facecolor=p[4], transform=lg.transAxes))
    nm = {"Carboniferous": "Carbonif.", "Neoproterozoic": "Neoprot.", "Mesoproterozoic": "Mesoprot.", "Palaeoproterozoic": "Palaeoprot."}.get(p[1], p[1])
    lg.text((k + 0.5) / len(PERIODS), 0.0 if k % 2 == 0 else -0.75, nm, ha="center", va="top", family=MONO, fontsize=7.2, color=FG, transform=lg.transAxes)
bx = fig.add_axes([0.42, 0.025, 0.5, 0.19])
ks = sorted(R["shields"].items(), key=lambda kv: -kv[1])
bx.barh(np.arange(len(ks)), [v for _, v in ks], color="#EEB0A3", edgecolor=RED, height=.7)
bx.set_yticks(np.arange(len(ks))); bx.set_yticklabels([k.replace(" (Norway, Sweden, Finland)", "").replace(" (Macrostrat)", "") for k, _ in ks], fontsize=8)
bx.invert_yaxis(); bx.set_xlim(0, 100); bx.set_xticks([]); bx.spines["bottom"].set_visible(False)
for y, (_, v) in enumerate(ks):
    bx.text(v + 1, y, f"{v:.1f}%", va="center", family=MONO, fontsize=7.5, color=MUT)
fig.text(0.02, 0.2, "Share of each region's\ndated, ice-free land that\nis Precambrian (older\nthan 539 million years)", family=MONO, fontsize=8.5, color=FG, va="top", linespacing=1.4)
save(fig, "b_world.png", "fig_world.png")
