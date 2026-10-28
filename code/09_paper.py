"""Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Rocks_Beneath.tex and compile it with xelatex (figures from 07_figures.py).
Run: python3 code/09_paper.py
"""
import csv, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

R = json.load(open(os.path.join(DATA, "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Rocks_Beneath"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


tex = lambda s: str(s).replace("\\", "/").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}".replace("-", "$-$")
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


P = R["uk_period_share"]
rows = ""
for p in PERIODS:
    sw = f"\\textcolor[HTML]{{{p[4][1:]}}}{{\\rule{{1.1em}}{{0.75em}}}}"
    vals = [P["gb"][p[0]], P["england"][p[0]], P["wales"][p[0]], P["scotland"][p[0]], P["ireland"][p[0]], R["world_period_share"][p[0]]]
    rows += f"{sw} {p[1]} & {p[2]:g} to {p[3]:g} & " + " & ".join(f"{v:.1f}" for v in vals) + "\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{Share of the land on each period (\\%), with the period's span in millions of years (ICS, rounded). "
      "Great Britain and its nations from BGS Geology 625k; the island of Ireland from GSI (Republic) and BGS (Northern Ireland); the world's dated, ice-free land from Macrostrat at zoom 4.}\\label{tab:periods}"
      "\\begin{tabular}{llrrrrrr}\\toprule Period & Ma & GB & England & Wales & Scotland & Ireland & World\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
src = list(csv.DictReader(open(os.path.join(DATA, "world_sources.csv"), encoding="utf-8")))
src.sort(key=lambda r: -float(r["pct_of_mapped_land"]))
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{The source maps behind Macrostrat's zoom-4 world map, with their share of the mapped land on the grid.}\\label{tab:sources}"
      "\\begin{tabular}{p{4.2cm}p{8.4cm}r}\\toprule Macrostrat name & Source & \\%\\\\\\midrule\n" +
      "".join(f"{tex(r['short_name'])} & {tex(r['authors'])} ({tex(r['year'])}) {tex(r['title'])} & {float(r['pct_of_mapped_land']):.1f}\\\\\n" for r in src) +
      "\\bottomrule\\end{tabular}\\end{table}")
RS = "".join(f"\\item {tex(r['authors'].rstrip(','))} ({tex(r['year'])}) {tex(r['title'])}. {tex(r['publisher'])}." + (f" {tex(r['isbn_or_doi'])}." if r['isbn_or_doi'] else "") + " Via Macrostrat, CC BY 4.0.\n" for r in sorted(src, key=lambda r: r["authors"]))
ex = R["c69_examples"]; sh = R["uk_1969_share"]
rows = ""
for c in C1969:
    if c[0] == "XX":
        continue
    sw = f"\\textcolor[HTML]{{{c[2][1:]}}}{{\\rule{{1.6em}}{{0.9em}}}}"
    rows += f"{sw} & {tex(c[1])} & \\texttt{{{tex(c[2])}}} & {tex('; '.join(ex.get(c[0], [])[:2]))} & {sh['gb'][c[0]]:.1f} & {sh['ireland'][c[0]]:.1f}\\\\\n"
TPAL = ("{\\scriptsize\\renewcommand{\\arraystretch}{0.88}\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{lp{4.0cm}lp{7.4cm}rr}\\caption{The 1969 palette: the 37 classes, their colours as sampled from the index of the 1969 map, "
        "the largest of today's units given each colour, and each class's share of the land of Great Britain and the island of Ireland (\\%).}\\label{tab:palette}\\\\"
        "\\toprule & Class & Colour & Largest units & GB & Ireland\\\\\\midrule\\endfirsthead\\toprule & Class & Colour & Largest units & GB & Ireland\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
t = open(os.path.join(HERE, "paper_template.tex"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!TABLE_|REFS_)(.+?)\}\}", sub, t)
t = t.replace("{{TABLE_PERIODS}}", TP).replace("{{TABLE_SOURCES}}", TS).replace("{{REFS_SOURCES}}", RS).replace("{{TABLE_PALETTE}}", TPAL)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print("\n".join(l for l in open(os.path.join(OUT, NAME + ".log"), errors="ignore") if l.startswith("!") or "Overfull" in l)[:3000])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
os.remove(os.path.join(OUT, NAME + ".pdf"))
print("paper written", r.returncode)
