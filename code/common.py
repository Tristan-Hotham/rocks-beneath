"""Shared settings for The rocks beneath: paths, the geological time scale, the palettes
and the rules that put each map unit into a period, a rock type and a 1969 class.

Inputs are read in place (nothing is copied into the project):
  BGS Geology 625k (DiGMapGB-625), Open Government Licence v3
  Geological Survey Ireland / GSNI 1:500k bedrock, CC BY 4.0 / OGL v3
  Macrostrat carto vector tiles at zoom 4, CC BY 4.0
"""
import math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
SRC = "/home/claude/hist/_data14"
BGS = os.path.join(SRC, "bgs625k.json.gz")
GSI_ZIP = os.path.join(SRC, "IE_GSI_GSNI_Bedrock_Geology_Datasets_500K_IE32_ITM.zip")
MACRO = os.path.join(SRC, "macrostrat_carto_z4.json.gz")
OSNAMES = "/home/claude/hist/osnames_gb.tsv"
GEONAMES = "/home/claude/hist/_data13/cities15000.zip"
TERRARIUM = "/home/claude/hist/_data13/terrarium_tiles.json.gz"
NE = "/home/claude/hist/_data3/ne/geojson"
COUNTIES = "/home/claude/hist/how-roman-is-your-road/data/counties.geojson"
SCRATCH = os.environ.get("RB_SCRATCH", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/rb")

# ---------------------------------------------------------------------------
# Time scale. Boundaries in millions of years (Ma), rounded to the nearest
# million years from the International Chronostratigraphic Chart (ICS).
# Colours: the standard ICS / CGMW period colours.
PERIODS = [  # key, name, start (older) Ma, end (younger) Ma, ICS colour, era key
    ("Q", "Quaternary", 2.58, 0, "#F9F97F", "CZ"),
    ("N", "Neogene", 23, 2.58, "#FFE619", "CZ"),
    ("Pg", "Palaeogene", 66, 23, "#FD9A52", "CZ"),
    ("K", "Cretaceous", 145, 66, "#7FC64E", "MZ"),
    ("J", "Jurassic", 201, 145, "#34B2C9", "MZ"),
    ("T", "Triassic", 252, 201, "#812B92", "MZ"),
    ("P", "Permian", 299, 252, "#F04028", "PZ"),
    ("C", "Carboniferous", 359, 299, "#67A599", "PZ"),
    ("D", "Devonian", 419, 359, "#CB8C37", "PZ"),
    ("S", "Silurian", 444, 419, "#B3E1B6", "PZ"),
    ("O", "Ordovician", 485, 444, "#009270", "PZ"),
    ("Cm", "Cambrian", 539, 485, "#7FA056", "PZ"),
    ("NP", "Neoproterozoic", 1000, 539, "#FEB342", "PC"),
    ("MP", "Mesoproterozoic", 1600, 1000, "#FDB462", "PC"),
    ("PP", "Palaeoproterozoic", 2500, 1600, "#F74370", "PC"),
    ("A", "Archaean", 4000, 2500, "#F0047F", "PC"),
]
PKEYS = [p[0] for p in PERIODS]
ERAS = [("CZ", "Cenozoic", 66, 0), ("MZ", "Mesozoic", 252, 66), ("PZ", "Palaeozoic", 539, 252), ("PC", "Precambrian", 4000, 539)]

# The BGS 625k ages use an older time scale (for example the Carboniferous begins
# at 354 Ma and the Permian at 290 Ma). BGS units are put into periods on that
# scale, so that each unit lands in the period BGS names for it.
BGS_BOUNDS = [("Q", 1.8), ("N", 23.8), ("Pg", 65), ("K", 142), ("J", 205.7), ("T", 248.2), ("P", 290),
              ("C", 354), ("D", 417), ("S", 443), ("O", 495), ("Cm", 545), ("NP", 1000), ("MP", 1600), ("PP", 2500), ("A", 1e9)]
ICS_BOUNDS = [(p[0], p[2]) for p in PERIODS]


def period_of(age_ma, bounds=ICS_BOUNDS):
    for k, start in bounds:
        if age_ma <= start:
            return k
    return "A"


def era_of_period(k):
    return {p[0]: p[5] for p in PERIODS}[k]


# Plain-words context for each period (kept short, modest and standard).
CONTEXT_UK = {
    "Q": "the ice ages: glaciers came and went, and Britain took its present shape",
    "N": "the climate was cooling and Britain sat close to where it is now",
    "Pg": "the North Atlantic was opening; volcanoes erupted on Skye, Mull and in Antrim, and the London Clay was laid down in a warm sea",
    "K": "sea levels were high and the chalk built up on the sea floor from the shells of microscopic algae",
    "J": "warm shallow seas covered much of England, home to ammonites and marine reptiles",
    "T": "Britain lay inside the supercontinent Pangaea, in a hot, dry belt of red deserts and salt lakes",
    "P": "Britain was a desert in the middle of Pangaea, with a shallow salty sea (the Zechstein Sea) to the east",
    "C": "Britain lay near the equator: warm seas laid down limestone, then swampy forests became coal",
    "D": "the Old Red Sandstone was laid down by rivers in a hot land south of the equator, with early fishes in its lakes",
    "S": "the Iapetus Ocean closed and the two halves of Britain met; the first plants were spreading onto land",
    "O": "England and Wales lay on a small continent far south of Scotland across the Iapetus Ocean, with volcanoes along its edges",
    "Cm": "animals with shells and skeletons were appearing; Britain was in two pieces on opposite sides of the Iapetus Ocean",
    "NP": "life was still mostly microscopic; rivers laid down the Torridonian sandstones and the world went through great ice ages",
    "MP": "life was microscopic; these rocks were later buried and changed by heat and pressure",
    "PP": "life was microscopic; the crust of what became north-west Scotland was being reworked deep underground",
    "A": "the Earth was less than half its present age and life was only microbial; these gneisses formed deep in an early crust",
}
CONTEXT_WORLD = {
    "Q": "the ice ages, when ice sheets came and went",
    "N": "the climate was cooling and the continents were close to where they are now",
    "Pg": "after the extinction of the dinosaurs, mammals spread and the Atlantic kept widening",
    "K": "dinosaurs still lived, sea levels were high and flowering plants appeared",
    "J": "dinosaurs lived on land, and Pangaea was breaking apart",
    "T": "the continents formed one supercontinent, Pangaea, and the first dinosaurs appeared",
    "P": "Pangaea was assembled; the period ended with the largest mass extinction known",
    "C": "great coal forests grew, and the first reptiles appeared",
    "D": "the age of fishes; forests and four-legged animals first appeared",
    "S": "plants were spreading onto land",
    "O": "life in the sea diversified quickly",
    "Cm": "animals with shells and skeletons appeared in large numbers",
    "NP": "life was mostly microscopic; there were worldwide ice ages and the first large soft-bodied animals",
    "MP": "life was microscopic; complex cells were spreading",
    "PP": "oxygen was building up in the air and the first complex cells appeared",
    "A": "the Earth was young and life was only microbial",
}

# ---------------------------------------------------------------------------
# The "1969 survey" palette: colours sampled from the index swatches of the
# 1969 Geological Map of the British Islands (5th edition). Only the colours are
# used; nothing of the map itself.
C1969 = [  # key, label, hex, group
    ("NQ", "Pleistocene (marine) and Pliocene", "#E59055", "sed"),
    ("PG", "Oligocene and Eocene (Palaeogene)", "#C79E93", "sed"),
    ("CH", "Chalk", "#C9CB96", "sed"),
    ("UG", "Upper Greensand and Gault", "#428468", "sed"),
    ("LG", "Lower Greensand", "#CBB74D", "sed"),
    ("WE", "Wealden", "#50962B", "sed"),
    ("OU", "Upper Oolite (Upper Jurassic clays and limestones)", "#B4A231", "sed"),
    ("OL", "Lower Oolite (Middle Jurassic)", "#E9C833", "sed"),
    ("LI", "Lias and Rhaetic", "#C04B27", "sed"),
    ("KE", "Keuper Marl and Sandstone (Mercia Mudstone)", "#E36140", "sed"),
    ("BU", "Bunter Sandstone (Sherwood Sandstone)", "#E99946", "sed"),
    ("PE", "Permian Marl and Permo-Triassic Sandstone", "#DA8E15", "sed"),
    ("ML", "Magnesian Limestone", "#048ED7", "sed"),
    ("CM", "Coal Measures", "#ADAEAF", "sed"),
    ("MG", "Millstone Grit and Culm", "#EEDFAA", "sed"),
    ("CL", "Carboniferous Limestone", "#A7DCF5", "sed"),
    ("OR3", "Upper Old Red Sandstone", "#ECCFC7", "sed"),
    ("OR2", "Middle Old Red Sandstone", "#EBA372", "sed"),
    ("OR1", "Lower Old Red Sandstone", "#D99A75", "sed"),
    ("SI", "Silurian", "#C4B7D9", "sed"),
    ("OD", "Ordovician", "#ECDEE8", "sed"),
    ("CA", "Cambrian", "#AA9BCA", "sed"),
    ("TO", "Torridonian, Charnian and Longmyndian", "#DD9A72", "sed"),
    ("DU", "Upper Dalradian", "#DED68E", "meta"),
    ("DL", "Lower Dalradian", "#F5DCE7", "meta"),
    ("MO", "Moine", "#FCE192", "meta"),
    ("LW", "Lewisian", "#EEB0A3", "meta"),
    ("MX", "Other metamorphic rocks", "#F8DBE3", "meta"),
    ("HB", "Hornblende schist and amphibolite", "#B0CE83", "meta"),
    ("GG", "Granite gneiss", "#F59338", "meta"),
    ("VT", "Volcanic rocks: Tertiary (Palaeogene)", "#F68794", "ign"),
    ("VC", "Volcanic rocks: Permian and Carboniferous", "#F98597", "ign"),
    ("VD", "Volcanic rocks: Devonian", "#F2CBC5", "ign"),
    ("VL", "Volcanic rocks: Lower Palaeozoic", "#F3C7C8", "ign"),
    ("VP", "Volcanic rocks: Precambrian", "#B2CE69", "ign"),
    ("IB", "Basic intrusions (dolerite, gabbro, serpentine)", "#67935D", "ign"),
    ("IA", "Acid intrusions (granite, diorite, felsite)", "#F36D09", "ign"),
    ("XX", "Not classified", "#C8C4BC", "other"),
]
C69KEYS = [c[0] for c in C1969]

# Rock types (my own colours).
ROCK = [
    ("ss", "Sandstone and conglomerate", "#E3B65E"),
    ("md", "Mudstone, siltstone and shale", "#9FB08A"),
    ("ls", "Limestone and dolomite", "#6FAFD6"),
    ("ch", "Chalk", "#EDE7BF"),
    ("co", "Coal-bearing rocks", "#4D4B4B"),
    ("sf", "Clay, sand and gravel (soft sediments)", "#E8CFA6"),
    ("ii", "Igneous intrusions", "#D2453A"),
    ("vo", "Volcanic rocks", "#8B5A9E"),
    ("mm", "Metamorphic rocks", "#D79AB8"),
    ("sd", "Sedimentary rocks, not divided", "#C9B99A"),
    ("ot", "Other or unknown", "#BDB8AE"),
]
RKEYS = [r[0] for r in ROCK]

# Superficial deposits (BGS 625k), drawn over the bedrock when switched on.
SUPER = [  # key, label, hex, match on BGS lex_d
    ("till", "Till (boulder clay)", "#BFCCD8", ["TILL"]),
    ("gsg", "Glacial sand and gravel", "#E8C79E", ["GLACIAL SAND AND GRAVEL"]),
    ("alv", "Alluvium", "#F2E8A6", ["ALLUVIUM"]),
    ("rtd", "River terrace deposits", "#E1D08A", ["RIVER TERRACE"]),
    ("peat", "Peat", "#8E6B50", ["PEAT"]),
    ("bsa", "Blown sand", "#F6E3A0", ["BLOWN SAND"]),
    ("rmd", "Raised marine deposits", "#B9DACF", ["RAISED MARINE"]),
    ("cwf", "Clay-with-flints", "#C49C77", ["CLAY-WITH-FLINTS"]),
    ("brk", "Brickearth", "#D7B68C", ["BRICKEARTH"]),
    ("lac", "Lake deposits", "#A6C4DF", ["LACUSTRINE"]),
    ("lsl", "Landslip", "#D69A9A", ["LANDSLIP"]),
    ("crag", "Crag Group (shelly sands)", "#E59055", ["CRAG GROUP"]),
    ("sgu", "Sand and gravel of uncertain origin", "#DCCBA6", ["SAND AND GRAVEL OF UNCERTAIN"]),
]
SKEYS = [s[0] for s in SUPER]


def super_class(lex_d):
    for k, _, _, pats in SUPER:
        if any(p in lex_d for p in pats):
            return k
    return None  # "drift geology not mapped" and anything unknown


# ---------------------------------------------------------------------------
# Rock type from a lithology text (BGS rcs_d, GSI unit name, Macrostrat lith).
IGN_INTR = ["IGNEOUS-ROCK", "FELSIC-ROCK", "MAFITE", "ULTRAMAFITITE", "SYENITIC", "ANORTHOSITE", "DOLERITE",
            "GRANITE", "GRANODIORITE", "GABBRO", "DIORITE", "TONALITE", "PORPHYRY", "APPINITE", "SERPENTINITE", "PLUTONIC", "INTRUSIVE"]
VOLC = ["LAVA", "TUFF", "VOLCANIC", "BASALT", "ANDESITE", "RHYOLITE", "TRACHYTE", "DACITE", "IGNIMBRITE", "PYROCLASTIC"]
META = ["GNEISS", "SCHIST", "PSAMMITE", "PELITE", "QUARTZITE", "METALIMESTONE", "MIGMATIT", "METASEDIMENTARY", "MYLONITIC",
        "PHYLLITE", "AMPHIBOLITE", "MARBLE", "SLATE", "METAMORPHIC", "HORNBLENDE", "CALCSILICATE", "METABRECCIA", "GRANULITE", "METAVOLCANIC", "META-"]


def rock_from_text(t, intrusion=False):
    t = (t or "").upper()
    if "COAL" in t or "LIGNITE" in t:
        return "co"
    if intrusion:
        if any(w in t for w in ["LAVA", "TUFF"]):
            return "vo"
        return "ii"
    if any(w in t for w in META):
        return "mm"
    if any(w in t for w in VOLC):
        return "vo"
    if any(w in t for w in IGN_INTR):
        return "ii"
    if t.startswith("CHALK") or t == "CHALK":
        return "ch"
    first = re.split(r"[ ,;&]+", t.strip())[0] if t.strip() else ""
    if first in ("LIMESTONE", "DOLOSTONE", "DOLOMITISED", "DOLOMITE", "CARBONATE", "MARL"):
        return "ls"
    if first in ("SANDSTONE", "CONGLOMERATE", "BRECCIA", "QUARTZ-ARENITE", "WACKE", "GREYWACKE", "ARKOSE", "GRIT"):
        return "ss"
    if first in ("MUDSTONE", "SILTSTONE", "SHALE", "CLAYSTONE", "ARGILLITE"):
        return "md"
    if first in ("CLAY", "SAND", "GRAVEL", "SILT", "ALLUVIUM", "PEAT", "TILL"):
        return "sf"
    if "SEDIMENTARY ROCK CYCLES" in t:
        return "ls"
    if "LIMESTONE" in t:
        return "ls"
    if "SANDSTONE" in t:
        return "ss"
    if "MUDSTONE" in t or "SHALE" in t:
        return "md"
    return "ot"


# ---------------------------------------------------------------------------
# Web Mercator helpers (EPSG:3857 pixel space, 256 px tiles).
def lonlat_to_px(lon, lat, z):
    n = 256 * 2 ** z
    x = (lon + 180.0) / 360.0 * n
    la = math.radians(lat)
    y = (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n
    return x, y


def px_to_lonlat(x, y, z):
    n = 256 * 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


def clean(s):
    """No dashes in visible text: en and em dashes become 'to' or commas."""
    s = s.replace("—", ", ").replace("–", " to ").replace("--", " to ")
    return re.sub(r"\s+", " ", s).strip()
