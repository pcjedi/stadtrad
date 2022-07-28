import os
import googlemaps
import json

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
