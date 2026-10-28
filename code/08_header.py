"""Social card: header.png, 1200 by 630.
Run: FONT_DIR=/path/to/fonts python3 code/08_header.py
"""
from figlib import *

bed, sup, hill, x0, y0, z = load_uk("overview")
fig = plt.figure(figsize=(6, 3.15), dpi=200)
ax = fig.add_axes([.58, .015, .41, .97]); ax.set_anchor("C")
rgba = uk_rgba(bed, hill, "c69", k=.45)
mapax(ax, rgba, x0, y0, z)
# crop to the British Isles
xa, ya = merc(-10.7, 60.95, z); xb, yb = merc(2.0, 49.85, z)
ax.set_xlim(xa, xb); ax.set_ylim(yb, ya)
# strata strip
sx = fig.add_axes([.055, .905, .42, .022]); sx.set_axis_off()
cols = [h2rgb(c[2]) for c in C1969 if c[3] == "sed"]
sx.imshow(np.array([cols]), aspect="auto", extent=(0, 1, 0, 1)); sx.set_xlim(0, 1)
fig.text(.055, .845, "DATA STUDY  ·  GEOLOGY  ·  BRITISH ISLES AND THE WORLD", family=MONO, fontsize=5.6, color=MUT)
fig.text(.05, .80, "The rocks", fontproperties=DISP, fontsize=36, color=FG, va="top")
fig.text(.05, .60, "beneath", fontproperties=DISP, fontsize=36, color=RED, va="top")
fig.text(.055, .385, "An interactive geological map in the colours of\nthe 1969 Geological Map of the British Islands:\n"
         f"from {R['oldest']['max_age_ma']:,} million-year-old Hebridean gneiss to the\nyoung sands of East Anglia, and the world beyond.",
         family=SER, fontsize=8.2, color=FG, va="top", linespacing=1.15)
fig.text(.055, .06, "Dr Tristan Hotham · Independent researcher", family=MONO, fontsize=6, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=200)
print("header.png written")
