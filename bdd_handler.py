import requests

def query_bdd_for_player(url_query):
    r = requests.get(url=url_query, params=None)
    data = r.json()
    return data