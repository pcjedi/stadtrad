from glob import glob
import pandas as pd
from python_tsp.distances import great_circle_distance_matrix
import numpy as np
import json
import os
from python_tsp.heuristics import solve_tsp_simulated_annealing
from utils import get_duration
import datetime
import googlemaps


df = pd.read_csv(sorted(glob("data/*"))[-1])
df = df[df["position.lat"] > 53.4].reset_index(drop=1)

positions = df[["position.lat", "position.lng"]]
dm = great_circle_distance_matrix(positions, positions)
stations = {f"{lat},{lng}": i for i, (lat, lng) in positions.iterrows()}

not_loaded = 1
start = datetime.datetime.now()
while not_loaded > 0 and (datetime.datetime.now() - start).seconds < 3600 * 5:
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
                not_loaded = 0
                print("breaking ..")
                break
    print(not_loaded)

print(permutation2)
