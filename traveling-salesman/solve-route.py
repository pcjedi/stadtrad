from glob import glob
import pandas as pd
from python_tsp.distances import great_circle_distance_matrix
import numpy as np
import json
import os
from python_tsp.heuristics import solve_tsp_simulated_annealing
from utils import get_duration, total_duration, plot_coords
import datetime
import googlemaps
import matplotlib.lines as mlines


df = pd.read_csv(sorted(glob("data/**/*.csv", recursive=True))[-1])
df = df[df["position.lat"] > 53.4].reset_index(drop=1)

positions = df[["position.lat", "position.lng"]]
dm = great_circle_distance_matrix(positions, positions)
stations = {f"{lat},{lng}": i for i, (lat, lng) in positions.iterrows()}

end_reached = False
start = datetime.datetime.now()
while not end_reached and (datetime.datetime.now() - start).seconds < 3600 * 5:
    duration_matrix = np.empty_like(dm)
    duration_matrix.fill(np.nan)
    values = []
    for d in glob("directions/*/*.json"):
        origin = d.split("/")[-2]
        destination = d.split("/")[-1][:-5]
        try:
            ix_origin = stations[origin]
            ix_destination = stations[destination]
        except KeyError:
            continue
        duration = json.load(open(d))[0]["legs"][0]["duration"]["value"]
        values.append(duration / dm[ix_origin, ix_destination])
        duration_matrix[ix_origin, ix_destination] = duration
        if not os.path.exists(f"directions/{destination}/{origin}.json"):
            duration_matrix[ix_destination, ix_origin] = duration

    duration_matrix[np.isnan(duration_matrix)] = dm[np.isnan(duration_matrix)] * np.mean(values)

    permutation2, distance2 = solve_tsp_simulated_annealing(
        distance_matrix=duration_matrix,
    )

    not_loaded = 0
    for o, d in zip(np.roll(permutation2, 1), permutation2):
        origin = positions.iloc[o].agg(lambda cols: ",".join([str(c) for c in cols]))
        destination = positions.iloc[d].agg(lambda cols: ",".join([str(c) for c in cols]))
        if not os.path.exists(f"directions/{origin}/{destination}.json"):
            not_loaded += 1
            try:
                get_duration(origin, destination, allow_reverse=False)
            except googlemaps.exceptions.Timeout:
                end_reached = True
                break
    if not_loaded == 0:
        coord_list = [positions.iloc[o].agg(lambda cols: ",".join([str(c) for c in cols])) for o in permutation2]
        td = total_duration(coord_list)
        try:
            with open("traveling-salesman/coord_list.json") as f:
                coord_list_old = json.load(f)
            td_old = total_duration(coord_list_old)
            coord_list_old_len = len(coord_list_old)
        except FileNotFoundError:
            td_old = np.inf
            coord_list_old_len = 0
        if td_old > td or coord_list_old_len < len(coord_list):
            with open("traveling-salesman/coord_list.json", "w+") as f:
                json.dump(coord_list, f, indent=2)
            print(td / 3600)
            coords = {
                "lat": [],
                "lng": [],
            }
            for o, d in zip(coord_list, coord_list[1:]):
                with open("directions/" + o + "/" + d + ".json") as fd:
                    direction = json.load(fd)
                    for coord in ["lat", "lng"]:
                        coords[coord].append(direction[0]["legs"][0]["steps"][0]["start_location"][coord])
                        coords[coord] += [step["end_location"][coord] for step in direction[0]["legs"][0]["steps"]]
            with open("directions/" + coord_list[-1] + "/" + coord_list[0] + ".json") as fd:
                direction = json.load(fd)
                for coord in ["lat", "lng"]:
                    coords[coord].append(direction[0]["legs"][0]["steps"][0]["start_location"][coord])
                    coords[coord] += [step["end_location"][coord] for step in direction[0]["legs"][0]["steps"]]
            fig, ax = plot_coords(
                lats=df["position.lat"].values,
                lngs=df["position.lng"].values,
                figsize=(25, 16),
                s=100,
                c="red",
                TILE_SIZE=256,
            )
            ax.add_line(mlines.Line2D(coords["lng"], coords["lat"], color="red"))
            fig.savefig("traveling-salesman/map.png", bbox_inches="tight")
