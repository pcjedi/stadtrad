import requests
from functools import cache


url_base = "https://stadtrad.hamburg.de/"
url_path = "scs-search-and-book/"
url_suffix = "api/search/{lat},{lng},{radius}".format


def stadtrad_session():
    session = requests.Session()
    session.get(url_base + url_path)
    session.get(url_base)
    return session


@cache
def stadtrad_payload(lat, lng, radius, session, retry=10):
    resp = session.get(url_base + url_path + url_suffix(lat=lat, lng=lng, radius=radius))
    if resp.status_code > 200:
        if retry > 0:
            session.get(url_base + url_path)
            session.get(url_base)
            return stadtrad_payload(lat, lng, radius, session, retry=retry - 1)
    assert "errors" not in resp.json(), resp.json()["errors"]
    return resp.json()["payload"]
