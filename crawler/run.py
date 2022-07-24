import time
from utils import stadtrad_payload, stadtrad_session
import pandas as pd
import json
import datetime
import os
import write_params

payload_dict = dict()
s = stadtrad_session()

rerun_params = False

with open("crawler/params.json") as f:
    for param in json.load(f):
        payload = stadtrad_payload(**param, session=s)
        rerun_params = len(payload) >= 50 or rerun_params
        payload_dict.update({(p["position"]["lat"], p["position"]["lng"]): p for p in payload})

path = os.path.join(
    "data",
    datetime.date.today().strftime("%Y/%m/%d"),
    str(int(time.time())) + ".csv",
)
os.makedirs(os.path.dirname(path), exist_ok=True)
pd.json_normalize(data=payload_dict.values()).to_csv(
    path_or_buf=path,
    index=False,
)

if rerun_params:
    write_params.main()
