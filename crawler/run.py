import time
from utils import stadtrad_payload, stadtrad_session
import pandas as pd
import json

payload_dict = dict()
s = stadtrad_session()

with open("crawler/params.json") as f:
    for param in json.load(f):
        payload = stadtrad_payload(**param, session=s)
        assert len(payload)<50, f"payload length is {len(payload)} at {param}"
        payload_dict.update({(p["position"]["lat"], p["position"]["lng"]): p for p in payload})

pd.json_normalize(data=payload_dict.values()).to_csv(
    path_or_buf="data/" + str(int(time.time())) + ".csv",
    index=False,
)
