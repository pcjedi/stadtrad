import os
import googlemaps
import json
import numpy as np
import math
from PIL import Image
from tqdm import tqdm
from matplotlib import pyplot as plt
from io import BytesIO
from itertools import product
from functools import cache
import requests

gmaps = googlemaps.Client(key=os.getenv("GMAPSKEY"))


def get_duration(origin, destination, mode="bicycling", units="metric", allow_reverse=True):
    folderpath = f"directions/{origin}"
    filepath = f"{folderpath}/{destination}.json"
    if os.path.exists(filepath):
        with open(filepath) as f:
            direction_result = json.load(f)
    elif allow_reverse:
        return get_duration(origin=destination, destination=origin, mode=mode, units=units, allow_reverse=False)
    else:
        direction_result = gmaps.directions(
            origin=origin,
            destination=destination,
            mode=mode,
            units=units,
        )
        os.makedirs(folderpath, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(
                obj=direction_result,
                fp=f,
                indent=2,
            )
    return direction_result[0]["legs"][0]["duration"]["value"]


def duration_available(origin, destination, allow_reverse=True):
    folderpath = f"directions/{origin}"
    filepath = f"{folderpath}/{destination}.json"
    if os.path.exists(filepath):
        return True
    elif allow_reverse:
        return duration_available(origin=destination, destination=origin, allow_reverse=False)
    else:
        return False


def total_duration(coord_list):
    return sum(get_duration(o, d) for o, d in zip(coord_list, coord_list[1:])) + get_duration(coord_list[-1], coord_list[0])


@cache
def get_tile(x, y, z):
    URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png".format
    return Image.open(
        BytesIO(requests.get(URL(x=x, y=y, z=z), headers={"User-Agent": "requests" + requests.__version__}).content)
    )


def point_to_pixels(lon, lat, zoom, TILE_SIZE):
    """convert gps coordinates to web mercator"""
    r = math.pow(2, zoom) * TILE_SIZE
    lat = math.radians(lat)

    x = int((lon + 180.0) / 360.0 * r)
    y = int((1.0 - math.log(math.tan(lat) + (1.0 / math.cos(lat))) / math.pi) / 2.0 * r)

    return x, y


def plot_coords(lats, lngs, figsize=(25, 16), s=200, c="red", alpha=1, TILE_SIZE=256):
    """plot the payload of the bikes"""
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
        if total < 30:
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
