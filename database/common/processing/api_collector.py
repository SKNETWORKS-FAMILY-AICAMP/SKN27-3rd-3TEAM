import requests
import json
import os
import time
from tqdm import tqdm

RAW_DATA_DIR = "database/common/data/raw"
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

# 단일 토큰 접미사 → 한국어 매핑
VARIANT_SUFFIX_MAP = {
    "mega":       "메가",
    "gmax":       "거다이맥스",
    "alola":      "알로라",
    "galar":      "가라르",
    "hisui":      "히스이",
    "paldea":     "팔데아",
    "origin":     "오리진",
    "therian":    "영물",
    "primal":     "원시회귀",
    "eternamax":  "에테르나맥스",
    "bloodmoon":  "블러드문",
    "combat":     "컴벳",
    "blaze":      "블레이즈",
    "aqua":       "워터",
    "hero":       "마이티",
    "noice":      "나이스페이스",
    "female":     "암컷",
    "terastal":   "테라스탈폼",
    "stellar":    "스텔라폼",
    "roaming":    "도보폼",
    "stretchy":   "뻗은",
    "droopy":     "늘어진",
    "curly":      "젖힌",
    "shadow":     "흑마 탄",
    "ice":        "백마 탄",
    "dada":       "아빠",
    "hangry":     "배고픈 모양",
    "amped":      "하이한",
    "gulping":    "그대로 삼킨",
    "gorging":    "통째로 삼킨",
    "original":   "500년 전의 색",
    "ultra":      "울트라",
    "dusk":       "황혼",
    "midnight":   "한밤중",
    "busted":     "틀킨 모습",
    "pau":        "훌라훌라",
    "sensu":      "하늘하늘",
    "unbound":    "굴레를 벗어난",
    "complete":   "퍼펙트폼",
    "small":      "작은 사이즈",
    "large":      "큰 사이즈",
    "super":      "특대 사이즈",
    "blade":      "블레이드폼",
    "eternal":    "영원의 꽃",
    "ash":        "변신후",
    "pirouette":  "스텝폼",
    "resolute":   "각오",
    "black":      "블랙",
    "white":      "화이트",
    "zen":        "달마모드",
    "sky":        "스카이폼",
    "heat":       "히트로토무",
    "wash":       "워시로토무",
    "frost":      "프로스트로토무",
    "fan":        "스핀로토무",
    "mow":        "커트로토무",
    "sunny":      "태양",
    "rainy":      "빗방울",
    "snowy":      "설운",
    "red":        "빨간색 코어",
    "orange":     "주황색 코어",
    "yellow":     "노란색 코어",
    "green":      "초록색 코어",
    "blue":       "옥색 코어",
    "indigo":     "파란색 코어",
    "violet":     "보라색 코어",
}

# 복합 토큰 접미사 (suffix 전체 문자열로 먼저 매칭, prefix여부 포함)
COMPOUND_SUFFIX_MAP = {
    "dusk-mane":          ("황혼의 갈기", True),
    "dawn-wings":         ("새벽의 날개", True),
    "pom-pom":            ("파츽파츽",   False),
    "low-key":            ("로우한",     False),
    "own-tempo":          ("마이페이스", False),
    "battle-bond":        ("변신전",     False),
    "single-strike":      ("일격의 태세", False),
    "rapid-strike":       ("연격의 태세", False),
    "three-segment":      ("세 마디폼",  False),
    "blue-striped":       ("청색근",     False),
    "white-striped":      ("백색근",     False),
    "blue-plumage":       ("블루 페더",  False),
    "yellow-plumage":     ("옐로 페더",  False),
    "white-plumage":      ("화이트 페더", False),
    "green-plumage":      ("그린 페더",  False),
    "family-of-three":    ("세 식구",    False),
    "family-of-four":     ("네 식구",    False),
    "wellspring-mask":    ("우물의 가면", False),
    "hearthflame-mask":   ("화덕의 가면", False),
    "cornerstone-mask":   ("주춧돌의 가면", False),
    "orange-meteor":      ("주황색 코어", False),
    "yellow-meteor":      ("노란색 코어", False),
    "green-meteor":       ("초록색 코어", False),
    "blue-meteor":        ("옥색 코어",   False),
    "indigo-meteor":      ("파란색 코어", False),
    "violet-meteor":      ("보라색 코어", False),
    "10-power-construct": ("10%",         False),
    "50-power-construct": ("50%",         False),
}

# "접두사 포켓몬명" 방식을 유지하는 접미사
VARIANT_PREFIX_STYLE = {"mega", "gmax", "primal", "ultra", "hero"}

# 포켓몬별 접미사 특수 처리 {한국어베이스: {suffix: (번역, prefix여부)}}
POKEMON_SPECIFIC_SUFFIX = {
    "자시안":   {"crowned": ("검왕",  False)},
    "자마젠타": {"crowned": ("방패왕", False)},
}

def build_korean_variant_name(poke_name, korean_base):
    parts = poke_name.split("-")
    suffix_tokens = parts[1:]
    suffix_full = "-".join(suffix_tokens)

    # totem 제외 → None 반환 시 수집 스킵
    if "totem" in suffix_tokens:
        return None

    # standard → 기본 이름 그대로
    if suffix_tokens == ["standard"]:
        return korean_base

    # 개굴닌자(Greninja) 특수 처리
    if korean_base == "개굴닌자":
        if suffix_full == "battle-bond":
            return f"지우의 {korean_base}(변신전)"
        if suffix_tokens == ["ash"]:
            return f"지우의 {korean_base}(변신후)"

    # 포켓몬별 특수 접미사 처리 (자시안 crowned → 검왕 등)
    if korean_base in POKEMON_SPECIFIC_SUFFIX:
        for token in suffix_tokens:
            spec = POKEMON_SPECIFIC_SUFFIX[korean_base].get(token)
            if spec:
                variant_ko, use_prefix = spec
                return f"{variant_ko} {korean_base}" if use_prefix else f"{korean_base}({variant_ko})"

    # 복합 접미사 우선 매칭
    if suffix_full in COMPOUND_SUFFIX_MAP:
        variant_ko, use_prefix = COMPOUND_SUFFIX_MAP[suffix_full]
        return f"{variant_ko} {korean_base}" if use_prefix else f"{korean_base}({variant_ko})"

    # 단일 토큰 매칭
    variant_ko = None
    use_prefix_style = False
    extra = []
    for s in suffix_tokens:
        if s in VARIANT_SUFFIX_MAP:
            variant_ko = VARIANT_SUFFIX_MAP[s]
            use_prefix_style = s in VARIANT_PREFIX_STYLE
        else:
            extra.append(s.upper())  # X, Y 같은 구분자

    if not variant_ko:
        return f"{korean_base}({suffix_full})"

    if use_prefix_style:
        name = f"{variant_ko} {korean_base}"
        if extra:
            name += " " + " ".join(extra)
    else:
        suffix_str = variant_ko
        if extra:
            suffix_str += " " + " ".join(extra)
        name = f"{korean_base}({suffix_str})"
    return name

def collect_variants(start_id, end_id):
    print("Collecting Pokemon Variants (Regional forms, Mega, etc)...")
    for i in tqdm(range(start_id, end_id + 1)):
        poke_data = fetch_data(f"pokemon/{i}")
        if not poke_data:
            time.sleep(0.1)
            continue

        poke_name = poke_data.get("name", "")

        # totem은 수집하지 않음
        if "totem" in poke_name.split("-"):
            time.sleep(0.1)
            continue

        # species URL에서 한국어 베이스 이름 조회
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
                    korean_name = build_korean_variant_name(poke_name, korean_base)
                    if korean_name:
                        poke_data["korean_name"] = korean_name

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
