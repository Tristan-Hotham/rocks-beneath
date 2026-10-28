"""Sea layer for the page: a sea mask with a gentle depth shading.

Value per pixel: 0 = land, 1 to 255 = sea, coding depth on a log scale: 1 + 254 * log10(1 + d) / log10(1 + 6000), in 16 steps,
d = depth in metres from the AWS Terrain Tiles (terrarium, zoom 4; shallower than 1 m counts as 1 m).
World: land is Natural Earth 1:10m land drawn at zoom 5 (the same mask the world geology was clipped to);
one 512 px greyscale PNG per zoom-4 tile in data/sea/world/, plus a 2048 px overview.
British Isles: on the zoom-9 page grid, land is wherever the geology has a unit, and Natural Earth land
away from the British Isles (more than 15 km from any mapped unit, e.g. France); in data/sea/uk/,
one PNG per 512 px chunk, plus an overview at zoom 7. Inland lakes with no bedrock unit show as water.
"""
import base64, gzip, io, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

OUT = os.path.join(DATA, "sea")
for d in ("uk", "world"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, d)):
        os.remove(os.path.join(OUT, d, f))

# terrarium elevation at zoom 4 (4096 x 4096)
T = json.load(gzip.open(TERRARIUM))["tiles"]
E = np.zeros((4096, 4096), np.float32)
for k, b64 in T.items():
    z, x, y = map(int, k.split("/"))
    if z == 4:
        a = np.asarray(Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")).astype(np.float32)
        E[y * 256:(y + 1) * 256, x * 256:(x + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
D = np.clip(-E, 1, 6000)
CODE4 = (1 + 254 * np.log10(1 + D) / math.log10(6001)).astype(np.float32)   # zoom-4 pixels
del E, D
CODE4 = ndimage.gaussian_filter(CODE4, 2.5)


def code_at(gx, gy, z):
    """Depth code at global pixel centres (arrays) of zoom z, bilinear from the zoom-4 grid."""
    s = 2.0 ** (4 - z)
    x = (gx + .5) * s - .5; y = (gy + .5) * s - .5
    x0 = np.clip(np.floor(x).astype(int), 0, 4094); y0 = np.clip(np.floor(y).astype(int), 0, 4094)
    fx = np.clip(x - x0, 0, 1); fy = np.clip(y - y0, 0, 1)
    c = CODE4
    v = (c[y0, x0] * (1 - fx) + c[y0, x0 + 1] * fx) * (1 - fy) + (c[y0 + 1, x0] * (1 - fx) + c[y0 + 1, x0 + 1] * fx) * fy
    v = np.clip(np.round(v), 1, 255)
    return np.clip((v // 16) * 16 + 8, 1, 255).astype(np.uint8)        # 16 steps: plenty for a gentle shading, and small files


def land_mask(z, x0, y0, w, h):
    """Natural Earth 1:10m land on a pixel window of zoom z."""
    n = 256 * 2 ** z
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    land = json.load(open(os.path.join(NE, "ne_10m_land.geojson")))

    def pj(r):
        out = []
        for lon, lat in r:
            la = math.radians(max(-85, min(85, lat)))
            out.append(((lon + 180) / 360 * n - x0, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n - y0))
        return out
    for f in land["features"]:
        g = f["geometry"]
        for rings in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            d.polygon(pj(rings[0]), fill=1)
            for hh in rings[1:]:
                d.polygon(pj(hh), fill=0)
    return np.asarray(im, dtype=bool)


def save(arr, path):
    Image.fromarray(arr, "L").save(path, optimize=True)


# ---------------- world, zoom 5 pixels
N5 = 8192
L5 = land_mask(5, 0, 0, N5, N5)
tot = 0
for ty in range(16):
    gy = np.arange(ty * 512, (ty + 1) * 512)
    for tx in range(16):
        gx = np.arange(tx * 512, (tx + 1) * 512)
        GX, GY = np.meshgrid(gx, gy)
        c = code_at(GX, GY, 5)
        c[L5[ty * 512:(ty + 1) * 512, tx * 512:(tx + 1) * 512]] = 0
        p = os.path.join(OUT, "world", "c_%d_%d.png" % (tx, ty)); save(c, p); tot += os.path.getsize(p)
GX, GY = np.meshgrid(np.arange(2048), np.arange(2048))
ov = code_at(GX, GY, 3); ov[L5[2::4, 2::4]] = 0
save(ov, os.path.join(OUT, "world", "overview.png"))
del L5
print("world sea bytes", tot, os.path.getsize(os.path.join(OUT, "world", "overview.png")))

# ---------------- British Isles, zoom 9 page grid
UM = json.load(open(os.path.join(SCRATCH, "uk_meta.json")))
GX0, GY0, W, H = UM["gx0"], UM["gy0"], UM["w"], UM["h"]
bed = np.load(os.path.join(SCRATCH, "uk_grid.npz"))["bed"] > 0
ne = land_mask(9, GX0, GY0, W, H)
far = ndimage.distance_transform_edt(~bed) > 15000 / 175.0       # pixels more than about 15 km from mapped geology
landU = bed | (ne & far)
del ne, far
chunks = []; tot = 0
for cy in range(H // 512):
    gy = GY0 + np.arange(cy * 512, (cy + 1) * 512)
    for cx in range(W // 512):
        gx = GX0 + np.arange(cx * 512, (cx + 1) * 512)
        GX, GY = np.meshgrid(gx, gy)
        c = code_at(GX, GY, 9)
        c[landU[cy * 512:(cy + 1) * 512, cx * 512:(cx + 1) * 512]] = 0
        tx, ty = GX0 // 512 + cx, GY0 // 512 + cy
        p = os.path.join(OUT, "uk", "c_%d_%d.png" % (tx, ty)); save(c, p); tot += os.path.getsize(p); chunks.append([tx, ty])
GX, GY = np.meshgrid(GX0 // 4 + np.arange(W // 4), GY0 // 4 + np.arange(H // 4))
ov = code_at(GX, GY, 7); ov[landU[2::4, 2::4]] = 0
save(ov, os.path.join(OUT, "uk", "overview.png"))
json.dump({"uk_chunks": chunks, "world_tiles": [[x, y] for y in range(16) for x in range(16)],
           "about": "0 = land, 1 to 255 = sea depth code: 1 + 254 log10(1 + depth m) / log10(6001). Layout as data/uk/meta.json and data/world/meta.json."},
          open(os.path.join(OUT, "meta.json"), "w"))
print("uk sea bytes", tot, "chunks", len(chunks), os.path.getsize(os.path.join(OUT, "uk", "overview.png")))
