import requests

def get_count(endpoint):
    url = f"https://pokeapi.co/api/v2/{endpoint}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('count')
    return None

endpoints = ["pokemon", "type", "move", "item", "evolution-chain"]
for ep in endpoints:
    print(f"{ep}: {get_count(ep)}")
