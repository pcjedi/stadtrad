from utils import stadtrad_payload, stadtrad_session
from decimal import Decimal
import math
from collections import defaultdict
import json


def radius49(lat, lng, session):
    radius = 100000
    len_payload = len(stadtrad_payload(lat, lng, radius, session))
    while len_payload >= 50 and radius > 100:
        radius = radius // 10
        len_payload = len(stadtrad_payload(lat, lng, radius, session))
    for i in range(int(math.log10(radius)), -1, -1):
        for _ in range(10):
            while len_payload < 50:
                radius += 10**i
                len_payload = len(stadtrad_payload(lat, lng, radius, session))
        if len_payload >= 50 and radius > 100:
            radius -= 10**i
            len_payload = len(stadtrad_payload(lat, lng, radius, session))
    return radius


def offs(payload):
    lats = [Decimal(str(p["position"]["lat"])) for p in payload]
    lngs = [Decimal(str(p["position"]["lng"])) for p in payload]
    return max(lats) - min(lats), max(lngs) - min(lngs)


def main():
    payload = list()
    payload_dict_all = dict()
    station2param = defaultdict(list)

    s = stadtrad_session()

    lat = Decimal("53.5")
    lng = Decimal("10")
    radius = radius49(lat, lng, s)

    lat_off, lng_off = offs(stadtrad_payload(lat, lng, radius, s))

    n1, n2 = 0, 0
    f1, f2 = 1, 1
    n1_max, n1_min = 0, 0
    n2_max, n2_min = 1, -1

    while True:
        print(n1, n2)
        params = {
            "lat": lat + n1 * lat_off,
            "lng": lng + n2 * lng_off,
        }
        params["radius"] = radius49(**params, session=s)
        payload = stadtrad_payload(**params, session=s)
        assert len(payload) > 0 and len(payload) < 50, len(payload)
        payload_dict = {(p["position"]["lat"], p["position"]["lng"]): p for p in payload if p["position"]["lat"] > 53.4}
        [station2param[position].append(params) for position in payload_dict]
        lat_off_new, lng_off_new = offs(payload_dict.values())
        if lat_off_new < lat_off or lng_off_new < lng_off:
            lat_off = min(lat_off_new, lat_off)
            lng_off = min(lng_off_new, lng_off)
            n1, n2 = 0, 0
            f1, f2 = 1, 1
            payload = list()
            payload_dict_all = dict()
            continue
        if set(payload_dict.keys()) - set(payload_dict_all.keys()) == set():
            if n1 > n1_max:
                f1 = -1
                n1 = 0
            elif n1 < n1_min:
                if n2 > n2_max:
                    f2 = -1
                    n2 = 0
                    n1 = -1
                    f1 = 1
                elif n2 < n2_min:
                    break
                f1 = 1
                n1 = -1
                n2 += f2
        else:
            n1_max = max(n1, n1_max)
            n1_min = min(n1, n1_min)
            n2_max = max(n2, n2_max)
            n2_min = min(n2, n2_min)
        payload_dict_all |= payload_dict
        n1 += f1

    rel_params = list()

    while len(station2param) > 0:
        next_rel_param = station2param[sorted(station2param, key=lambda p: len(station2param.get(p)))[0]][0]
        rel_params.append(next_rel_param)
        for station in stadtrad_payload(**next_rel_param, session=s):
            station2param.pop((station["position"]["lat"], station["position"]["lng"]), None)

    with open("crawler/params.json", "w+") as f:
        f.write(
            json.dumps(
                obj=[{k: float(v) if not isinstance(v, int) else v for k, v in param.items()} for param in rel_params],
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
