"""Water layer for the page: rivers and lakes.

Great Britain: OS Open Rivers watercourse links (OGL v3). Each link is given the total length of the
river network upstream of it (its own length plus everything that flows into it), worked out by
following the network's start and end nodes in the flow direction. That length sets its class:
  0: 500 km or more upstream (shown from zoom 5)   1: 100 km (zoom 6.5)   2: 25 km (zoom 8)
  3: 5 km (zoom 9.5)                               4: smaller streams (zoom 11)
Classes 0 and 1 go in data/water/gb_main.json; classes 2, 3 and 4 are split into one-degree cells
(data/water/gb<class>_<lon>_<lat>.json) that the page loads only when zoomed in on them.
Ireland, the world and lakes: Natural Earth 1:10m rivers and lake centrelines, the 1:10m European
rivers supplement, and 1:10m lakes plus the European lakes supplement (public domain), in
data/water/world_a.json (Natural Earth minimum zoom up to 4.5) and world_b.json (the rest), each feature with Natural Earth's own minimum zoom. Natural Earth rivers
inside Great Britain are dropped (OS Open Rivers is used there).

Encoding: integer 1e-4 degree coordinates, delta-coded: [class or min zoom, width, x0, y0, dx1, dy1, ...].
"""
import json, math, os, sqlite3, struct, sys
from collections import defaultdict, deque
import numpy as np
from shapely import wkb
from shapely.geometry import shape, LineString
from shapely.ops import transform as stransform
from pyproj import Transformer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

OSR = "/home/claude/hist/osrivers/Data/oprvrs_gb.gpkg"
OUT = os.path.join(DATA, "water"); os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
tr = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)


def gp_geom(b):
    flags = b[3]; env = (flags >> 1) & 7
    n = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[env]
    return wkb.loads(bytes(b[8 + n:]))


def enc(head, coords):
    q = [(int(round(x * 1e4)), int(round(y * 1e4))) for x, y in coords]
    ded = [q[0]]
    for p in q[1:]:
        if p != ded[-1]:
            ded.append(p)
    if len(ded) < 2:
        return None
    out = list(head) + [ded[0][0], ded[0][1]]
    for a, b in zip(ded[:-1], ded[1:]):
        out += [b[0] - a[0], b[1] - a[1]]
    return out


# ---------------------------------------------------------------- Great Britain: OS Open Rivers
con = sqlite3.connect(OSR)
rows = con.execute("select fid, geometry, length, form, start_node, end_node, flow_direction from watercourse_link").fetchall()
print("links", len(rows))
ln = {}; frm = {}; to = {}
for fid, g, L, form, s, e, fd in rows:
    a, b = (e, s) if fd == "in opposite direction" else (s, e)
    ln[fid] = L or 0.0; frm[fid] = a; to[fid] = b
into = defaultdict(list)          # node -> links ending there
for fid in ln:
    into[to[fid]].append(fid)
outn = defaultdict(list)          # node -> links starting there
for fid in ln:
    outn[frm[fid]].append(fid)
# upstream length by Kahn's algorithm over links (a link depends on the links that end at its start node)
need = {fid: len(into[frm[fid]]) for fid in ln}
up = {fid: ln[fid] for fid in ln}
qd = deque([f for f, k in need.items() if k == 0])
done = 0
while qd:
    f = qd.popleft(); done += 1
    for g in outn[to[f]]:
        # where a river splits, each branch inherits the full upstream length (a simplification)
        up[g] += up[f]
        need[g] -= 1
        if need[g] == 0:
            qd.append(g)
print("ordered", done, "of", len(ln), "(the rest sit in loops and keep their partial totals)")
TH = [500e3, 100e3, 25e3, 5e3]
TOL = [120, 80, 50, 30, 20]       # simplification tolerance in metres, by class
main, cells = [], defaultdict(list)
cnt = [0] * 5
for fid, g, L, form, s, e, fd in rows:
    u = up[fid]
    c = next((k for k, t in enumerate(TH) if u >= t), 4)
    geom = gp_geom(g)
    lines = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
    for line in lines:
        line = LineString([p[:2] for p in line.coords]).simplify(TOL[c])
        xs, ys = line.xy
        lon, lat = tr.transform(np.asarray(xs), np.asarray(ys))
        r = enc([c], list(zip(lon, lat)))
        if not r:
            continue
        cnt[c] += 1
        if c <= 1:
            main.append(r)
        else:
            cells[(c, math.floor(lon[0]), math.floor(lat[0]))].append(r)
print("classes", cnt)
json.dump(main, open(os.path.join(OUT, "gb_main.json"), "w"), separators=(",", ":"))
for (c, x, y), v in cells.items():
    json.dump(v, open(os.path.join(OUT, "gb%d_%d_%d.json" % (c, x, y)), "w"), separators=(",", ":"))

# ---------------------------------------------------------------- Natural Earth: Ireland, the world, lakes
G = np.load(os.path.join(SCRATCH, "uk_grid.npz"))
NAT = G["nat"]; UM = json.load(open(os.path.join(SCRATCH, "uk_meta.json")))


def in_gb(lon, lat):
    x, y = lonlat_to_px(lon, lat, UM["z"]); i, j = int(x) - UM["gx0"], int(y) - UM["gy0"]
    return 0 <= i < UM["w"] and 0 <= j < UM["h"] and NAT[j, i] in (1, 2, 3)


rivers, lakes = [], []
for fn in ("ne_10m_rivers_lake_centerlines.geojson", "ne_10m_rivers_europe.geojson"):
    for f in json.load(open(os.path.join(NE, fn)))["features"]:
        p = f["properties"]; g = shape(f["geometry"])
        mz = max(2.0, float(p.get("min_zoom") or 7) - 1)
        sr = float(p.get("scalerank") or 10)
        wdt = 3 if sr <= 2 else 2 if sr <= 5 else 1
        for line in (list(g.geoms) if g.geom_type.startswith("Multi") else [g]):
            line = line.simplify(0.004)
            mid = line.interpolate(0.5, normalized=True)
            if in_gb(mid.x, mid.y):
                continue
            r = enc([round(mz * 10), wdt], list(line.coords))
            if r:
                rivers.append(r)
for fn in ("ne_10m_lakes.geojson", "ne_10m_lakes_europe.geojson"):
    for f in json.load(open(os.path.join(NE, fn)))["features"]:
        p = f["properties"]; g = shape(f["geometry"])
        mz = max(2.0, float(p.get("min_zoom") or 7) - 1)
        for poly in (list(g.geoms) if g.geom_type.startswith("Multi") else [g]):
            poly = poly.simplify(0.003)
            if poly.is_empty or poly.area < 2e-5:
                continue
            r = enc([round(mz * 10), 0], list(poly.exterior.coords))
            if r and len(r) >= 8:
                lakes.append(r)
A = lambda L: [r for r in L if r[0] <= 45]
B = lambda L: [r for r in L if r[0] > 45]
json.dump({"rivers": A(rivers), "lakes": A(lakes)}, open(os.path.join(OUT, "world_a.json"), "w"), separators=(",", ":"))
json.dump({"rivers": B(rivers), "lakes": B(lakes)}, open(os.path.join(OUT, "world_b.json"), "w"), separators=(",", ":"))
tot = 0
for f in sorted(os.listdir(OUT)):
    tot += os.path.getsize(os.path.join(OUT, f))
big = max(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("NE rivers", len(rivers), "lakes", len(lakes), "files", len(os.listdir(OUT)), "total bytes", tot, "largest", big)
json.dump({"cells": sorted([[c, x, y] for c, x, y in cells]), "counts": cnt}, open(os.path.join(OUT, "index.json"), "w"))
