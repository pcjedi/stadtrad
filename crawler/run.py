from dateutil import parser
import requests
import pandas as pd
from matplotlib import pyplot as plt

x = 53.566466
y = 9.955832
r = 2336

url_base = "https://stadtrad.hamburg.de/"
url_path = "scs-search-and-book/"
url_suffix = f"api/search/{x},{y},{r}"

s = requests.Session()
s.get(url_base + url_path)
s.get(url_base)
r = s.get(url_base + url_path + url_suffix)

pd.json_normalize(
    data=r.json().get("payload"),
).to_csv(
    path_or_buf="data/" + str(int(parser.parse(r.headers["date"]).utcnow().timestamp())) + ".csv",
    index=False,
)


fig, ax = plt.subplots(figsize=(4,4))

url = "https://matplotlib.org/"
x=0
y=0

ax.text(x, y, url, url=url, bbox = dict(color='w', alpha=0.01, url=url))

fig.savefig("svg/text.svg")