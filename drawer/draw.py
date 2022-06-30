from glob import glob
import pandas as pd
import datetime
from tqdm import tqdm
from utils import plot_payload
import numpy as np

dfs = []

for p in tqdm(glob("data/*"), desc="Loading data"):
    try:
        df = pd.read_csv(p)
        df["time"] = datetime.datetime.fromtimestamp(int(p.split("/")[-1][:-4]))
        dfs.append(df)
    except pd.errors.EmptyDataError:
        pass

for (lat, lng, name), dfg in tqdm(pd.concat(dfs).groupby(["position.lat", "position.lng", "name"]), desc="Plotting data"):
    dfg.set_index("time")["rentalObjectCount.bike"].plot(
        drawstyle="steps",
        title=name,
    ).figure.savefig(f"drawer/stations/{lat}-{lng}.svg")

df_now = df[df.time == df.time.max()]

f, ax = plot_payload(
    lngs=df_now["position.lng"],
    lats=df_now["position.lat"],
    alpha=0.25 + df_now["rentalObjectCount.bike"] / (2 * np.max(df_now["rentalObjectCount.bike"])),
    s=100,
    figsize=(50, 10),
)
for ix, row in df_now.iterrows():
    ax.text(
        x=row["position.lng"],
        y=row["position.lat"],
        s=row["name"],
        fontdict={
            "size": 6,
        },
    )
f.savefig("drawer/overview.svg")
