import requests
import json
import os
import time
from tqdm import tqdm

RAW_DATA_DIR = "data/data/raw"
BASE_URL = "https://pokeapi.co/api/v2"

def ensure_dir():
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)

def save_json(data, filename):
    filepath = os.path.join(RAW_DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_data(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {endpoint}: {e}")
        return None

def collect_pokemon(start_id, end_id):
    print("Collecting Pokemon and Species data...")
    for i in tqdm(range(start_id, end_id + 1)):
        # 포켓몬 데이터 수집
        poke_data = fetch_data(f"pokemon/{i}")
        if poke_data:
            save_json(poke_data, f"pokemon_{i}.json")

        # 도감 데이터 수집 (한국어 이름 및 도감 설명 포함)
        species_data = fetch_data(f"pokemon-species/{i}")
        if species_data:
            save_json(species_data, f"species_{i}.json")

        time.sleep(0.1)  # API 요청 속도 제한

def collect_types(start_id, end_id):
    print("Collecting Types data...")
    for i in tqdm(range(start_id, end_id + 1)):
        type_data = fetch_data(f"type/{i}")
        if type_data:
            save_json(type_data, f"type_{i}.json")
        time.sleep(0.1)

def collect_moves(start_id, end_id):
    print("Collecting Moves data...")
    for i in tqdm(range(start_id, end_id + 1)):
        move_data = fetch_data(f"move/{i}")
        if move_data:
            save_json(move_data, f"move_{i}.json")
        time.sleep(0.1)

def collect_items(start_id, end_id):
    print("Collecting Items data...")
    for i in tqdm(range(start_id, end_id + 1)):
        item_data = fetch_data(f"item/{i}")
        if item_data:
            save_json(item_data, f"item_{i}.json")
        time.sleep(0.1)

def collect_evolutions(start_id, end_id):
    print("Collecting Evolution Chains...")
    for i in tqdm(range(start_id, end_id + 1)):
        evo_data = fetch_data(f"evolution-chain/{i}")
        if evo_data:
            save_json(evo_data, f"evolution_{i}.json")
        time.sleep(0.1)

def collect_abilities(start_id, end_id):
    print("Collecting Abilities data...")
    for i in tqdm(range(start_id, end_id + 1)):
        ability_data = fetch_data(f"ability/{i}")
        if ability_data:
            save_json(ability_data, f"ability_{i}.json")
        time.sleep(0.1)

def collect_natures(start_id, end_id):
    print("Collecting Natures data...")
    for i in tqdm(range(start_id, end_id + 1)):
        nature_data = fetch_data(f"nature/{i}")
        if nature_data:
            save_json(nature_data, f"nature_{i}.json")
        time.sleep(0.1)

VARIANT_PREFIX_MAP = {
    "mega":       "메가",
    "gmax":       "거다이맥스",
    "alola":      "알로라",
    "galar":      "가라르",
    "hisui":      "히스이",
    "paldea":     "팔데아",
    "origin":     "오리진",
    "therian":    "영물",
    "primal":     "원시회귀",
    "totem":      "토템",
    "eternamax":  "에테르나맥스",
    "bloodmoon":  "블러드문",
}

def build_korean_variant_name(poke_name, korean_base):
    # poke_name 예: "charizard-mega-x", "pikachu-gmax", "raichu-alola"
    suffixes = poke_name.split("-")[1:]  # 베이스 이름 제거
    prefix = None
    extra = []
    for s in suffixes:
        if s in VARIANT_PREFIX_MAP:
            prefix = VARIANT_PREFIX_MAP[s]
        else:
            extra.append(s.upper())  # X, Y 같은 구분자
    if not prefix:
        return f"{korean_base} ({'-'.join(suffixes)})"
    name = f"{prefix} {korean_base}"
    if extra:
        name += " " + " ".join(extra)
    return name

def collect_variants(start_id, end_id):
    print("Collecting Pokemon Variants (Regional forms, Mega, etc)...")
    for i in tqdm(range(start_id, end_id + 1)):
        poke_data = fetch_data(f"pokemon/{i}")
        if not poke_data:
            time.sleep(0.1)
            continue

        # species URL에서 엔드포인트만 추출해 한국어 베이스 이름 조회
        species_url = poke_data.get("species", {}).get("url", "")
        if species_url:
            endpoint = species_url.replace(BASE_URL + "/", "")
            time.sleep(0.1)
            species_data = fetch_data(endpoint)
            if species_data:
                korean_base = next(
                    (n["name"] for n in species_data.get("names", [])
                     if n["language"]["name"] == "ko"),
                    None
                )
                if korean_base:
                    poke_data["korean_name"] = build_korean_variant_name(
                        poke_data["name"], korean_base
                    )

        save_json(poke_data, f"pokemon_{i}.json")
        time.sleep(0.1)

if __name__ == "__main__":
    ensure_dir()
    # 전체 포켓몬 수집 (약 1025마리)
    collect_pokemon(1, 1025)
    # 18개 기본 속성 수집
    collect_types(1, 18)
    # 모든 기술 수집 (약 950개)
    collect_moves(1, 950)
    # 모든 도구 수집 (약 2250개)
    collect_items(1, 2250)
    # 모든 진화 트리 (약 550개)
    collect_evolutions(1, 550)
    # 모든 특성 수집 (약 307개)
    collect_abilities(1, 307)
    # 모든 성격 수집 (25개)
    collect_natures(1, 25)
    # 리전폼 및 특수 폼 수집 (ID 10001 ~ 10325)
    collect_variants(10001, 10325)
    print("All Generations & Variants Collection Complete.")
