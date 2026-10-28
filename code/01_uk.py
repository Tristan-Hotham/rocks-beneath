"""British Isles: unit table and page rasters.

Reads the BGS Geology 625k bedrock and superficial polygons (Great Britain, Northern
Ireland and the Isle of Man) and the GSI/GSNI 1:500k bedrock polygons (used for the
Republic of Ireland; where both exist, BGS wins), and draws them onto one grid in Web
Mercator at zoom 9 (305.7 m per pixel at the equator, about 175 m on the ground at
55 degrees north).

Writes
  data/units_uk.csv            one row per map unit
  data/uk/u_<x>_<y>.png         512 by 512 chunks (one per zoom-8 tile): R + 256 G = unit, B = superficial class
  data/uk/overview.png          the same at zoom 7 (every fourth pixel), for the zoomed-out view
  scratch uk_grid.npz           full grids for the analysis (not published)
"""
import csv, gzip, json, math, os, re, sys, zipfile, io
import numpy as np
from PIL import Image, ImageDraw
import shapefile
from pyproj import Transformer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

Z = 9
CH = 512
LON0, LON1, LAT0, LAT1 = -11.0, 2.1, 49.7, 61.0
x0, y1 = lonlat_to_px(LON0, LAT0, Z); x1, y0 = lonlat_to_px(LON1, LAT1, Z)
GX0 = int(x0 // CH) * CH; GY0 = int(y0 // CH) * CH
GX1 = int(math.ceil(x1 / CH)) * CH; GY1 = int(math.ceil(y1 / CH)) * CH
W, H = GX1 - GX0, GY1 - GY0
print("grid", W, H, "origin", GX0, GY0)
os.makedirs(os.path.join(DATA, "uk"), exist_ok=True)
os.makedirs(SCRATCH, exist_ok=True)

N9 = 256 * 2 ** Z


def proj(coords):
    a = np.asarray(coords, dtype=np.float64)
    x = (a[:, 0] + 180.0) / 360.0 * N9 - GX0
    la = np.radians(np.clip(a[:, 1], -85, 85))
    y = (1 - np.log(np.tan(la) + 1 / np.cos(la)) / np.pi) / 2 * N9 - GY0
    return list(zip(x.tolist(), y.tolist()))


def rings_of(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def ring_area(r):
    a = np.asarray(r)
    return abs(np.dot(a[:-1, 0], a[1:, 1]) - np.dot(a[1:, 0], a[:-1, 1])) / 2


def paint(img, polys):
    """polys: list of (value, [exterior, holes...] in pixel coords). Largest first; holes cleared."""
    d = ImageDraw.Draw(img)
    polys.sort(key=lambda p: -ring_area(p[1][0]))
    for v, rings in polys:
        if len(rings[0]) < 3:
            continue
        d.polygon(rings[0], fill=v)
        for h in rings[1:]:
            if len(h) >= 3:
                d.polygon(h, fill=0)


def tcase(s):
    s = re.sub(r"\s*\[.*?\]", "", s).strip()
    small = {"And", "Of", "To", "The", "In", "With", "Or", "On", "Including"}
    keep = {"UK", "NW", "SE"}
    out = []
    for i, w in enumerate(s.lower().split()):
        t = "-".join(x.capitalize() for x in w.split("-")) if w[:1].isalpha() else w
        if w.startswith("(") or w.startswith("["):
            t = w[0] + w[1:].capitalize()
        if i and t in small:
            t = t.lower()
        out.append(t)
    s = " ".join(out)
    for k in keep:
        s = s.replace(k.capitalize(), k)
    return s.replace("[see Also Migr]", "").replace("[obsolete  Except in Northern Ireland: Use Pcm, Swcm, Cmsc]", "").replace("[under Review; Possibly Obsolete]", "").replace("  ", " ").strip()


def sentence(s):
    s = s.strip().lower()
    return s[:1].upper() + s[1:]


# ---------------------------------------------------------------------------
# BGS units: ages, period, rock type, 1969 class
def bgs_ages(p):
    mx, mn = p["max_time_y"], p["min_time_y"]
    note = ""
    if mx is None or mx < 0:
        era = (p.get("max_era") or "").strip() or (p.get("max_period") or "").strip()
        if "ARCHAEAN" in (p.get("max_time_d") or "") or era == "":
            mx = 3200e6; note = "oldest age given only as Archaean: set to 3,200 Ma, the oldest protolith age of the Lewisian gneisses (BGS Earthwise)"
        elif "PALAEOPROTEROZOIC" in era:
            mx = 2500e6; note = "oldest age given only as Palaeoproterozoic: set to 2,500 Ma, the start of that era"
        else:
            mx = 2500e6; note = "oldest age given only as Proterozoic: set to 2,500 Ma"
    if mn is None or mn < 0:
        mn = 0
    if mx == 0 and mn == 0:
        return None, None, "no age in the source"
    return mx / 1e6, mn / 1e6, note


def bgs_1969(p, rock):
    lex = p["lex"]; lr = p["lex_rcs"]; gp = p["gp_eq_d"]; sg = p["supgp_eq_d"]; t = p["rcs_d"]
    mx = (p["max_time_y"] or 0) / 1e6
    if lex.startswith("UI") or p["rank"] == "INTRUSION":
        if rock == "vo":
            pass
        elif any(w in t for w in ["FELSIC", "SYENITIC", "PYROCLASTIC"]):
            return "IA"
        else:
            return "IB"
    if lex.startswith("UEX") or lex == "CAOR":
        code = lex[3:]
        if code.startswith("G"):
            return "VT"
        if code.startswith("C") or code.startswith("P"):
            return "VC"
        if code.startswith("D") or code.startswith("SD"):
            return "VD"
        if code.startswith("A"):
            return "VP"
        return "VL"
    if lex in ("L", "LMR", "MSC") or lex.startswith("UIIAL"):
        return "LW"
    if "MOINE" in sg:
        return "MO"
    if "DALRADIAN" in sg:
        return "DU" if lex in ("SOHI", "ARGY") else "DL"
    if lex in ("TC", "TB", "TA", "UMSAZ"):
        return "TO"
    if lex in ("UMAZ",) and "HORNBLENDE" in t or lr == "DEV-HBSCH":
        return "HB"
    if lex in ("UMAZ", "BZ", "UMPCC", "AXRU", "HBX", "UNPH", "FZRU") or lr == "DEV-SCHM":
        return "MX"
    m = {"LRC": "CA", "MC": "CA", "UC": "CA", "ARDV": "CA", "DNG": "CA",
         "TREM": "OD", "ORD": "OD", "ARNG": "OD", "LLVN": "OD", "CARA": "OD", "ASHL": "OD", "LHG": "OD", "TAP": "OD", "KKF": "OD",
         "SHGN": "OD", "PPGW": "OD", "BKGA": "OD", "CRMF": "OD",
         "GALA": "SI", "LDVY": "SI", "HWK": "SI", "SILU": "SI", "RCN": "SI", "WEN": "SI", "LUDL": "SI", "PRID": "SI",
         "SHG": "OR1", "LNK": "OR1", "DRCR": "OR1", "REST": "OR1", "LORS": "OR1", "LDEV": "OR1", "ATGK": "OR1", "CSSL": "OR1", "SEG": "OR1",
         "ORS": "OR2", "DEV": "OR2", "MOR": "OR2", "MDEV": "OR2",
         "UDEV": "OR3", "UORS": "OR3", "SAG": "OR3", "FIN": "OR3", "SHAN": "OR3",
         "TEVY": "MG", "MG": "MG", "HOWY": "MG",
         "INV": "CL", "DINA": "CL", "OMSG": "CL", "TYRO": "CL", "BHCR": "CL", "ROEV": "CL", "HOLY": "CL", "OWSA": "CL", "BDR": "CL",
         "ARMA": "CL", "SYG": "CL", "YORE": "CL", "KILS": "CL", "LEG": "CL", "CKN": "CL",
         "PSLCM": "CM", "CMSC": "CM", "CM": "CM", "PCM": "CM", "PSMCM": "CM", "PUCM": "CM", "SWUCM": "CM", "WAWK": "CM", "SLI": "CM",
         "STEW": "PE", "PUND": "PE", "ENLE": "PE", "NRS": "PE", "APY": "PE",
         "ZG": "ML", "BELF": "ML",
         "SSG": "BU", "TRIA": "KE", "MMG": "KE",
         "LI": "LI", "INO": "OL", "RAG": "OL", "JURM": "OL", "GOG": "OL",
         "KLOX": "OU", "WWAK": "OU", "CR": "OU", "JURU": "OU", "PL": "OU", "PB": "OU",
         "W": "WE", "LGS": "LG", "GUGS": "UG", "GYCK": "CH", "WHCK": "CH", "HGUW": "CH",
         "PALUC": "PG", "LMBE": "PG", "SOLT": "PG", "TAB": "PG", "THAM": "PG", "BRBA": "PG", "LNG": "PG", "EOMIO": "PG",
         "NEOG": "NQ", "NEOQ": "NQ"}
    if lr == "TRIA-SCON":
        return "BU"
    return m.get(lex, "XX")


PERIOD_OVERRIDE = {"WAWK": "C"}   # Warwickshire Group: overwhelmingly Westphalian (Late Carboniferous)

units = []      # dicts
ukey = {}


def add_unit(key, **kw):
    if key in ukey:
        return ukey[key]
    kw["id"] = len(units) + 1
    units.append(kw); ukey[key] = kw["id"]
    return kw["id"]


print("reading BGS")
B = json.load(gzip.open(BGS))
bed = B["collections"]["bgsgeology625kbedrock"]
sup = B["collections"]["bgsgeology625ksuperficial"]
bed_polys = []
for f in bed:
    p = f["properties"]
    mx, mn, note = bgs_ages(p)
    intr = p["lex"].startswith("UI") or p["rank"] == "INTRUSION"
    rock = rock_from_text(p["rcs_d"], intr)
    if p["lex"].startswith("UEX") or p["lex"] == "CAOR":
        rock = "vo"
    if mx is None:
        per = None
    elif mx >= 1000:
        per = period_of(mx - 1e-6, BGS_BOUNDS)
    else:
        per = period_of((mx + mn) / 2 + 1e-6, BGS_BOUNDS)
    per = PERIOD_OVERRIDE.get(p["lex"], per)
    uid = add_unit("BGS:" + p["lex_rcs"], src="BGS", code=p["lex_rcs"], name=tcase(p["lex_d"]), rocktext=sentence(p["rcs_d"]),
                   group=tcase(p["gp_eq_d"]) if p["gp_eq_d"].strip() not in ("", "No Parent", "Not Applicable") else "",
                   max_ma=mx, min_ma=mn, age_text=(p["max_time_d"].title() + (" to " + p["min_time_d"].title() if p["min_time_d"] != p["max_time_d"] else "")).replace("Mid ", "Middle "),
                   period=per, rock=rock, c69=bgs_1969(p, rock), note=note)
    for rings in rings_of(f["geometry"]):
        bed_polys.append((uid, [proj(r) for r in rings]))
n_bgs = len(units)
print("BGS units", n_bgs, "polygon parts", len(bed_polys))

# ---------------------------------------------------------------------------
# GSI / GSNI 1:500k
GSI_AGE = {  # AGEBRACKET -> (oldest Ma, youngest Ma)
    "Neoproterozoic": (1000, 539), "Neoproterozoic & Lower Palaeozoic": (1000, 444), "Lower Palaeozoic": (539, 419),
    "Caledonian (Silurian - Devonian)": (444, 359), "Palaeogene": (66, 23), "Palaeoproterozoic": (2500, 1600),
    "Palaeoproterozoic, Annagh Gneiss Complex": (2500, 1600), "Mesooproterozoic, Annagh Gneiss Complex": (1600, 1000),
    "Neoproterozoic, Rosslare Complex": (1000, 539), "Neoproterozoic, Dalradian Supergroup": (1000, 539),
    "Neoproterozoic (-Cambrian), Dalradian Supergroup": (1000, 509), "Palaeozoic, Cambrian": (539, 485),
    "Palaeozoic, Lower - Middle Ordovician": (485, 458), "Palaeozoic, Middle - Upper Ordovician": (470, 444),
    "Palaeozoic, Ordovician or Silurian": (485, 419), "Palaeozoic, Ordovician - Silurian": (485, 419), "Palaeozoic, Silurian": (444, 419),
    "Palaeozoic, Devonian": (419, 359), "Palaeozoic, Lower Devonian": (419, 393), "Palaeozoic, Middle Devonian": (393, 383),
    "Palaeozoic, Upper Devonian - Carboniferous": (383, 347), "Palaeozoic, Upper Devonian": (383, 359), "Palaeozoic, Carboniferous": (359, 299),
    "Palaeozoic, Carboniferous, Mississippian": (359, 323), "Palaeozoic, Carboniferous, Mississipp. - Pennsyl.": (335, 310),
    "Palaeozoic, Carboniferous, Pennsylvanian": (323, 299), "Palaeozoic, Permian": (299, 252), "Palaeozoic - Mesozoic, Permian - Triassic": (299, 201),
    "Mesozoic, Triassic": (252, 201), "Mesozoic, Jurassic": (201, 145), "Mesozoic, Cretaceous": (145, 66),
    "Cenozoic, Palaeogene, Palaeocene": (66, 56), "Cenozoic, Palaeogene, Oligocene": (34, 23),
}
GSI_OVERRIDE_AGE = {76: (201, 174), 77: (100, 66)}   # unit names say Lias (Early Jurassic) and Upper Cretaceous
GSI_1969 = {1: "IB", 2: "IB", 3: "GG", 4: "IA", 5: "IB", 6: "IA", 7: "IB", 8: "IA", 9: "IA", 10: "VT", 11: "IB", 12: "GG", 13: "GG", 14: "GG", 15: "GG",
            16: "MX", 17: "HB", 18: "MX", 19: "MX", 20: "MX", 21: "DL", 22: "DL", 23: "DL", 24: "DU", 25: "DU", 26: "DU", 27: "DU", 28: "DU", 29: "DU",
            30: "CA", 31: "CA", 32: "CA", 33: "VL", 34: "VL", 35: "OD", 36: "OD", 37: "VL", 38: "VL", 39: "OD", 40: "OD", 41: "OD", 42: "OD",
            43: "SI", 44: "VL", 45: "SI", 46: "SI", 47: "SI", 48: "SI", 49: "SI", 50: "VD", 51: "VD", 52: "OR1", 53: "OR2", 54: "OR3", 55: "OR3",
            56: "VC", 72: "CM", 70: "MG", 71: "MG", 73: "PE", 74: "PE", 75: "KE", 76: "LI", 77: "CH", 78: "VT", 79: "VT", 80: "VT", 81: "VT", 82: "VT", 83: "PG"}
for k in range(57, 70):
    GSI_1969[k] = "CL"
GSI_ROCK = {1: "mm", 2: "ii", 3: "mm", 12: "mm", 13: "mm", 14: "mm", 15: "mm", 10: "vo", 80: "vo", 66: "ss", 68: "md", 30: "mm", 31: "mm",
            35: "mm", 72: "co", 69: "ss", 71: "md", 83: "sf", 57: "md", 58: "md", 59: "ss", 63: "ss", 60: "ls", 61: "ls", 62: "ls", 64: "ls", 65: "ls", 67: "ls",
            73: "ss", 74: "ss", 75: "ss", 76: "md", 77: "ch", 42: "md", 41: "ss"}
gdir = os.path.join(SCRATCH, "gsi")
os.makedirs(gdir, exist_ok=True)
with zipfile.ZipFile(GSI_ZIP) as zf:
    for n in zf.namelist():
        if "_MS." in n and n.split(".")[-1] in ("shp", "shx", "dbf", "prj", "CPG"):
            zf.extract(n, gdir)
itm = Transformer.from_crs("EPSG:2157", "EPSG:4326", always_xy=True)
sr = shapefile.Reader(os.path.join(gdir, "IE_GSI_GSNI_Bedrock_Geology_500k_IE32_ITM_MS"))
gsi_polys = []
for sh, rec in zip(sr.shapes(), sr.records()):
    un, ab = rec["UNITNAME"], rec["AGEBRACKET"]
    num = int(un.split(",")[0])
    nm = un.split(",", 1)[1].strip()
    mx, mn = GSI_OVERRIDE_AGE.get(num, GSI_AGE[ab])
    per = period_of(mx - 1e-6) if mx >= 1000 else period_of((mx + mn) / 2 + 1e-6)
    if ";" in nm:
        setting, lith = [s.strip() for s in nm.split(";", 1)]
    else:
        setting, lith = "", nm
    rock = GSI_ROCK.get(num) or rock_from_text(lith.upper(), num <= 11)
    uid = add_unit("GSI:%d" % num, src="GSI", code="GSI %d" % num, name=clean(nm.replace(' - "', ', "').replace(" - ", " to ")), rocktext=clean(lith.replace(" - ", " to ")), group=clean(setting.replace(' - "', ', "').replace(" - ", " to ")),
                   max_ma=mx, min_ma=mn, age_text=clean(ab.replace("Mesooproterozoic", "Mesoproterozoic").replace(" - ", " to ").replace("Mississipp. to Pennsyl.", "Mississippian to Pennsylvanian")),
                   period=per, rock=rock, c69=GSI_1969[num], note="")
    pts = np.asarray(sh.points)
    parts = list(sh.parts) + [len(pts)]
    rings = []
    for a, b in zip(parts[:-1], parts[1:]):
        lon, lat = itm.transform(pts[a:b, 0], pts[a:b, 1])
        rings.append(proj(np.column_stack([lon, lat])))
    # shapefile rings: clockwise exteriors, counter-clockwise holes; group holes after their exterior
    cur = None
    for r in rings:
        a = np.asarray(r); s = np.dot(a[:-1, 0], a[1:, 1]) - np.dot(a[1:, 0], a[:-1, 1])
        if s > 0 or cur is None:   # y runs downwards in pixel space, so clockwise rings have positive signed area
            if cur:
                gsi_polys.append((uid, cur))
            cur = [r]
        else:
            cur.append(r)
    if cur:
        gsi_polys.append((uid, cur))
print("units total", len(units), "GSI parts", len(gsi_polys))

# ---------------------------------------------------------------------------
print("painting")
img = Image.new("I", (W, H), 0)
paint(img, gsi_polys)
gsi_only = np.asarray(img, dtype=np.int32).copy()
img2 = Image.new("I", (W, H), 0)
paint(img2, bed_polys)
bgs = np.asarray(img2, dtype=np.int32)
grid = np.where(bgs > 0, bgs, gsi_only).astype(np.uint16)
del img, img2
print("land px", int((grid > 0).sum()), "bgs px", int((bgs > 0).sum()))

# superficial
sup_polys = []
sup_seen = {}
for f in sup:
    k = super_class(f["properties"]["lex_d"])
    if k is None:
        continue
    v = SKEYS.index(k) + 1
    for rings in rings_of(f["geometry"]):
        sup_polys.append((v, [proj(r) for r in rings]))
simg = Image.new("L", (W, H), 0)
paint(simg, sup_polys)
supg = np.asarray(simg, dtype=np.uint8).copy()
supg[grid == 0] = 0
# areas where superficial deposits were not mapped at this scale
nm_polys = []
for f in sup:
    if "NOT MAPPED" in f["properties"]["lex_d"]:
        for rings in rings_of(f["geometry"]):
            nm_polys.append((1, [proj(r) for r in rings]))
nimg = Image.new("L", (W, H), 0)
paint(nimg, nm_polys)
notmapped = np.asarray(nimg, dtype=np.uint8) > 0

# nations: E/W/S from county polygons; NI and the Isle of Man by position; Republic of Ireland where only GSI data
cty = json.load(open(COUNTIES))
cimg = Image.new("L", (W, H), 0)
cp = []
for f in cty["features"]:
    v = {"England": 1, "Wales": 2, "Scotland": 3}[f["properties"]["nation"]]
    for rings in rings_of(f["geometry"]):
        cp.append((v, [proj(r) for r in rings]))
paint(cimg, cp)
nat = np.asarray(cimg, dtype=np.uint8).copy()
from scipy import ndimage
jj, ii = np.nonzero(grid)
xs = (GX0 + ii + .5) / N9 * 360 - 180
ys = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (GY0 + jj + .5) / N9))))
is_ni = (bgs[jj, ii] > 0) & (((xs < -5.3) & (ys > 54.0) & (ys < 55.0)) | ((xs < -5.95) & (ys >= 55.0) & (ys < 55.35)))
is_im = (bgs[jj, ii] > 0) & (xs > -4.9) & (xs < -4.25) & (ys > 54.0) & (ys < 54.45)
is_ie = bgs[jj, ii] == 0
# land in GB not inside a county polygon: nearest county
missing = nat == 0
dist, (ri, rc) = ndimage.distance_transform_edt(missing, return_indices=True)
near = nat[ri, rc]
natv = nat[jj, ii].copy()
natv[natv == 0] = near[jj, ii][natv == 0]
natv[is_ni] = 4; natv[is_im] = 5; natv[is_ie] = 6
NAT = np.zeros_like(nat); NAT[jj, ii] = natv
del dist, ri, rc, near, missing
print("nations px", {k: int((NAT == v).sum()) for k, v in [("E", 1), ("W", 2), ("S", 3), ("NI", 4), ("IM", 5), ("IE", 6)]})

np.savez_compressed(os.path.join(SCRATCH, "uk_grid.npz"), bed=grid, sup=supg, nat=NAT, notmapped=notmapped,
                    meta=np.array([GX0, GY0, W, H, Z]))

# ---------------------------------------------------------------------------
# chunks
cnt = 0; tot = 0
for f in os.listdir(os.path.join(DATA, "uk")):
    if f.startswith("u_"):
        os.remove(os.path.join(DATA, "uk", f))
chunks = []
for cy in range(H // CH):
    for cx in range(W // CH):
        g = grid[cy * CH:(cy + 1) * CH, cx * CH:(cx + 1) * CH]
        if not g.any():
            continue
        s = supg[cy * CH:(cy + 1) * CH, cx * CH:(cx + 1) * CH]
        rgb = np.dstack([(g & 255).astype(np.uint8), (g >> 8).astype(np.uint8), s])
        tx, ty = GX0 // CH + cx, GY0 // CH + cy
        fn = os.path.join(DATA, "uk", "u_%d_%d.png" % (tx, ty))
        Image.fromarray(rgb, "RGB").save(fn, optimize=True)
        cnt += 1; tot += os.path.getsize(fn); chunks.append([tx, ty])
print("chunks", cnt, "bytes", tot)
ov = grid[2::4, 2::4]; os_ = supg[2::4, 2::4]
Image.fromarray(np.dstack([(ov & 255).astype(np.uint8), (ov >> 8).astype(np.uint8), os_]), "RGB").save(os.path.join(DATA, "uk", "overview.png"), optimize=True)
print("overview", ov.shape, os.path.getsize(os.path.join(DATA, "uk", "overview.png")))

with open(os.path.join(DATA, "units_uk.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "source", "code", "name", "group_or_setting", "lithology", "age_text", "max_age_ma", "min_age_ma", "period", "rock_type", "class_1969", "age_note"])
    for u in units:
        w.writerow([u["id"], u["src"], u["code"], u["name"], u["group"], u["rocktext"], u["age_text"], "" if u["max_ma"] is None else round(u["max_ma"], 2),
                    "" if u["min_ma"] is None else round(u["min_ma"], 2), u["period"] or "", u["rock"], u["c69"], u["note"]])
META = {"z": Z, "chunk": CH, "chunk_zoom": Z - 1, "gx0": GX0, "gy0": GY0, "w": W, "h": H, "ov_step": 4, "chunks": chunks,
        "about": "Web Mercator (EPSG:3857) pixels at zoom z (256 px tiles). u_<x>_<y>.png covers global pixels x*512 to x*512+511 (same for y); "
                 "unit id = R + 256 G (data/units_uk.csv), B = superficial class (1-based, data/uk_superficial_share.csv order), 0 = none. "
                 "h_<x>_<y>.jpg: hill shade at half resolution (255 flat). overview.png: every fourth pixel of the grid whose top-left global pixel is (gx0, gy0)."}
json.dump(META, open(os.path.join(SCRATCH, "uk_meta.json"), "w"))
json.dump(META, open(os.path.join(DATA, "uk", "meta.json"), "w"), indent=0)
print("done")
