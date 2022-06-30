import numpy as np
import math
from PIL import Image
from tqdm import tqdm
from matplotlib import pyplot as plt
from io import BytesIO
from itertools import product
from functools import cache
import requests

URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png".format


@cache
def get_tile(x, y, z):
    return Image.open(BytesIO(requests.get(URL(x=x, y=y, z=z)).content))


def point_to_pixels(lon, lat, zoom, TILE_SIZE):
    """convert gps coordinates to web mercator"""
    r = math.pow(2, zoom) * TILE_SIZE
    lat = math.radians(lat)

    x = int((lon + 180.0) / 360.0 * r)
    y = int((1.0 - math.log(math.tan(lat) + (1.0 / math.cos(lat))) / math.pi) / 2.0 * r)

    return x, y


def plot_payload(lats, lngs, s=200, alpha=1, figsize=(25, 16), c="red", TILE_SIZE=256, max_total=30):
    # bikes = np.array([p["rentalObjectCount"]["bike"] for p in payload])
    # lats = np.array([p["position"]["lat"] for p in payload])
    # lngs = np.array([p["position"]["lng"] for p in payload])

    top = np.max(lats)
    bot = np.min(lats)
    lef = np.min(lngs)
    rgt = np.max(lngs)

    for zoom in range(20, 4, -1):
        x0, y0 = point_to_pixels(lef, top, zoom, TILE_SIZE)
        x1, y1 = point_to_pixels(rgt, bot, zoom, TILE_SIZE)

        x0_tile, y0_tile = int(x0 / TILE_SIZE), int(y0 / TILE_SIZE)
        x1_tile, y1_tile = math.ceil(x1 / TILE_SIZE), math.ceil(y1 / TILE_SIZE)

        total = (x1_tile - x0_tile) * (y1_tile - y0_tile)
        if total < max_total:
            break

    img = Image.new(mode="RGB", size=((x1_tile - x0_tile) * TILE_SIZE, (y1_tile - y0_tile) * TILE_SIZE))

    # loop through every tile inside our bounded box
    for x_tile, y_tile in tqdm(product(range(x0_tile, x1_tile), range(y0_tile, y1_tile)), total=total):
        tile_img = get_tile(x=x_tile, y=y_tile, z=zoom)
        img.paste(im=tile_img, box=((x_tile - x0_tile) * TILE_SIZE, (y_tile - y0_tile) * TILE_SIZE))

    x, y = x0_tile * TILE_SIZE, y0_tile * TILE_SIZE
    img = img.crop(
        (
            int(abs(x - x0)),  # left
            int(abs(y - y0)),  # top
            int(abs(x - x1)),  # right
            int(abs(y - y1)),  # bottom
        )
    )

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x=lngs, y=lats, s=s, alpha=alpha, c=c)
    ax.imshow(img, extent=(lef, rgt, bot, top))

    ax.set_ylim(bot, top)
    ax.set_xlim(lef, rgt)

    return fig, ax
