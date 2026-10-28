# The rocks beneath: an interactive geological map of the British Isles and the world

An interactive geological map of the British Isles and the world, coloured with a palette sampled from the index of the 1969 Geological Map of the British Islands (5th edition), with the international period colours, rock types and age as alternatives. Click or search any place for its rock, filter by age with a time slider (or press play and watch the islands build up, oldest rock first), isolate any colour, switch base maps, hill shading, names, faults, dykes and ice-age deposits, and find where else in the world has rocks the same age.

**Interactive version:** https://tristan-hotham.github.io/rocks-beneath/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23734962

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- Carboniferous rocks cover more of Great Britain than any other period: {{uk_top.period_pct|f1}}% of the land (then the Neoproterozoic {{uk_period_share.gb.NP|f1}}%, Cretaceous {{uk_period_share.gb.K|f1}}%, Jurassic {{uk_period_share.gb.J|f1}}%). The Carboniferous covers {{uk_carb_ireland_roi_pct|f1}}% of the Republic of Ireland; {{oldest.precambrian_pct_gb|f1}}% of Great Britain is Precambrian.
- The oldest rocks are the Lewisian gneisses of the Outer Hebrides and the north west Highlands, with protolith ages up to about {{oldest.max_age_ma|int}} million years (BGS Earthwise): {{oldest.lewisian_km2|int}} km², {{oldest.outer_hebrides_pct_of_lewisian|f1}}% of it in the Outer Hebrides. The youngest bedrock is the {{youngest_bedrock.0.name|raw}} of Norfolk and Suffolk ({{youngest_bedrock.0.km2|int}} km²).
- England's layer cake: from Scafell Pike to London ({{transect.lakes_london.km|int}} km) the rank correlation between distance and the age of the rock is {{transect.lakes_london.rho|f2}}; from Holyhead {{transect.anglesey_london.rho|f2}}. Across England and Wales, position along a north-west to south-east axis and age correlate at {{layer_cake_rho_ew|f2}}.
- The Coal Measures cover {{coal.gb_pct|f1}}% of Great Britain but carry {{coal.os_towns_on_cm|int}} of its {{coal.os_towns|int}} OS cities and towns ({{coal.os_towns_on_cm_pct|f1}}%, {{coal.ratio_towns_to_land|f1}} times their share of land) and {{coal.gn_pop_on_cm_pct|f1}}% of the population of its towns of 15,000 or more.
- The Chalk covers {{chalk.gb_pct|f1}}% of Great Britain and {{chalk.england_pct|f1}}% of England; Dover, Beachy Head, the Seven Sisters, Old Harry, Durdle Door and Flamborough Head all fall on the White Chalk Subgroup.
- Superficial deposits cover {{superficial.gb_pct|f1}}% of Great Britain's mapped land ({{superficial.scotland_pct|f1}}% of Scotland); till alone {{superficial.pct_till|f1}}%.
- World (Macrostrat, zoom 4): {{world_era_share.PC|f1}}% of the dated, ice-free land is Precambrian, from {{shields.Fennoscandia (Norway, Sweden, Finland)|f1}}% of Norway, Sweden and Finland and {{shields.Canada|f1}}% of Canada to {{shields.United States|f1}}% of the United States. Volcanic rocks younger than 2.6 million years cover {{young_volcanic.quaternary_km2|int}} km².

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## The 1969 palette

37 colour classes sampled from the index swatches of the 1969 map (median of the lighter pixels in a small box in each swatch), listed with their hex codes, the largest of today's units in each class and their shares of land in `data/uk_share_by_1969_class.csv` and in Table 3 of the paper. Units of the rock groups the 1969 map named take the group's colour (Chalk Group, Gault and Upper Greensand, Lower Greensand, Wealden, Inferior and Great Oolite and Ravenscar groups, Ancholme and Corallian groups with Portland and Purbeck, Lias, Mercia Mudstone, Sherwood Sandstone, Zechstein, the Coal Measures groups and Warwickshire Group, Millstone Grit and Culm, Old Red Sandstone by epoch, Torridon, Stoer and Sleat, Moine, Dalradian, Lewisian); other sedimentary units take the colour of their period; volcanic rocks are coloured by age and intrusions by composition. World units take the 1969 colour of their period and rock type (`code/06_build_site.py`, `c69_world`).

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page. Palettes, the British Isles unit table, results, coalfield towns, transects and label places are embedded; rasters and the other tables are fetched from `data/`. |
| `header.png` | Social card (1200 by 630). |
| `data/uk/u_<x>_<y>.png` | British Isles grid in Web Mercator at zoom 9 (about 175 m), in 512 px chunks named by zoom-8 tile: unit id = R + 256 G (`data/units_uk.csv`), B = superficial class. `h_<x>_<y>.jpg` hill shade; `overview.png` and `overview_h.jpg` at zoom 7; `meta.json` describes the layout. |
| `data/world/w_<x>_<y>.png` | World grid at zoom-5 pixels (about 4.9 km), one 512 px image per zoom-4 tile: unit id = R + 256 G (`data/units_world.csv`). Hill shade, overview and `meta.json` as above. |
| `data/units_uk.csv` | The {{n_units_uk.bgs|int}} BGS and {{n_units_uk.gsi|int}} GSI map units: name, group or setting, lithology, age text, oldest and youngest age (Ma), period, rock type, 1969 class, notes on assigned ages. |
| `data/units_world.csv` | The {{world.units|int}} Macrostrat legend entries: name, lithology, age, intervals, ages, period, rock type, source map. `units_world_page.json` is the compact copy the page loads. |
| `data/uk_unit_areas.csv` | Area of every British Isles unit (km²). |
| `data/uk_share_by_period.csv`, `uk_share_by_rock_type.csv`, `uk_share_by_1969_class.csv`, `uk_superficial_share.csv` | Shares of land for Great Britain, its nations, Northern Ireland, the Republic, the island of Ireland and the British Isles. |
| `data/world_share_by_period.csv`, `data/world_sources.csv` | World shares by period, and the six source maps behind the Macrostrat zoom-4 map with their share of mapped land. |
| `data/transect_lakes_london.csv`, `transect_anglesey_london.csv` | The rock every kilometre along the two lines. |
| `data/towns_on_coal_measures.csv` | OS Open Names cities and towns on the Coal Measures. |
| `data/uk_lines.json`, `data/world_lines.json` | Faults and dykes (simplified) for the map. |
| `data/places_gb.json`, `data/places_world.json` | Place search lists (OS Open Names; GeoNames). |
| `data/results.json` | Every number used anywhere. |
| `code/common.py` | Paths, time scale, palettes and classification rules. |
| `code/01_uk.py` | BGS and GSI units and the British Isles grid. |
| `code/02_world.py` | Macrostrat units, world grid and relief. |
| `code/03_uk_extras.py` | British Isles hill shading, faults and dykes. |
| `code/04_places.py` | Search and label places. |
| `code/05_analyse.py` | All statistics; writes `results.json` and the CSVs. |
| `code/06_build_site.py` | Fills `code/page_template.html` to make `index.html`, and checks facts stated in words. |
| `code/07_figures.py`, `code/08_header.py`, `code/figlib.py` | Static figures and social card (matplotlib). |
| `code/09_paper.py` | Builds the paper PDF from `code/paper_template.tex` with xelatex. |
| `code/10_release.py` | README, blog post, blog and Zenodo metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Grids.** Every bedrock polygon is drawn onto a Web Mercator grid (zoom 9 for the British Isles, about 175 m on the ground; zoom 5 for the world, about 4.9 km), largest polygons first, holes cleared. Areas are measured on the grids with each pixel weighted by its true ground area. The world grid is clipped to Natural Earth 1:10m land; lake, submarine and ocean-floor units are dropped and ice is counted separately.
- **Sources.** BGS Geology 625k for Great Britain, Northern Ireland and the Isle of Man (bedrock, superficial deposits, faults, dykes), from the BGS OGC API Features service; GSI/GSNI 1:500,000 bedrock for the Republic of Ireland (BGS wins where both exist); Macrostrat carto tiles at zoom 4 for the world.
- **Ages.** BGS ages as given (an older time scale: Carboniferous from 354 Ma). "Archaean" with no number is set to 3,200 Ma (the oldest Lewisian protolith age reported by BGS Earthwise), "Palaeoproterozoic" or "Proterozoic" to 2,500 Ma. GSI age brackets are converted with ICS boundaries rounded to the nearest million years. A unit's period contains the middle of its age range (Precambrian units of 1,000 Ma or more by their oldest age; the Warwickshire Group is set to the Carboniferous).
- **Rock types.** Grouped from the lithology descriptions into sandstone, mudstone, limestone, chalk, coal-bearing, soft sediments, intrusions, volcanic and metamorphic rocks (plus "sedimentary, not divided" and "other" for the world).
- **The page.** Chunks are recoloured in the browser for each palette, age filter and isolated class; zooming past the native grid smooths boundaries with the Scale2x rule. Hill shading is baked into the colours (AWS Terrain Tiles). In the world view the page progressively loads Macrostrat's live vector tiles at zoom 6 and closer (with Leaflet.VectorGrid) and asks Macrostrat's API for detail on a clicked spot; if either fails the bundled map is used and the page says so.

## What loads live on the page

Bundled: all geology, hill shading, names, faults, charts. Live from the internet: base maps (Esri Canvas, World Topo, World Imagery, Esri reference labels and World Hillshade; OpenStreetMap), Google Fonts, Leaflet 1.9.4 (cdnjs), and in the world view Leaflet.VectorGrid 1.3.0 (unpkg), Macrostrat live tiles (`https://tiles.macrostrat.org/carto/{z}/{x}/{y}`) and the Macrostrat API (`https://macrostrat.org/api/v2/geologic_units/map`).

## Known limits

- Small-scale maps: lines are generalised and small outcrops merged; the world map mixes six sources of very different detail and has seams where they meet.
- A unit's age is its stratigraphic range; a broad range is reduced to one period by its midpoint. BGS and GSI use different time scales and naming.
- Rock types and the mapping of today's units to the 1969 classes are my own judgements. The world shares include young unconsolidated sediments that the British bedrock maps treat as superficial.
- Superficial deposits are mapped here for Great Britain and Northern Ireland, not for the Republic of Ireland. Towns are points.

## How to rerun

Inputs are read in place (paths in `code/common.py`): `bgs625k.json.gz`, the GSI zip and `macrostrat_carto_z4.json.gz` (retrieved 28 October 2026), OS Open Names (`osnames_gb.tsv`, compact), GeoNames `cities15000.zip`, the AWS terrain tiles (zoom 10 for Britain and Ireland via `within-sight/code/dem.py`; zoom 4 for the world), Natural Earth and county outlines.

```
python3 code/01_uk.py
python3 code/02_world.py
python3 code/03_uk_extras.py
python3 code/04_places.py
python3 code/05_analyse.py
python3 code/06_build_site.py
FONT_DIR=path/to/fonts python3 code/07_figures.py
FONT_DIR=path/to/fonts python3 code/08_header.py
python3 code/09_paper.py
python3 code/10_release.py
```

Needs Python 3 with numpy, scipy, Pillow, pyproj, shapely, pyshp, mapbox_vector_tile and matplotlib, and xelatex with TeX Gyre Pagella and Inter for the paper.

## Sources and licences

- Bedrock and superficial geology of Great Britain, Northern Ireland and the Isle of Man: BGS Geology 625k (DiGMapGB-625), British Geological Survey, Open Government Licence. Contains British Geological Survey materials © UKRI 2026. Retrieved from https://ogcapi.bgs.ac.uk/.
- Bedrock geology of Ireland: Geological Survey Ireland and Geological Survey of Northern Ireland, 1:500,000 bedrock geology datasets. Contains Irish Public Sector Data (Geological Survey Ireland) licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) licence. Contains UK public sector information (Geological Survey of Northern Ireland) licensed under the UK Open Government Licence v3.0.
- World geology: Macrostrat (macrostrat.org), CC BY 4.0; Peters, Husson and Czaplewski (2018). Source maps: see `data/world_sources.csv`.
- Lewisian ages: BGS Earthwise, Bedrock Geology UK North: Archaean and Palaeoproterozoic.
- Palette: colours sampled from the index of the Geological Map of the British Islands, 5th edition (1969, K. C. Dunham, Director); the map is not reproduced.
- Places: OS Open Names, contains OS data © Crown copyright and database right 2026 (Open Government Licence v3.0); GeoNames cities15000 (CC BY 4.0). Relief: AWS Terrain Tiles (Mapzen terrarium). Land and countries: Natural Earth (public domain). Map library: Leaflet.

Derived data: CC BY 4.0 with the attributions above (see `LICENSE`). Text and figures: CC BY 4.0. Code: MIT.

## Citation

Hotham, T. (2026) The Rocks Beneath: An Interactive Geological Map of the British Isles and the World, in the Colours of the 1969 Survey. Zenodo. https://doi.org/10.5281/zenodo.23734962

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
