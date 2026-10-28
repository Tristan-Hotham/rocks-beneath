"""Place names for search and map labels.

Great Britain: OS Open Names cities, towns and villages (rank 3, 2, 1).
Ireland and the world: GeoNames cities15000 (places of 15,000 or more people).
Writes data/places_gb.json and data/places_world.json (compact lists).
"""
import csv, io, json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

RANK = {"City": 3, "Town": 2, "Village": 1}
gb = []
seen = set()
with open(OSNAMES, encoding="utf-8") as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        if r["type"] != "populatedPlace" or r["local_type"] not in RANK:
            continue
        nm = r["name1"]
        area = r["county"] or r["district"] or r["region"]
        k = (nm, area)
        if k in seen:
            continue
        seen.add(k)
        gb.append([nm, area, round(float(r["lat"]), 4), round(float(r["lon"]), 4), RANK[r["local_type"]]])
gb.sort(key=lambda p: (-p[4], p[0]))
json.dump(gb, open(os.path.join(DATA, "places_gb.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("GB places", len(gb), os.path.getsize(os.path.join(DATA, "places_gb.json")))

ne = json.load(open(os.path.join(NE, "ne_50m_admin_0_countries.geojson")))
cname = {}
for f in ne["features"]:
    p = f["properties"]
    for k in ("ISO_A2", "ISO_A2_EH", "WB_A2"):
        if p.get(k) and p[k] != "-99":
            cname.setdefault(p[k], p.get("NAME"))
cname.update({"GB": "United Kingdom", "IE": "Ireland", "XK": "Kosovo"})
world = []
with zipfile.ZipFile(GEONAMES) as z:
    for line in io.TextIOWrapper(z.open("cities15000.txt"), encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if c[7] in ("PPLX",):
            continue
        cc = c[8]
        world.append([c[1], cc, round(float(c[4]), 3), round(float(c[5]), 3), int(c[14] or 0), c[10]])
world.sort(key=lambda p: -p[4])
out = {"countries": {k: v for k, v in cname.items() if any(p[1] == k for p in world[:1])} , "places": []}
codes = sorted({p[1] for p in world})
out["countries"] = {k: cname.get(k, k) for k in codes}
# place list: name, country code, lat, lon, population in thousands; NIR flag for Northern Ireland
out["places"] = [[p[0], p[1] + ("-NIR" if p[1] == "GB" and p[5] == "NIR" else ""), p[2], p[3], round(p[4] / 1000)] for p in world]
json.dump(out, open(os.path.join(DATA, "places_world.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("world places", len(world), os.path.getsize(os.path.join(DATA, "places_world.json")))
