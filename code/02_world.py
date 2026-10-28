"""The world: unit table and page rasters from the Macrostrat carto tiles at zoom 4.

Each zoom-4 vector tile is drawn at 512 by 512 pixels (the pixel size of zoom 5: about
4.9 km at the equator, 0.044 degrees of longitude). Relief comes from the AWS Terrain
Tiles (terrarium) at zoom 4, shaded and doubled to the same grid.

Writes
  data/units_world.csv             one row per distinct Macrostrat legend entry
  data/world_sources.csv           the regional maps behind the tiles, with their share of mapped land
  data/world/w_<x>_<y>.png         R + 256 G = unit, B = hill shade (255 flat)
  data/world/overview.png          the whole world at a quarter of that (zoom 3 pixels)
  data/world_lines.json            faults from the same tiles (simplified, for the map)
  scratch world_grid.npz           the full grid and a country grid for the analysis
"""
import base64, csv, gzip, io, json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw
import mapbox_vector_tile as mvt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

TZ = 4; RES = 512; EXT = 4096; NT = 2 ** TZ
S = RES / EXT
os.makedirs(os.path.join(DATA, "world"), exist_ok=True)
for f in os.listdir(os.path.join(DATA, "world")):
    os.remove(os.path.join(DATA, "world", f))

M = json.load(gzip.open(MACRO))
units, ukey, refs, refkey = [], {}, [], {}
G = np.zeros((NT * RES, NT * RES), np.uint16)
lines_out = []


def ring_area(r):
    a = np.asarray(r)
    return abs(np.dot(a[:-1, 0], a[1:, 1]) - np.dot(a[1:, 0], a[:-1, 1])) / 2 if len(a) > 2 else 0


def rock_world(lith, name):
    t = (lith or "").upper()
    nm = (name or "").upper()
    m = re.search(r"MAJOR:\{([^}]*)\}", t)
    if m:
        t = m.group(1)
    if "SEDIMENTARY AND/OR VOLCANIC" in t or "SEDIMENTARY AND VOLCANIC" in t:
        return "sd"
    # Macrostrat names such as "Sedimentary; Carbonate", "Plutonic; Felsic", "Metamorphic; Gneiss"
    if nm.startswith("PLUTONIC") or "INTRUSIVE" in nm or "GRANIT" in nm:
        return "ii"
    if nm.startswith("VOLCANIC") or "VOLCANIC" in nm.split(";")[0]:
        return "vo"
    if nm.startswith("METAMORPHIC"):
        return "mm"
    r = rock_from_text(t)
    if r != "ot":
        return r
    if "CARBONATE" in nm:
        return "ls"
    if "SILICICLASTIC" in nm or "CLASTIC" in nm:
        return "ss"
    if "UNCONSOLIDATED" in nm or "QUATERNARY" in nm:
        return "sf"
    if "SEDIMENTARY" in t or "SEDIMENTARY" in nm:
        return "sd"
    r = rock_from_text(nm)
    return r


for key, b64 in M["tiles"].items():
    z, tx, ty = map(int, key.split("/"))
    t = mvt.decode(base64.b64decode(b64), default_options={"y_coord_down": True})
    if "units" in t:
        polys = []
        for f in t["units"]["features"]:
            p = f["properties"]
            rk = (p.get("ref_title"), p.get("ref_authors"), p.get("ref_year"), p.get("source_id"))
            if rk not in refkey:
                refkey[rk] = len(refs)
                refs.append({"source_id": p.get("source_id"), "name": p.get("ref_name"), "title": clean(p.get("ref_title") or ""),
                             "authors": clean((p.get("ref_authors") or "").replace("\n", " ")), "year": p.get("ref_year"),
                             "publisher": clean(p.get("ref_source") or ""), "url": p.get("ref_url") or "", "isbn_doi": p.get("ref_isbn") or ""})
            top, bot = p.get("best_age_top"), p.get("best_age_bottom")
            k = (p.get("name"), top, bot, p.get("lith"), p.get("source_id"), p.get("b_int"), p.get("t_int"))
            if k not in ukey:
                ukey[k] = len(units) + 1
                mx = float(bot) if bot is not None else None
                mn = float(top) if top is not None else None
                if mx is not None:
                    per = period_of(mx - 1e-6) if mx >= 1000 else period_of((mx + (mn or 0)) / 2 + 1e-6)
                else:
                    per = None
                units.append({"id": ukey[k], "name": clean(p.get("name") or "").replace(" - ", ", "), "lith": clean(p.get("lith") or "").replace(" - ", ", "),
                              "age": clean(p.get("age") or "").replace(" - ", " to "), "b_int": p.get("b_int") or "", "t_int": p.get("t_int") or "",
                              "max_ma": mx, "min_ma": mn, "period": per, "rock": rock_world(p.get("lith"), p.get("name")),
                              "ref": refkey[rk], "descrip": clean((p.get("descrip") or "")).replace(" - ", ", ")[:160]})
            uid = ukey[k]
            g = f["geometry"]
            parts = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"] if g["type"] == "MultiPolygon" else []
            for rings in parts:
                polys.append((uid, [[(x * S, y * S) for x, y in r] for r in rings]))
        polys.sort(key=lambda q: -ring_area(q[1][0]))
        im = Image.new("I", (RES, RES), 0)
        d = ImageDraw.Draw(im)
        for v, rings in polys:
            if len(rings[0]) >= 3:
                d.polygon(rings[0], fill=v)
            for h in rings[1:]:
                if len(h) >= 3:
                    d.polygon(h, fill=0)
        G[ty * RES:(ty + 1) * RES, tx * RES:(tx + 1) * RES] = np.asarray(im, dtype=np.int32)
    if "lines" in t:
        for f in t["lines"]["features"]:
            ty_ = (f["properties"].get("type") or "").lower()
            if "fault" not in ty_ and "thrust" not in ty_:
                continue
            g = f["geometry"]
            parts = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"] if g["type"] == "MultiLineString" else []
            for ln in parts:
                pts = []
                for x, y in ln:
                    if -64 <= x <= EXT + 64 and -64 <= y <= EXT + 64:
                        lon, lat = px_to_lonlat((tx + x / EXT) * 256, (ty + y / EXT) * 256, TZ)
                        pts.append([round(lat, 1), round(lon, 1)])
                # thin: drop points closer than about 0.2 degrees to the previous kept point; drop short lines
                kept = []
                for q in pts:
                    if not kept or abs(q[0] - kept[-1][0]) + abs(q[1] - kept[-1][1]) >= 0.2:
                        kept.append(q)
                if len(kept) >= 2 and abs(kept[0][0] - kept[-1][0]) + abs(kept[0][1] - kept[-1][1]) >= 0.5:
                    lines_out.append([1 if "thrust" in ty_ else 0] + [c for q in kept for c in q])
print("units", len(units), "refs", len(refs), "land px", int((G > 0).sum()), "fault lines", len(lines_out))

# ---------------------------------------------------------------------------
# keep land only: Natural Earth 1:10m land, and drop lake, submarine and ocean-floor units
N5 = 256 * 2 ** (TZ + 1)


def pj(r):
    out = []
    for lon, lat_ in r:
        la = math.radians(max(-85, min(85, lat_)))
        out.append(((lon + 180) / 360 * N5, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * N5))
    return out


land = json.load(open(os.path.join(NE, "ne_10m_land.geojson")))
limg = Image.new("L", (NT * RES, NT * RES), 0); ld = ImageDraw.Draw(limg)
for f in land["features"]:
    g = f["geometry"]
    for rings in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
        ld.polygon(pj(rings[0]), fill=1)
        for h in rings[1:]:
            ld.polygon(pj(h), fill=0)
LAND = np.asarray(limg, dtype=bool)
drop = np.zeros(len(units) + 1, bool)
for u in units:
    nm = u["name"].lower()
    if "submarine" in nm or "ocean-continent" in nm or u["lith"].lower() == "lake" or (not u["name"] and not u["lith"]):
        drop[u["id"]] = True
    u["ice"] = (nm in ("ice", "phanerozoic ice"))
before = int((G > 0).sum())
G[~LAND] = 0
G[drop[G]] = 0
print("land-masked px", before, "->", int((G > 0).sum()))


def on_land(lat_, lon_):
    x, y = pj([(lon_, lat_)])[0]
    xi, yi = int(min(N5 - 1, max(0, x))), int(min(N5 - 1, max(0, y)))
    return LAND[yi, xi]


lines_out = [l for l in lines_out if sum(on_land(l[k], l[k + 1]) for k in range(1, len(l), 2)) * 2 >= (len(l) - 1) // 2]
print("fault lines on land", len(lines_out))
del limg

# ---------------------------------------------------------------------------
# relief: terrarium zoom 4 -> 4096 x 4096 elevation, shaded, doubled
T = json.load(gzip.open(TERRARIUM))["tiles"]
E = np.zeros((NT * 256, NT * 256), np.float32)
for k, b64 in T.items():
    z, x, y = map(int, k.split("/"))
    if z != 4:
        continue
    a = np.asarray(Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")).astype(np.float32)
    E[y * 256:(y + 1) * 256, x * 256:(x + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
E = np.maximum(E, 0)
rows = np.arange(NT * 256)
lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (rows + .5) / (NT * 256)))))
cell = 2 * np.pi * 6378137 / (NT * 256) * np.cos(np.radians(lat))      # ground metres per pixel, by row
zf = 18.0
gy = np.gradient(E, axis=0) * zf / cell[:, None]
gx = np.gradient(E, axis=1) * zf / cell[:, None]
dzdx, dzdy = gx, -gy
slope = np.arctan(np.hypot(dzdx, dzdy)); aspect = np.arctan2(-dzdx, -dzdy)
alt = np.radians(45); shade = np.zeros_like(E)
for az, w in ((315, .6), (270, .2), (0, .2)):
    a = np.radians(az)
    shade += w * (np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(a - aspect))
v = np.clip(shade / np.sin(alt), 0, 1) ** 1.4
HS = (25 + 230 * v).astype(np.uint8)
del E, gx, gy, dzdx, dzdy, slope, aspect, shade, v

# ---------------------------------------------------------------------------
# countries (Natural Earth 1:50m) for the analysis
ne = json.load(open(os.path.join(NE, "ne_50m_admin_0_countries.geojson")))
cimg = Image.new("L", (NT * RES, NT * RES), 0)
cd = ImageDraw.Draw(cimg)
countries = []

for f in ne["features"]:
    pr = f["properties"]
    countries.append({"name": pr.get("NAME") or pr.get("ADMIN"), "iso": pr.get("ISO_A3") or pr.get("ADM0_A3"), "continent": pr.get("CONTINENT")})
    v = len(countries)
    g = f["geometry"]
    parts = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for rings in parts:
        cd.polygon(pj(rings[0]), fill=v)
CTRY = np.asarray(cimg, dtype=np.uint8)
np.savez_compressed(os.path.join(SCRATCH, "world_grid.npz"), g=G, c=CTRY)
json.dump(countries, open(os.path.join(SCRATCH, "world_countries.json"), "w"))
del CTRY, cimg

# ---------------------------------------------------------------------------
tot = 0; tiles = []
LAND4 = G.reshape(NT * 256, 2, NT * 256, 2).max(axis=(1, 3)) > 0
for ty in range(NT):
    for tx in range(NT):
        g = G[ty * RES:(ty + 1) * RES, tx * RES:(tx + 1) * RES]
        if not g.any():
            continue
        fn = os.path.join(DATA, "world", "w_%d_%d.png" % (tx, ty))
        Image.fromarray(np.dstack([(g & 255).astype(np.uint8), (g >> 8).astype(np.uint8), np.zeros_like(g, np.uint8)]), "RGB").save(fn, optimize=True)
        h = HS[ty * 256:(ty + 1) * 256, tx * 256:(tx + 1) * 256].copy()
        h[~LAND4[ty * 256:(ty + 1) * 256, tx * 256:(tx + 1) * 256]] = 255
        fh = os.path.join(DATA, "world", "h_%d_%d.jpg" % (tx, ty))
        Image.fromarray(h).save(fh, quality=72)
        tot += os.path.getsize(fn) + os.path.getsize(fh); tiles.append([tx, ty])
print("tiles", len(tiles), "bytes", tot)
st = 4
og = G[st // 2::st, st // 2::st]
Image.fromarray(np.dstack([(og & 255).astype(np.uint8), (og >> 8).astype(np.uint8), np.zeros_like(og, np.uint8)]), "RGB").save(os.path.join(DATA, "world", "overview.png"), optimize=True)
oh = HS[1::2, 1::2].copy(); oh[og == 0] = 255
Image.fromarray(oh).save(os.path.join(DATA, "world", "overview_h.jpg"), quality=72)
print("overview", og.shape, os.path.getsize(os.path.join(DATA, "world", "overview.png")), os.path.getsize(os.path.join(DATA, "world", "overview_h.jpg")))

with open(os.path.join(DATA, "units_world.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "name", "lithology", "age_text", "oldest_interval", "youngest_interval", "max_age_ma", "min_age_ma", "period", "rock_type", "source_ref", "description", "ice"])
    for u in units:
        w.writerow([u["id"], u["name"], u["lith"], u["age"], u["b_int"], u["t_int"], u["max_ma"], u["min_ma"], u["period"] or "", u["rock"], u["ref"], u["descrip"], int(u.get("ice", False))])
json.dump(refs, open(os.path.join(SCRATCH, "world_refs.json"), "w"), indent=1)
WMETA = {"tz": TZ, "res": RES, "tiles": tiles, "ov_step": st,
         "about": "Web Mercator (EPSG:3857). w_<x>_<y>.png is zoom-4 tile x, y drawn at 512 px (zoom-5 pixels); unit id = R + 256 G (data/units_world.csv), 0 = none. "
                  "h_<x>_<y>.jpg: hill shade at 256 px. overview.png and overview_h.jpg: the whole world at 2048 px (zoom-3 pixels)."}
json.dump(WMETA, open(os.path.join(SCRATCH, "world_meta.json"), "w"))
json.dump(WMETA, open(os.path.join(DATA, "world", "meta.json"), "w"), indent=0)
json.dump(lines_out, open(os.path.join(DATA, "world_lines.json"), "w"), separators=(",", ":"))
print("lines bytes", os.path.getsize(os.path.join(DATA, "world_lines.json")))
