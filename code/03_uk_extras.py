"""British Isles: hill shading and fault and dyke lines for the page.

Hill shading: AWS Terrain Tiles (terrarium, zoom 10, about 100 m) sampled at the zoom-9 page
grid, shaded with light from the north west, then averaged to zoom 8 (one 256 by 256 JPEG per
page chunk, white is flat ground) and to zoom 7 for the overview.
Lines: BGS 625k faults and dykes, GSI/GSNI 1:500k faults and dykes, simplified to about 150 m.
"""
import gzip, json, os, sys
import numpy as np
from PIL import Image
import shapefile
from pyproj import Transformer
from shapely.geometry import shape, LineString
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa
sys.path.insert(0, "/home/claude/hist/within-sight/code")
from dem import DEM  # noqa: E402

meta = json.load(open(os.path.join(SCRATCH, "uk_meta.json")))
GX0, GY0, W, H, Z, CH = meta["gx0"], meta["gy0"], meta["w"], meta["h"], meta["z"], meta["chunk"]
_g = np.load(os.path.join(SCRATCH, "uk_grid.npz"))
land = _g["bed"] > 0
NAT = _g["nat"]
dem = DEM()
N9 = 256 * 2 ** Z
xs = GX0 + np.arange(W) + .5
E = np.zeros((H, W), np.float32)
for j0 in range(0, H, 256):
    j1 = min(H, j0 + 256)
    ys = GY0 + np.arange(j0, j1) + .5
    gx = np.broadcast_to(xs[None, :] * 2, (j1 - j0, W))          # zoom 10 pixels are half the size
    gy = np.broadcast_to(ys[:, None] * 2, (j1 - j0, W))
    E[j0:j1] = np.maximum(dem.bilinear(gx.ravel(), gy.ravel()).reshape(j1 - j0, W), 0)
print("elevation max", float(E.max()))
rows = GY0 + np.arange(H) + .5
lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * rows / N9))))
cell = 2 * np.pi * 6378137 / N9 * np.cos(np.radians(lat))
zf = 4.0
gyy = np.gradient(E, axis=0) * zf / cell[:, None]
gxx = np.gradient(E, axis=1) * zf / cell[:, None]
del E
slope = np.arctan(np.hypot(gxx, gyy)); aspect = np.arctan2(-gxx, gyy)
del gxx, gyy
alt = np.radians(45); shade = np.zeros(slope.shape, np.float32)
for az, w in ((315, .6), (270, .2), (0, .2)):
    a = np.radians(az)
    shade += w * (np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(a - aspect))
del slope, aspect
v = np.clip(shade / np.sin(alt), 0, 1) ** 1.5
del shade
HS = (25 + 230 * v).astype(np.float32)
del v
HS[~land] = 255
H8 = HS.reshape(H // 2, 2, W // 2, 2).mean(axis=(1, 3)).astype(np.uint8)
del HS
out = os.path.join(DATA, "uk")
for f in os.listdir(out):
    if f.startswith("h_"):
        os.remove(os.path.join(out, f))
tot = 0
for tx, ty in meta["chunks"]:
    cx, cy = tx - GX0 // CH, ty - GY0 // CH
    h = H8[cy * 256:(cy + 1) * 256, cx * 256:(cx + 1) * 256]
    fn = os.path.join(out, "h_%d_%d.jpg" % (tx, ty))
    Image.fromarray(h).save(fn, quality=72); tot += os.path.getsize(fn)
ov = H8.reshape(H // 4, 2, W // 4, 2).mean(axis=(1, 3)).astype(np.uint8)
Image.fromarray(ov).save(os.path.join(out, "overview_h.jpg"), quality=72)
print("hill chunks bytes", tot, "overview", os.path.getsize(os.path.join(out, "overview_h.jpg")))

# ---------------------------------------------------------------------------
lines = []


def add(kind, coords, tol=0.0015):
    ls = LineString(coords)
    if ls.length == 0:
        return
    ls = ls.simplify(tol)
    pts = [c for xy in ls.coords for c in (round(xy[1], 3), round(xy[0], 3))]
    if len(pts) >= 4:
        lines.append([kind] + pts)


B = json.load(gzip.open(BGS))
for f in B["collections"]["bgsgeology625kfaults"]:
    g = f["geometry"]; kind = 1 if "Thrust" in f["properties"].get("feature_d", "") else 0
    for part in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]):
        add(kind, part)
nd = 0
for f in B["collections"]["bgsgeology625kdykes"]:
    shp = shape(f["geometry"])
    for poly in (getattr(shp, "geoms", None) or [shp]):
        r = poly.minimum_rotated_rectangle
        cs = list(r.exterior.coords)[:4]
        if len(cs) < 4:
            continue
        # the long axis of the rectangle, through the middle
        d01 = (cs[0][0] - cs[1][0]) ** 2 + (cs[0][1] - cs[1][1]) ** 2
        d12 = (cs[1][0] - cs[2][0]) ** 2 + (cs[1][1] - cs[2][1]) ** 2
        if d01 >= d12:
            a = ((cs[0][0] + cs[3][0]) / 2, (cs[0][1] + cs[3][1]) / 2); b = ((cs[1][0] + cs[2][0]) / 2, (cs[1][1] + cs[2][1]) / 2)
        else:
            a = ((cs[0][0] + cs[1][0]) / 2, (cs[0][1] + cs[1][1]) / 2); b = ((cs[2][0] + cs[3][0]) / 2, (cs[2][1] + cs[3][1]) / 2)
        add(2, [a, b]); nd += 1
del B
itm = Transformer.from_crs("EPSG:2157", "EPSG:4326", always_xy=True)
gdir = os.path.join(SCRATCH, "gsi")
for nm, kind in (("IE_GSI_GSNI_Faults_500k_IE32_ITM_MS", 0), ("IE_GSI_GSNI_Dykes_500k_IE32_ITM_MS", 2)):
    r = shapefile.Reader(os.path.join(gdir, nm))
    for sh in r.shapes():
        pts = np.asarray(sh.points); parts = list(sh.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            lon, lat_ = itm.transform(pts[a:b, 0], pts[a:b, 1])
            # leave Northern Ireland to BGS
            px, py = lonlat_to_px(float(np.mean(lon)), float(np.mean(lat_)), Z)
            i, j = int(px) - GX0, int(py) - GY0
            if 0 <= i < W and 0 <= j < H and NAT[j, i] == 4:
                continue
            add(kind, list(zip(lon, lat_)))
json.dump(lines, open(os.path.join(DATA, "uk_lines.json"), "w"), separators=(",", ":"))
print("lines", len(lines), "dykes", nd, "bytes", os.path.getsize(os.path.join(DATA, "uk_lines.json")))
