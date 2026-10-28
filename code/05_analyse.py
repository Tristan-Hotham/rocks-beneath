"""All the numbers. Areas are measured on the page grids, each pixel weighted by its true
ground area (Web Mercator pixels shrink with the cosine of latitude).

Writes data/results.json and the summary CSVs in data/.
"""
import csv, io, json, math, os, sys, zipfile
import numpy as np
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

R_E = 6378137.0
res = {"meta": {"retrieved": "28 October 2026"}}

# ---------------------------------------------------------------------------
# British Isles
UM = json.load(open(os.path.join(SCRATCH, "uk_meta.json")))
GX0, GY0, W, H, Z = UM["gx0"], UM["gy0"], UM["w"], UM["h"], UM["z"]
N9 = 256 * 2 ** Z
g = np.load(os.path.join(SCRATCH, "uk_grid.npz"))
BED, SUP, NAT, NOTM = g["bed"], g["sup"], g["nat"], g["notmapped"]
rows = GY0 + np.arange(H) + .5
LAT = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * rows / N9))))
PXA = (2 * np.pi * R_E / N9 * np.cos(np.radians(LAT))) ** 2 / 1e6         # km2 per pixel, by row
A = np.broadcast_to(PXA[:, None], (H, W))
U = {int(r["id"]): r for r in csv.DictReader(open(os.path.join(DATA, "units_uk.csv")))}
NU = max(U) + 1


def lut(field, keys):
    a = np.full(NU, -1, np.int16)
    for i, u in U.items():
        if u[field] in keys:
            a[i] = keys.index(u[field])
    return a


L_PER, L_ROCK, L_69 = lut("period", PKEYS), lut("rock_type", RKEYS), lut("class_1969", C69KEYS)
MAXA = np.zeros(NU); MINA = np.zeros(NU)
for i, u in U.items():
    MAXA[i] = float(u["max_age_ma"] or "nan"); MINA[i] = float(u["min_age_ma"] or "nan")

NATS = {"england": [1], "wales": [2], "scotland": [3], "gb": [1, 2, 3], "ni": [4], "iom": [5], "roi": [6], "ireland": [4, 6], "isles": [1, 2, 3, 4, 5, 6]}
mask = {k: np.isin(NAT, v) & (BED > 0) for k, v in NATS.items()}
area = {k: float(A[m].sum()) for k, m in mask.items()}
res["uk_area_km2"] = {k: round(v) for k, v in area.items()}


def shares(m, L, keys):
    out = {}
    idx = L[BED[m]]; w = A[m]
    tot = w.sum()
    for k, key in enumerate(keys):
        out[key] = float(w[idx == k].sum() / tot * 100)
    return out


per_sh = {k: shares(mask[k], L_PER, PKEYS) for k in ("gb", "england", "wales", "scotland", "ireland", "roi", "ni", "isles")}
rock_sh = {k: shares(mask[k], L_ROCK, RKEYS) for k in ("gb", "england", "wales", "scotland", "ireland", "isles")}
c69_sh = {k: shares(mask[k], L_69, C69KEYS) for k in ("gb", "ireland", "isles")}
res["uk_period_share"] = {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in per_sh.items()}
res["uk_rock_share"] = {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in rock_sh.items()}
res["uk_1969_share"] = {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in c69_sh.items()}
with open(os.path.join(DATA, "uk_share_by_period.csv"), "w", newline="") as fh:
    w = csv.writer(fh); keys = ["gb", "england", "wales", "scotland", "ni", "roi", "ireland", "isles"]
    w.writerow(["period", "name"] + ["pct_" + k for k in keys])
    for p in PERIODS:
        w.writerow([p[0], p[1]] + [round(per_sh[k][p[0]], 2) for k in keys])
with open(os.path.join(DATA, "uk_share_by_rock_type.csv"), "w", newline="") as fh:
    w = csv.writer(fh); keys = ["gb", "england", "wales", "scotland", "ireland", "isles"]
    w.writerow(["rock_type", "name"] + ["pct_" + k for k in keys])
    for r in ROCK:
        w.writerow([r[0], r[1]] + [round(rock_sh[k][r[0]], 2) for k in keys])
with open(os.path.join(DATA, "uk_share_by_1969_class.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["class", "label", "colour", "pct_gb", "pct_ireland", "pct_isles"])
    for c in C1969:
        w.writerow([c[0], c[1], c[2], round(c69_sh["gb"][c[0]], 2), round(c69_sh["ireland"][c[0]], 2), round(c69_sh["isles"][c[0]], 2)])

# area of every unit (British Isles), and the biggest units in each 1969 class
mi = mask["isles"]
ua = np.bincount(BED[mi].ravel(), weights=A[mi].ravel(), minlength=NU)
with open(os.path.join(DATA, "uk_unit_areas.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["id", "source", "name", "class_1969", "period", "rock_type", "km2_british_isles"])
    for i in sorted(U, key=lambda i: -ua[i]):
        w.writerow([i, U[i]["source"], U[i]["name"], U[i]["class_1969"], U[i]["period"], U[i]["rock_type"], round(float(ua[i]), 1)])
ex = {}
for c in C69KEYS:
    ids = sorted([i for i in U if U[i]["class_1969"] == c and ua[i] > 0], key=lambda i: -ua[i])
    names = []
    for i in ids:
        if U[i]["name"] not in names:
            names.append(U[i]["name"])
    ex[c] = names[:3]
res["c69_examples"] = ex
res["n_units_uk"] = {"bgs": sum(1 for u in U.values() if u["source"] == "BGS"), "gsi": sum(1 for u in U.values() if u["source"] == "GSI")}

# eras for GB
era_gb = {}
for e in ERAS:
    era_gb[e[0]] = sum(per_sh["gb"][p[0]] for p in PERIODS if p[5] == e[0])
res["uk_era_share_gb"] = {k: round(v, 1) for k, v in era_gb.items()}
era_isles = {e[0]: sum(per_sh["isles"][p[0]] for p in PERIODS if p[5] == e[0]) for e in ERAS}
res["uk_era_share_isles"] = {k: round(v, 1) for k, v in era_isles.items()}

# largest period and rock type in GB
top_p = max(per_sh["gb"].items(), key=lambda x: x[1]); top_r = max(rock_sh["gb"].items(), key=lambda x: x[1])
res["uk_top"] = {"period": top_p[0], "period_pct": round(top_p[1], 1), "rock": top_r[0], "rock_pct": round(top_r[1], 1)}
res["uk_carb_ireland_roi_pct"] = round(per_sh["roi"]["C"], 1)

# ---------------------------------------------------------------------------
# oldest rocks: Lewisian complex
lew = np.array([U[i]["code"].startswith("L-") and U[i]["source"] == "BGS" if i in U else False for i in range(NU)])
m = lew[BED] & mask["gb"]
jj, ii = np.nonzero(m)
lon = (GX0 + ii + .5) / N9 * 360 - 180
latp = LAT[jj]
wa = A[jj, ii]
lew_area = float(wa.sum())
west = (lon < -5.0) | (latp > 57.9)
hebr = lon < -6.1
res["oldest"] = {"lewisian_km2": round(lew_area), "lewisian_pct_gb": round(lew_area / area["gb"] * 100, 2),
                 "outer_hebrides_pct_of_lewisian": round(float(wa[hebr].sum() / lew_area * 100), 1),
                 "max_age_ma": 3200, "age_source": "BGS Earthwise, Bedrock Geology UK North: Archaean and Palaeoproterozoic (protolith ages 3.2 to 2.8 Ga)"}
# share of GB older than 1000 Ma (oldest age) and Precambrian by period assignment
res["oldest"]["precambrian_pct_gb"] = round(era_gb["PC"], 1)

# youngest bedrock
dated = [(i, MINA[i], MAXA[i]) for i in U if not math.isnan(MAXA[i]) and MAXA[i] > 0]
present = set(np.unique(BED[mask["isles"]]).tolist())
young = sorted([d for d in dated if d[0] in present], key=lambda d: (d[2], d[1]))[:4]
yl = []
for i, mn, mx in young:
    mm = (BED == i) & mask["isles"]
    jj, ii = np.nonzero(mm)
    yl.append({"id": i, "name": U[i]["name"], "max_ma": mx, "min_ma": mn, "km2": round(float(A[jj, ii].sum()), 1),
               "lat": round(float(LAT[jj].mean()), 3), "lon": round(float(((GX0 + ii + .5) / N9 * 360 - 180).mean()), 3)})
res["youngest_bedrock"] = yl
# Palaeogene volcanic and intrusive rocks (the youngest igneous rocks)
vt = np.isin(L_69[BED], [C69KEYS.index("VT")]) | (np.isin(L_69[BED], [C69KEYS.index("IA"), C69KEYS.index("IB")]) & (L_PER[BED] == PKEYS.index("Pg")))
res["palaeogene_igneous_km2"] = {"isles": round(float(A[vt & mask["isles"]].sum())), "gb": round(float(A[vt & mask["gb"]].sum())),
                                 "ni": round(float(A[vt & mask["ni"]].sum()))}

# ---------------------------------------------------------------------------
# transects: the tilted layer cake


def sample(lat, lon):
    x, y = lonlat_to_px(lon, lat, Z)
    i, j = int(x) - GX0, int(y) - GY0
    best = 0
    for r in range(0, 4):
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                if 0 <= j + dj < H and 0 <= i + di < W and BED[j + dj, i + di] > 0:
                    return int(BED[j + dj, i + di])
    return 0


def transect(name, a, b, step_km=1.0):
    la1, lo1 = a; la2, lo2 = b
    # straight line on the map (rhumb-ish, fine at this scale); distance along the ground
    d = 6371.0 * math.acos(math.sin(math.radians(la1)) * math.sin(math.radians(la2)) + math.cos(math.radians(la1)) * math.cos(math.radians(la2)) * math.cos(math.radians(lo2 - lo1)))
    n = int(d / step_km)
    out = []
    for k in range(n + 1):
        t = k / n
        la, lo = la1 + (la2 - la1) * t, lo1 + (lo2 - lo1) * t
        u = sample(la, lo)
        if u:
            uu = U[u]
            out.append({"km": round(d * t, 1), "lat": round(la, 4), "lon": round(lo, 4), "unit": u, "name": uu["name"], "period": uu["period"],
                        "max_ma": MAXA[u], "min_ma": MINA[u], "c69": uu["class_1969"], "rock": uu["rock_type"]})
    with open(os.path.join(DATA, "transect_%s.csv" % name), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["km", "lat", "lon", "unit_id", "unit", "period", "max_age_ma", "min_age_ma", "class_1969", "rock_type"])
        for o in out:
            w.writerow([o["km"], o["lat"], o["lon"], o["unit"], o["name"], o["period"], o["max_ma"], o["min_ma"], o["c69"], o["rock"]])
    ok = [o for o in out if not math.isnan(o["max_ma"])]
    rho = stats.spearmanr([o["km"] for o in ok], [o["max_ma"] for o in ok]).correlation
    # runs of periods along the line, in order
    runs = []
    for o in ok:
        if runs and runs[-1]["period"] == o["period"]:
            runs[-1]["to"] = o["km"]
        else:
            runs.append({"period": o["period"], "from": o["km"], "to": o["km"]})
    return {"km": round(d), "n": len(out), "rho": round(float(rho), 2), "start": out[0]["name"], "start_period": out[0]["period"],
            "start_max_ma": out[0]["max_ma"], "end": out[-1]["name"], "end_period": out[-1]["period"], "end_max_ma": out[-1]["max_ma"],
            "periods_in_order": [r["period"] for r in runs if r["to"] - r["from"] >= 4]}, out


SCAFELL = (54.45426, -3.2116); LONDON = (51.50741, -0.12772); HOLYHEAD = (53.3128, -4.63282)
t1, tr1 = transect("lakes_london", SCAFELL, LONDON)
t2, tr2 = transect("anglesey_london", HOLYHEAD, LONDON)
res["transect"] = {"lakes_london": t1, "anglesey_london": t2}

# across all of England and Wales: position along a north-west to south-east axis against oldest age
ew = mask["england"] | mask["wales"]
jj, ii = np.nonzero(ew)
sel = np.arange(len(jj))[::7]
jj, ii = jj[sel], ii[sel]
lon = (GX0 + ii + .5) / N9 * 360 - 180; la = LAT[jj]
xk = (lon + 2.0) * 111.32 * math.cos(math.radians(53)); yk = (la - 53) * 110.57
axis = (xk - yk) / math.sqrt(2)           # increases towards the south east
age = MAXA[BED[jj, ii]]
ok = ~np.isnan(age)
res["layer_cake_rho_ew"] = round(float(stats.spearmanr(axis[ok], age[ok]).correlation), 2)
res["layer_cake_n"] = int(ok.sum())
# England only, sedimentary rocks only (igneous intrusions break the cake)
sed = np.isin(L_ROCK[BED[jj, ii]], [RKEYS.index(k) for k in ("ss", "md", "ls", "ch", "co", "sf")])
okE = ok & sed & np.isin(NAT[jj, ii], [1])
res["layer_cake_rho_england_sed"] = round(float(stats.spearmanr(axis[okE], age[okE]).correlation), 2)

# ---------------------------------------------------------------------------
# chalk
ch = (L_69[BED] == C69KEYS.index("CH"))
res["chalk"] = {"gb_km2": round(float(A[ch & mask["gb"]].sum())), "gb_pct": round(float(A[ch & mask["gb"]].sum() / area["gb"] * 100), 1),
                "england_pct": round(float(A[ch & mask["england"]].sum() / area["england"] * 100), 1),
                "ni_km2": round(float(A[ch & mask["ni"]].sum()))}
spots = {"Dover": (51.12814, 1.30843), "Beachy Head": (50.73635, 0.25069), "Seven Sisters": (50.74702, 0.19068), "Old Harry": (50.64228, -1.92315),
         "Flamborough Head": (54.11642, -0.08492), "Durdle Door": (50.62159, -2.27545)}
res["chalk"]["spots"] = {k: U[sample(*v)]["name"] for k, v in spots.items()}

# ---------------------------------------------------------------------------
# coal: Coal Measures (1969 class) and towns
cm = (L_69[BED] == C69KEYS.index("CM"))
cm_gb = float(A[cm & mask["gb"]].sum())
res["coal"] = {"gb_km2": round(cm_gb), "gb_pct": round(cm_gb / area["gb"] * 100, 1)}
towns = []
with open(OSNAMES, encoding="utf-8") as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        if r["type"] == "populatedPlace" and r["local_type"] in ("City", "Town"):
            towns.append((r["name1"], r["county"] or r["district"], float(r["lat"]), float(r["lon"]), r["local_type"]))
on = []
for t in towns:
    u = sample(t[2], t[3])
    if u and U[u]["class_1969"] == "CM":
        on.append(t)
res["coal"]["os_towns"] = len(towns); res["coal"]["os_towns_on_cm"] = len(on)
res["coal"]["os_towns_on_cm_pct"] = round(len(on) / len(towns) * 100, 1)
res["coal"]["ratio_towns_to_land"] = round(len(on) / len(towns) * 100 / (cm_gb / area["gb"] * 100), 1)
# GeoNames towns of 15,000+ in Great Britain, with population
gn = []
with zipfile.ZipFile(GEONAMES) as z:
    for line in io.TextIOWrapper(z.open("cities15000.txt"), encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if c[8] == "GB" and c[10] in ("ENG", "SCT", "WLS") and c[7] != "PPLX":
            gn.append((c[1], float(c[4]), float(c[5]), int(c[14] or 0)))
gon = [p for p in gn if (lambda u: u and U[u]["class_1969"] == "CM")(sample(p[1], p[2]))]
res["coal"]["gn_towns"] = len(gn); res["coal"]["gn_towns_on_cm"] = len(gon)
res["coal"]["gn_pop_on_cm_pct"] = round(sum(p[3] for p in gon) / sum(p[3] for p in gn) * 100, 1)
res["coal"]["gn_examples"] = [p[0] for p in sorted(gon, key=lambda p: -p[3])[:14]]
with open(os.path.join(DATA, "towns_on_coal_measures.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["name", "county_or_district", "lat", "lon", "os_type"])
    for t in sorted(on):
        w.writerow([t[0], t[1], t[2], t[3], t[4]])

# what is under the towns, all of them (GeoNames 15,000+ in GB), by period and rock type
tp = {}; trk = {}
for p in gn:
    u = sample(p[1], p[2])
    if not u:
        continue
    tp[U[u]["period"]] = tp.get(U[u]["period"], 0) + p[3]
    trk[U[u]["rock_type"]] = trk.get(U[u]["rock_type"], 0) + p[3]
totp = sum(tp.values())
res["towns_by_period_pop_pct"] = {k: round(v / totp * 100, 1) for k, v in sorted(tp.items(), key=lambda x: -x[1])}

# ---------------------------------------------------------------------------
# superficial deposits (Great Britain; BGS 625k does not map them in Northern Ireland at this scale, see notmapped)
gbm = mask["gb"]
mapped = gbm & ~NOTM
sup_any = (SUP > 0) & mapped
res["superficial"] = {"gb_mapped_km2": round(float(A[mapped].sum())), "gb_notmapped_km2": round(float(A[gbm & NOTM].sum())),
                      "gb_pct": round(float(A[sup_any].sum() / A[mapped].sum() * 100), 1),
                      "ni_any_km2": round(float(A[(SUP > 0) & mask["ni"]].sum())), "ni_notmapped_km2": round(float(A[mask["ni"] & NOTM].sum()))}
for k in SKEYS:
    res["superficial"]["pct_" + k] = round(float(A[(SUP == SKEYS.index(k) + 1) & mapped].sum() / A[mapped].sum() * 100), 1)
for nm, nv in (("england", 1), ("wales", 2), ("scotland", 3)):
    mm = (NAT == nv) & (BED > 0) & ~NOTM
    res["superficial"][nm + "_pct"] = round(float(A[(SUP > 0) & mm].sum() / A[mm].sum() * 100), 1)
    res["superficial"][nm + "_till_pct"] = round(float(A[(SUP == SKEYS.index("till") + 1) & mm].sum() / A[mm].sum() * 100), 1)
with open(os.path.join(DATA, "uk_superficial_share.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["class", "label", "pct_of_gb_mapped_land"])
    for s in SUPER:
        w.writerow([s[0], s[1], res["superficial"]["pct_" + s[0]]])

# named spot checks
for k, v in {"Butt of Lewis": (58.51303, -6.26204), "Scafell Pike": (54.45426, -3.2116), "Ben Nevis": (56.7969, -5.0037),
             "London": LONDON, "Holyhead": HOLYHEAD}.items():
    u = sample(*v)
    res.setdefault("spots", {})[k] = {"name": U[u]["name"], "period": U[u]["period"], "max_ma": MAXA[u], "min_ma": MINA[u]}
del BED, SUP, NAT, NOTM, A, g

# ---------------------------------------------------------------------------
# World
WM = json.load(open(os.path.join(SCRATCH, "world_meta.json")))
gw = np.load(os.path.join(SCRATCH, "world_grid.npz"))
G, C = gw["g"], gw["c"]
NW = G.shape[0]
rows = np.arange(NW) + .5
LATW = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * rows / NW))))
PXW = (2 * np.pi * R_E / NW * np.cos(np.radians(LATW))) ** 2 / 1e6
WU = {int(r["id"]): r for r in csv.DictReader(open(os.path.join(DATA, "units_world.csv")))}
NWU = max(WU) + 1
ICE = np.zeros(NWU, bool); WPER = np.full(NWU, -1, np.int16); WROCK = np.full(NWU, -1, np.int16); WREF = np.full(NWU, -1, np.int16)
WMAX = np.full(NWU, np.nan); WMIN = np.full(NWU, np.nan)
for i, u in WU.items():
    ICE[i] = u["ice"] == "1"
    if u["period"]:
        WPER[i] = PKEYS.index(u["period"])
    WROCK[i] = RKEYS.index(u["rock_type"])
    WREF[i] = int(u["source_ref"])
    if u["max_age_ma"]:
        WMAX[i] = float(u["max_age_ma"]); WMIN[i] = float(u["min_age_ma"] or 0)
countries = json.load(open(os.path.join(SCRATCH, "world_countries.json")))
refs = json.load(open(os.path.join(SCRATCH, "world_refs.json")))

# accumulate per row band to keep memory modest
per_a = np.zeros(len(PKEYS)); ice_a = 0.0; undated_a = 0.0; rock_a = np.zeros(len(RKEYS)); ref_a = np.zeros(len(refs))
cper = np.zeros((len(countries) + 1, len(PKEYS))); cland = np.zeros(len(countries) + 1); cice = np.zeros(len(countries) + 1)
qvol = np.zeros(len(countries) + 1); nvol = np.zeros(len(countries) + 1)
agebins = np.logspace(0, math.log10(4000), 41); age_a = np.zeros(40)
VO = RKEYS.index("vo")
for j0 in range(0, NW, 512):
    gg = G[j0:j0 + 512]; cc = C[j0:j0 + 512].astype(np.int64)
    wgt = np.broadcast_to(PXW[j0:j0 + 512, None], gg.shape)
    on = gg > 0
    if not on.any():
        continue
    u = gg[on]; w = wgt[on]; c = cc[on]
    ice = ICE[u]; ice_a += w[ice].sum()
    np.add.at(cice, c[ice], w[ice])
    p = WPER[u]
    undated_a += w[(p < 0) & ~ice].sum()
    okp = p >= 0
    np.add.at(per_a, p[okp], w[okp])
    np.add.at(cper, (c[okp], p[okp]), w[okp])
    np.add.at(cland, c, w)
    nr = ~ice
    np.add.at(rock_a, WROCK[u][nr], w[nr])
    np.add.at(ref_a, WREF[u], w)
    mx = WMAX[u]; mn = WMIN[u]
    vol = (WROCK[u] == VO) & ~np.isnan(mx)
    q = vol & (mx <= 2.6)
    np.add.at(qvol, c[q], w[q])
    nn = vol & (mx <= 23.1)
    np.add.at(nvol, c[nn], w[nn])
    a = (~np.isnan(mx)) & (mx >= 1)
    k = np.clip(np.searchsorted(agebins, mx[a]) - 1, 0, 39)
    np.add.at(age_a, k, w[a])
dated_a = per_a.sum()
res["world"] = {"mapped_km2": round(float(dated_a + ice_a + undated_a)), "dated_km2": round(float(dated_a)), "ice_km2": round(float(ice_a)),
                "undated_km2": round(float(undated_a)), "units": len(WU)}
res["world_period_share"] = {PKEYS[k]: round(float(per_a[k] / dated_a * 100), 2) for k in range(len(PKEYS))}
era_w = {e[0]: sum(res["world_period_share"][p[0]] for p in PERIODS if p[5] == e[0]) for e in ERAS}
res["world_era_share"] = {k: round(v, 1) for k, v in era_w.items()}
res["world_rock_share"] = {RKEYS[k]: round(float(rock_a[k] / rock_a.sum() * 100), 1) for k in range(len(RKEYS))}
with open(os.path.join(DATA, "world_share_by_period.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["period", "name", "pct_of_dated_land"])
    for p in PERIODS:
        w.writerow([p[0], p[1], res["world_period_share"][p[0]]])
tot_ref = ref_a.sum()
with open(os.path.join(DATA, "world_sources.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["macrostrat_source_id", "short_name", "title", "authors", "year", "publisher", "url", "isbn_or_doi", "pct_of_mapped_land"])
    for k, r in enumerate(refs):
        w.writerow([r["source_id"], r["name"], r["title"], r["authors"], r["year"], r["publisher"], r["url"], r["isbn_doi"], round(float(ref_a[k] / tot_ref * 100), 1)])
res["world_sources"] = [{"name": r["name"], "title": r["title"], "authors": r["authors"], "year": r["year"], "pct": round(float(ref_a[k] / tot_ref * 100), 1)} for k, r in enumerate(refs)]
res["world_age_hist"] = {"bins_ma": [round(float(b), 2) for b in agebins], "km2": [round(float(x)) for x in age_a]}

# shields: Precambrian share of the dated, ice-free land
PCK = [PKEYS.index(k) for k in ("NP", "MP", "PP", "A")]


def pc_share(idx):
    d = cper[idx].sum()
    return round(float(cper[idx][:, PCK].sum() / d * 100), 1) if d else None


def cidx(names=None, continent=None):
    return [i + 1 for i, c in enumerate(countries) if (names and c["name"] in names) or (continent and c["continent"] == continent)]


res["shields"] = {
    "Canada": pc_share(cidx(["Canada"])), "Fennoscandia (Norway, Sweden, Finland)": pc_share(cidx(["Norway", "Sweden", "Finland"])),
    "Africa": pc_share(cidx(continent="Africa")), "Australia": pc_share(cidx(["Australia"])), "Brazil": pc_share(cidx(["Brazil"])),
    "India": pc_share(cidx(["India"])), "United States": pc_share(cidx(["United States of America"])), "China": pc_share(cidx(["China"])),
    "Europe (continent)": pc_share(cidx(continent="Europe")), "United Kingdom (Macrostrat)": pc_share(cidx(["United Kingdom"])),
}
res["shields_note"] = "Share of each area's dated, ice-free land whose map unit is Precambrian (older than 539 Ma), on the Macrostrat zoom-4 map."
# youngest volcanic rocks
qtot = qvol.sum(); ntot = nvol.sum()
topq = sorted([(countries[i - 1]["name"], qvol[i]) for i in range(1, len(countries) + 1) if qvol[i] > 0], key=lambda x: -x[1])[:10]
topn = sorted([(countries[i - 1]["name"], nvol[i]) for i in range(1, len(countries) + 1) if nvol[i] > 0], key=lambda x: -x[1])[:10]
res["young_volcanic"] = {"quaternary_km2": round(float(qtot)), "quaternary_pct_land": round(float(qtot / dated_a * 100), 2),
                         "top_quaternary": [[n, round(float(a))] for n, a in topq],
                         "neogene_quaternary_km2": round(float(ntot)), "top_neogene_quaternary": [[n, round(float(a))] for n, a in topn],
                         "unassigned_km2": round(float(qvol[0]))}
res["greenland_ice_pct"] = round(float(cice[cidx(["Greenland"])].sum() / cland[cidx(["Greenland"])].sum() * 100), 1)

json.dump(res, open(os.path.join(DATA, "results.json"), "w"), indent=1, default=float)
print(json.dumps({k: res[k] for k in ("uk_area_km2", "uk_top", "uk_era_share_gb", "oldest", "youngest_bedrock", "transect", "layer_cake_rho_ew",
                                       "layer_cake_rho_england_sed", "chalk", "coal", "superficial", "world", "world_era_share", "shields", "young_volcanic",
                                       "towns_by_period_pop_pct", "spots", "palaeogene_igneous_km2", "greenland_ice_pct")}, indent=1, default=float))
