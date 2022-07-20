from glob import glob
import pandas as pd
from scipy.spatial import distance_matrix
import numpy as np
import json
import os
from python_tsp.heuristics import solve_tsp_simulated_annealing
from utils import get_duration


df = pd.read_csv(sorted(glob("data/*"))[-1])
df = df[df["position.lat"] > 53.4].reset_index(drop=1)

positions = df[["position.lat", "position.lng"]]
dm = distance_matrix(positions, positions)
stations = {f"{lat},{lng}": i for i, (lat, lng) in positions.iterrows()}

not_loaded = 1
while not_loaded > 0:
    values = [
        json.load(open(d))[0]["legs"][0]["duration"]["value"]
        / (
            sum(
                [
                    (s - d) ** 2
                    for s, d in zip(
                        [float(v) for v in d.split("/")[-2].split(",")], [float(v) for v in d.split("/")[-1][:-5].split(",")]
                    )
                ]
            )
            ** (1 / 2)
        )
        for d in glob("directions/*/*.json")
    ]
    duration_matrix = dm * np.mean(values)

    for d in glob("directions/*/*.json"):
        origin = d.split("/")[-2]
        destination = d.split("/")[-1][:-5]
        duration = json.load(open(d))[0]["legs"][0]["duration"]["value"]
        try:
            duration_matrix[stations[origin], stations[destination]] = duration
            if not os.path.exists(f"directions/{destination}/{origin}.json"):
                duration_matrix[stations[destination], stations[origin]] = duration
        except KeyError:
            pass

    permutation2, distance2 = solve_tsp_simulated_annealing(
        distance_matrix=duration_matrix,
    )

    not_loaded = 0
    for o, d in zip(np.roll(permutation2, 1), permutation2):
        origin = positions.iloc[o].agg(lambda cols: ",".join([str(c) for c in cols]))
        destination = positions.iloc[d].agg(lambda cols: ",".join([str(c) for c in cols]))
        if not os.path.exists(f"directions/{origin}/{destination}.json"):
            not_loaded += 1
            get_duration(origin, destination, allow_reverse=False)

print(permutation2)
