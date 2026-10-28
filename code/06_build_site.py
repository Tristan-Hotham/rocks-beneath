"""Build index.html from code/page_template.html, and the compact page tables.

Every number in the text is a {{path|format}} token filled from data/results.json. The palettes,
unit table for the British Isles, grid layout, coalfield towns, transects and label places are
embedded; the rasters, the world unit table, the fault lines and the search lists are fetched.
Run: python3 code/06_build_site.py
"""
import csv, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

R = json.load(open(os.path.join(DATA, "results.json"), encoding="utf-8"))
UM = json.load(open(os.path.join(SCRATCH, "uk_meta.json")))
WM = json.load(open(os.path.join(SCRATCH, "world_meta.json")))


def c69_world(per, rock, text):
    t = (text or "").upper()
    if per is None:
        return "XX"
    if rock == "vo":
        return {"Q": "VT", "N": "VT", "Pg": "VT", "K": "VC", "J": "VC", "T": "VC", "P": "VC", "C": "VC", "D": "VD", "S": "VL", "O": "VL", "Cm": "VL"}.get(per, "VP")
    if rock == "ii":
        return "IB" if any(w in t for w in ("MAFIC", "GABBRO", "DOLERITE", "BASIC", "ULTRAMAFIC", "SERPENTIN", "DIABASE", "PERIDOTITE")) else "IA"
    if rock == "mm":
        return "LW" if per in ("A", "PP") else "MO" if per in ("MP", "NP") else "MX"
    if per in ("Q", "N"):
        return "NQ"
    if per == "Pg":
        return "PG"
    if per == "K":
        return "CH" if rock in ("ch", "ls") else "UG" if rock == "md" else "LG"
    if per == "J":
        return "LI" if rock == "md" else "OL"
    if per == "T":
        return "KE" if rock == "md" else "BU"
    if per == "P":
        return "ML" if rock == "ls" else "PE"
    if per == "C":
        return "CM" if rock == "co" else "CL" if rock == "ls" else "MG"
    return {"D": "OR2", "S": "SI", "O": "OD", "Cm": "CA", "NP": "TO", "MP": "TO", "PP": "TO", "A": "TO"}.get(per, "XX")


def num(s):
    return None if s in ("", None) else round(float(s), 2)


# British Isles unit table (embedded)
UK = {"n": [], "g": [], "l": [], "a": [], "x": [], "m": [], "p": [], "r": [], "c": [], "s": []}
for r in csv.DictReader(open(os.path.join(DATA, "units_uk.csv"), encoding="utf-8")):
    UK["n"].append(r["name"]); UK["g"].append(r["group_or_setting"]); UK["l"].append(r["lithology"]); UK["a"].append(r["age_text"])
    UK["x"].append(num(r["max_age_ma"])); UK["m"].append(num(r["min_age_ma"]))
    UK["p"].append(PKEYS.index(r["period"]) if r["period"] else -1); UK["r"].append(RKEYS.index(r["rock_type"]))
    UK["c"].append(C69KEYS.index(r["class_1969"])); UK["s"].append(0 if r["source"] == "BGS" else 1)

# world unit table (fetched)
WU = {"n": [], "l": [], "a": [], "b": [], "t": [], "x": [], "m": [], "p": [], "r": [], "c": [], "f": [], "i": []}
c69w = {}
for r in csv.DictReader(open(os.path.join(DATA, "units_world.csv"), encoding="utf-8")):
    per = r["period"] or None
    c = c69_world(per, r["rock_type"], r["lithology"] + " " + r["name"])
    c69w[c] = c69w.get(c, 0) + 1
    WU["n"].append(r["name"]); WU["l"].append(r["lithology"][:110]); WU["a"].append(r["age_text"]); WU["b"].append(r["oldest_interval"]); WU["t"].append(r["youngest_interval"])
    WU["x"].append(num(r["max_age_ma"])); WU["m"].append(num(r["min_age_ma"])); WU["p"].append(PKEYS.index(per) if per else -1)
    WU["r"].append(RKEYS.index(r["rock_type"])); WU["c"].append(C69KEYS.index(c)); WU["f"].append(int(r["source_ref"])); WU["i"].append(int(r["ice"]))
json.dump(WU, open(os.path.join(DATA, "units_world_page.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
srcs = [dict(r) for r in csv.DictReader(open(os.path.join(DATA, "world_sources.csv"), encoding="utf-8"))]

PAL = {"periods": [[p[0], p[1], p[2], p[3], p[4], p[5]] for p in PERIODS], "eras": ERAS,
       "c69": [[c[0], c[1], c[2], c[3]] for c in C1969], "rock": [[r[0], r[1], r[2]] for r in ROCK],
       "sup": [[s[0], s[1], s[2]] for s in SUPER], "ctx_uk": CONTEXT_UK, "ctx_world": CONTEXT_WORLD}
GRIDS = {"uk": {"nz": UM["z"], "ox": UM["gx0"], "oy": UM["gy0"], "w": UM["w"], "h": UM["h"], "chunks": UM["chunks"], "dir": "data/uk/", "pre": "u_"},
         "world": {"nz": WM["tz"] + 1, "ox": 0, "oy": 0, "w": 2 ** WM["tz"] * WM["res"], "h": 2 ** WM["tz"] * WM["res"], "chunks": WM["tiles"], "dir": "data/world/", "pre": "w_"}}

# label places: GB cities and towns (OS Open Names); Ireland and Northern Ireland (GeoNames 15,000+)
gbp = json.load(open(os.path.join(DATA, "places_gb.json"), encoding="utf-8"))
LBL = [[p[0], p[2], p[3], p[4]] for p in gbp if p[4] >= 2]
wp = json.load(open(os.path.join(DATA, "places_world.json"), encoding="utf-8"))
for p in wp["places"]:
    if p[1] in ("IE", "GB-NIR"):
        LBL.append([p[0], p[2], p[3], 3 if p[4] >= 100 else 2])
coal = [[r["name"], round(float(r["lat"]), 3), round(float(r["lon"]), 3)] for r in csv.DictReader(open(os.path.join(DATA, "towns_on_coal_measures.csv"), encoding="utf-8"))]


def tr(name):
    out = []
    for r in csv.DictReader(open(os.path.join(DATA, "transect_%s.csv" % name), encoding="utf-8")):
        out.append([float(r["km"]), int(r["unit_id"])])
    return out


TR = {"lakes_london": tr("lakes_london"), "anglesey_london": tr("anglesey_london")}


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw":
        return str(v)
    if f == "int":
        return f"{round(v):,}"
    if f == "f1":
        return f"{v:.1f}"
    if f == "f2":
        return f"{v:.2f}".replace("-", "−")
    if f == "pname":
        return {p[0]: p[1] for p in PERIODS}[v]
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1)), m.group(3))


def check():
    """Facts the page, paper and blog state in words."""
    assert R["uk_top"]["period"] == "C" and R["uk_top"]["rock"] == "md"
    assert R["spots"]["Butt of Lewis"]["name"] == "Lewisian Complex"
    assert R["spots"]["London"]["name"] == "Thames Group"
    assert R["spots"]["Scafell Pike"]["period"] == "O"
    y = R["youngest_bedrock"][0]
    assert y["max_ma"] < 24 and 52 < y["lat"] < 53 and y["lon"] > 1  # Norfolk and Suffolk
    assert all(v == "White Chalk Subgroup" for v in R["chalk"]["spots"].values())
    assert {"Sheffield", "Leeds", "Swansea", "Wigan"} <= set(R["coal"]["gn_examples"])
    t = R["transect"]["lakes_london"]
    assert t["start_period"] == "O" and t["end_period"] == "Pg" and t["rho"] < -0.8
    sh = R["shields"]
    assert max(sh, key=lambda k: sh[k]).startswith("Fennoscandia")
    yq = [x[0] for x in R["young_volcanic"]["top_quaternary"][:5]]
    assert {"Saudi Arabia", "Ethiopia", "Kenya"} <= set(yq)
    tp = R["towns_by_period_pop_pct"]
    assert list(tp)[:2] == ["Pg", "C"]
    pg = R["palaeogene_igneous_km2"]
    assert pg["ni"] > pg["gb"]


if __name__ == "__main__":
    check()
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", sub, tpl)
    slim = {k: v for k, v in R.items() if k not in ("world_age_hist",)}
    for k, v in (("RESULTS", slim), ("PAL", PAL), ("GRIDS", GRIDS), ("UNITS_UK", UK), ("LABELS", LBL), ("COAL", coal), ("TRANSECTS", TR), ("SOURCES", srcs),
                 ("AGEHIST", R["world_age_hist"])):
        html = html.replace("/*%s*/" % k, json.dumps(v, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in html and "/*RESULTS*/" not in html
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    for bad in ("—", "–"):
        assert bad not in html, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes; world units json", os.path.getsize(os.path.join(DATA, "units_world_page.json")), "c69 world", c69w)
