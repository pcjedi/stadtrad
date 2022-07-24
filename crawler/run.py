import time
from utils import stadtrad_payload, stadtrad_session
import pandas as pd
import json
from datetime import datetime
import os

payload_dict = dict()
s = stadtrad_session()

with open("crawler/params.json") as f:
    for param in json.load(f):
        payload = stadtrad_payload(**param, session=s)
        assert len(payload) < 50, f"payload length is {len(payload)} at {param}"
        payload_dict.update({(p["position"]["lat"], p["position"]["lng"]): p for p in payload})

path = f"data/{datetime.now().year}/{datetime.now().month}/{datetime.now().day}/"
os.makedirs(path, exist_ok=True)
pd.json_normalize(data=payload_dict.values()).to_csv(
    path_or_buf=path+str(int(time.time()))+".csv",
    index=False,
)
