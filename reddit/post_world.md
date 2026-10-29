## Title

[OC] How old is the ground under your feet? Every rock unit on a geological map of the world, coloured by the period it formed in: 24% of the world's land is more than 539 million years old, but 86% of Scandinavia is

## Body (optional)

I coloured every unit on Macrostrat's world geological map by geological period, using the international colours (pinks and reds for the oldest rock, yellows for the youngest), and reprojected it to Equal Earth.

The oldest rock sits in shields, the worn-down cores of the continents. On this map 23.8% of the world's dated, ice-free land is Precambrian, older than 539 million years. That rises to 86% of Norway, Sweden and Finland, 52% of Canada and 47% of India, but is just 9% of the United States and 9% of China. At the other end, 38% is Cenozoic, younger than 66 million years. Lava and ash from the last 2.6 million years cover about 825,000 km², mostly in the western United States, Arabia, the East African Rift and Mexico.

Caveat: this is a small-scale map (about 5 km pixels), stitched by Macrostrat from regional maps of very different detail, so you can see seams where they meet. A unit's period is the one containing the middle of its age range.

Interactive version, with the world and the British Isles, a time slider and "what's under your town": https://maps.tristanhotham.com/rocks-beneath/

## Source comment

Source: Macrostrat world geological map (carto tiles at zoom 4), compiled from the geological maps of North America, Europe (1:5 million), Africa, Australia and the Arctic, and a generalised geology of the world (CC BY 4.0). Hill shading from AWS Terrain Tiles. Shares are of dated, ice-free land.

Tools: Python (NumPy, Pillow, mapbox_vector_tile, matplotlib). Equal Earth projection.

Interactive: https://maps.tristanhotham.com/rocks-beneath/
Blog post: https://blog.tristanhotham.com/2026/10/28/rocks-beneath/
Data and code: https://github.com/Tristan-Hotham/rocks-beneath
