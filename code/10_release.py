"""Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files, and the
Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 code/10_release.py
"""
import importlib.util, json, os, re, shutil, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "06_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
b.check()
# numbers written into image alt text are checked here
assert f"{R['uk_top']['period_pct']:.1f}" == "17.5" and f"{R['uk_period_share']['ireland']['C']:.1f}" == "49.2"
assert f"{R['superficial']['pct_till']:.1f}" == "29.3" and f"{R['shields']['Fennoscandia (Norway, Sweden, Finland)']:.1f}" == "86.2"
assert round(R["transect"]["lakes_london"]["start_max_ma"]) == 458 and round(R["transect"]["anglesey_london"]["start_max_ma"]) == 505
rd = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", b.sub, open(os.path.join(HERE, "README_template.md"), encoding="utf-8").read())
for bad in ("\u2014", "\u2013", "--"):
    assert bad not in re.sub(r"^\|(---\|)+$", "", rd, flags=re.M), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(rd)
t = open(os.path.join(HERE, "blog_template.html"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "release", "blog", "post.html"), "w", encoding="utf-8").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = dict(
    title="The rocks beneath: a geological map in the colours of 1969",
    slug="rocks-beneath",
    excerpt=(f"An interactive geological map of the British Isles and the world, coloured with the palette of the 1969 Geological Map of the British Islands. "
             f"Carboniferous rocks cover {R['uk_top']['period_pct']:.1f}% of Great Britain, and England's layers get younger all the way to London."),
    seo_description="What lies under your town? An interactive geological map of Britain, Ireland and the world in the colours of the classic 1969 survey map.",
    tags=["geology", "maps", "British Geological Survey", "Geological Survey Ireland", "Macrostrat", "rocks", "data", "history of science"],
    header_alt=("Title card reading 'The rocks beneath' in black and brick red on warm paper, under a strip of coloured swatches, with a map of Britain and Ireland "
                "coloured in the 1969 survey palette: pale blue across central Ireland, pinks and yellows over the Highlands, a red band through the English Midlands "
                f"and yellow, green and grey green across the south and east. Text: from {R['oldest']['max_age_ma']:,} million-year-old Hebridean gneiss to the young sands of East Anglia."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in ("—", "–", "--"):
        assert bad not in str(v)
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_Rocks_Beneath"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex"), encoding="utf-8").read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = (ab.replace("\\%", "%").replace("\\&", "&").replace("Spearman's $\\rho$", "Spearman's rho").replace("$\\rho$", "rho").replace("$-$", "−")
      .replace("``", "\"").replace("''", "\"").replace("km\\textsuperscript{2}", "km²"))
assert "\\" not in ab and "$" not in ab, ab
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="The Rocks Beneath: An Interactive Geological Map of the British Isles and the World, in the Colours of the 1969 Survey",
    description_html=(f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/rocks-beneath/. Data and code: https://github.com/Tristan-Hotham/rocks-beneath. "
                      "Blog post: to follow.</p><p>Contains British Geological Survey materials © UKRI 2026 (BGS Geology 625k, DiGMapGB-625, Open Government Licence). "
                      "Contains Irish Public Sector Data (Geological Survey Ireland) licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) licence. "
                      "Contains UK public sector information (Geological Survey of Northern Ireland) licensed under the UK Open Government Licence v3.0. "
                      "World geology from Macrostrat (macrostrat.org), CC BY 4.0. Contains OS data © Crown copyright and database right 2026 (OGL v3) and GeoNames data (CC BY 4.0). "
                      "Colours were sampled from the index of the Geological Map of the British Islands, 5th edition (1969); the map itself is not reproduced. "
                      "Derived data, paper and figures: CC BY 4.0. Code: MIT.</p>"),
    keywords=["geology", "geological map", "British Geological Survey", "DiGMapGB-625", "Geological Survey Ireland", "Macrostrat", "stratigraphy", "cartography", "colour", "open data"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/rocks-beneath", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/rocks-beneath/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://ogcapi.bgs.ac.uk/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.gsi.ie/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://macrostrat.org/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://download.geonames.org/export/dump/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://registry.opendata.aws/terrain-tiles/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
    ])
for v in zmeta.values():
    for bad in ("—", "–", "--"):
        assert bad not in str(v)
for f in os.listdir(Z):
    os.remove(os.path.join(Z, f))
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ("units_uk.csv", "units_world.csv", "uk_unit_areas.csv", "uk_share_by_period.csv", "uk_share_by_rock_type.csv", "uk_share_by_1969_class.csv",
          "uk_superficial_share.csv", "world_share_by_period.csv", "world_sources.csv", "towns_on_coal_measures.csv", "transect_lakes_london.csv",
          "transect_anglesey_london.csv", "results.json"):
    shutil.copy(os.path.join(ROOT, "data", f), Z)
zp = os.path.join(Z, "rocks-beneath_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for top in ("code", "data"):
        for dp, dn, fn in os.walk(os.path.join(ROOT, top)):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in fn:
                if f in ("places_gb.json", "places_world.json", "units_world_page.json"):
                    continue   # search lists and the page's copy of units_world.csv: in the GitHub repo, left out here to keep the zip small
                p = os.path.join(dp, f); z.write(p, os.path.relpath(p, ROOT))
    for f in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, f), f)
print("blog words", words, "zenodo files", sorted(os.listdir(Z)), "zip MB", round(os.path.getsize(zp) / 1e6, 1))
