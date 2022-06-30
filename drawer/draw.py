from glob import glob
import pandas as pd
import datetime
from tqdm import tqdm
from utils import plot_payload
import matplotlib.pylab as plt

dfs = []

for p in tqdm(glob("data/*"), desc="Loading data"):
    try:
        df = pd.read_csv(p)
        df["time"] = datetime.datetime.fromtimestamp(int(p.split("/")[-1][:-4]))
        dfs.append(df)
    except pd.errors.EmptyDataError:
        pass

df = pd.concat(dfs)

for (lat, lng, name), dfg in tqdm(df.groupby(["position.lat", "position.lng", "name"]), desc="Plotting data"):
    plt.clf()
    dfg.set_index("time")["rentalObjectCount.bike"].plot(
        drawstyle="steps",
        title=name,
    ).figure.savefig(f"drawer/stations/{lat}-{lng}.svg")

df_now = df[df.time == df.time.max()]

f, ax = plot_payload(
    lngs=df_now["position.lng"],
    lats=df_now["position.lat"],
    s=100,
    figsize=(100, 100),
    max_total=80,
)

for ix, row in df_now.iterrows():
    url = f"stations/{row['position.lat']}-{row['position.lng']}.svg"
    ax.text(
        x=row["position.lng"],
        y=row["position.lat"],
        s=row["name"],
        fontdict={
            "size": 6,
        },
        url=url,
        bbox=dict(color="w", alpha=0.01, url=url),
    )

f.savefig(fname="drawer/overview.svg", bbox_inches="tight")
