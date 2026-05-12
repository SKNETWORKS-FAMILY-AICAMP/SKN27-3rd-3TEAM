import os
import json

RAW_DATA_DIR = "database/common/data/raw"
PROCESSED_DATA_DIR = "database/common/data/processed"

def ensure_dir():
    if not os.path.exists(PROCESSED_DATA_DIR):
        os.makedirs(PROCESSED_DATA_DIR)

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_json(data, filename):
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

ABILITY_TRANSLATIONS = {
    "sharpness": "예리함",
    "protosynthesis": "고대활성",
    "quark-drive": "쿼크차지",
    "orichalcum-pulse": "진홍빛고동",
    "hadron-engine": "일렉트릭엔진",
    "supreme-overlord": "대장군",
    "costar": "공동지휘",
    "cud-chew": "되새김질",
    "anger-shell": "분노의껍질",
    "purifying-salt": "정화의소금",
    "well-baked-body": "다익은몸",
    "wind-rider": "바람타기",
    "guard-dog": "파수견",
    "rocky-payload": "암석운반",
    "wind-power": "풍력발전",
    "zero-to-hero": "마이티체인지",
    "commander": "사령탑",
    "electromorphosis": "전기변환",
    "opportunist": "편승",
    "thermal-exchange": "열교환",
    "armor-tail": "아머테일",
    "earth-eater": "토먹기",
    "mycelium-might": "균사력",
    "good-as-gold": "황금몸",
    "vessel-of-ruin": "재앙의그릇",
    "sword-of-ruin": "재앙의검",
    "tablets-of-ruin": "재앙의목간",
    "beads-of-ruin": "재앙의구슬",
    "tera-shift": "테라시프트",
    "tera-shell": "테라쉘",
    "teraform-zero": "테라폼제로",
    "poison-puppeteer": "독꼭두각시",
    "hospitality": "대접",
    "mind-seye": "심안",
    "embody-aspect": "투영",
    "toxic-chain": "독사슬",
}

def get_korean_name(names_list, default_name):
    for n in names_list:
        if n['language']['name'] == 'ko':
            return n['name']
    
    # 수동 번역 테이블 확인 (영어 소문자 기준)
    return ABILITY_TRANSLATIONS.get(default_name.lower(), default_name)

def get_korean_flavor_texts(flavor_text_entries):
    texts = []
    seen = set()  # 완전 중복 제거용
    for f in flavor_text_entries:
        if f['language']['name'] == 'ko':
            cleaned_text = f['flavor_text'].replace('\n', ' ').replace('\f', ' ').replace('\r', '')
            key = f"{f['version']['name']}:{cleaned_text}"
            if key not in seen:
                seen.add(key)
                texts.append({
                    'version_name': f['version']['name'],
                    'content': cleaned_text
                })
    return texts

def get_korean_genus(genera_list):
    for g in genera_list:
        if g['language']['name'] == 'ko':
            return g['genus']
    return None

def process_types():
    types_data = []
    type_efficacy = []
    
    # 1~18: 노말~페어리 타입
    for i in range(1, 19):
        t_data = load_json(os.path.join(RAW_DATA_DIR, f"type_{i}.json"))
        if not t_data: continue

        type_id = t_data['id']
        name_ko = get_korean_name(t_data.get('names', []), t_data['name'])
        types_data.append({'id': type_id, 'name': name_ko})

        # 타입 상성 관계 처리
        relations = t_data['damage_relations']

        def add_efficacy(target_list, factor):
            for t in target_list:
                # API가 URL 형태로 반환하므로 ID 추출
                target_id = int(t['url'].split('/')[-2])
                if target_id <= 18:  # 기본 18개 타입만 처리
                    type_efficacy.append({
                        'damage_type_id': type_id,
                        'target_type_id': target_id,
                        'damage_factor': factor
                    })

        add_efficacy(relations['double_damage_to'], 2.0)
        add_efficacy(relations['half_damage_to'], 0.5)
        add_efficacy(relations['no_damage_to'], 0.0)
        # 배율 1.0(보통 데미지)은 명시하지 않고 쿼리에서 기본값으로 처리
    
    save_json(types_data, "types.json")
    save_json(type_efficacy, "type_efficacy.json")

def process_pokemon():
    pokemon_list = []
    stats_list = []
    pokemon_types_list = []
    species_list = []
    flavor_texts_list = []
    pokemon_abilities_list = []
    pokemon_moves_list = []
    
    # 기본 포켓몬(1~1025) + 폼 변형(10001~10325)
    ranges = list(range(1, 1026)) + list(range(10001, 10326))

    for i in ranges:
        p_data = load_json(os.path.join(RAW_DATA_DIR, f"pokemon_{i}.json"))
        if not p_data: continue

        # 베이스 species ID 추출 (폼 변형도 베이스 포켓몬의 species를 참조)
        species_id = int(p_data['species']['url'].split('/')[-2])
        s_data = load_json(os.path.join(RAW_DATA_DIR, f"species_{species_id}.json"))

        if not s_data: continue

        # 한국어 이름: 폼 변형은 collect_variants에서 저장한 korean_name 우선 사용
        # 기본 포켓몬은 species names 목록에서 추출
        name_ko = p_data.get('korean_name') or get_korean_name(s_data.get('names', []), p_data['name'])

        # 공식 아트워크 이미지 URL 추출 (없으면 기본 스프라이트로 대체)
        sprites = p_data.get('sprites', {})
        image_url = sprites.get('other', {}).get('official-artwork', {}).get('front_default')
        if not image_url:
            image_url = sprites.get('front_default')

        # 울음소리 URL 추출
        cry_url = p_data.get('cries', {}).get('latest')

        # 1. 포켓몬 기본 정보
        pokemon_list.append({
            'id': p_data['id'],
            'name': name_ko,
            'height': p_data['height'],
            'weight': p_data['weight'],
            'base_exp': p_data['base_experience'],
            'image_url': image_url,
            'cry_url': cry_url,
            'is_default': p_data['is_default'],
            'species_id': species_id
        })
        
        # 2. 종족값
        stats = {s['stat']['name']: s['base_stat'] for s in p_data['stats']}
        stats_list.append({
            'pokemon_id': p_data['id'],
            'hp': stats.get('hp', 0),
            'attack': stats.get('attack', 0),
            'defense': stats.get('defense', 0),
            'sp_attack': stats.get('special-attack', 0),
            'sp_defense': stats.get('special-defense', 0),
            'speed': stats.get('speed', 0)
        })
        
        # 3. 타입
        for t in p_data['types']:
            type_id = int(t['type']['url'].split('/')[-2])
            pokemon_types_list.append({
                'pokemon_id': p_data['id'],
                'type_id': type_id,
                'slot': t['slot']
            })
            
        # 4. 도감 정보 (기본 포켓몬만, 폼 변형 중복 방지)
        if i <= 1025:
            gen_id = int(s_data['generation']['url'].split('/')[-2])
            classification = get_korean_genus(s_data.get('genera', []))
            gender_rate = s_data.get('gender_rate')

            species_list.append({
                'id': species_id,
                'pokemon_id': p_data['id'],
                'generation': gen_id,
                'capture_rate': s_data['capture_rate'],
                'classification': classification,
                'gender_rate': gender_rate
            })

            # 5. 도감 설명 (기본 포켓몬 species 기준)
            ko_flavors = get_korean_flavor_texts(s_data.get('flavor_text_entries', []))
            for f in ko_flavors:
                flavor_texts_list.append({
                    'species_id': species_id,
                    'version_name': f['version_name'],
                    'content': f['content']
                })
            
        # 6. 특성
        for a in p_data.get('abilities', []):
            ability_id = int(a['ability']['url'].split('/')[-2])
            pokemon_abilities_list.append({
                'pokemon_id': p_data['id'],
                'ability_id': ability_id,
                'is_hidden': a['is_hidden'],
                'slot': a['slot']
            })
            
        # 7. 습득 기술 목록
        for m in p_data.get('moves', []):
            move_id = int(m['move']['url'].split('/')[-2])
            # 버전별 중복 제거: 습득 방법 + 레벨 조합 기준으로 유일한 항목만 저장
            seen_methods = set()
            for detail in m.get('version_group_details', []):
                method = detail['move_learn_method']['name']
                level = detail['level_learned_at']
                key = f"{method}:{level}"
                if key not in seen_methods:
                    seen_methods.add(key)
                    pokemon_moves_list.append({
                        'pokemon_id': p_data['id'],
                        'move_id': move_id,
                        'learn_method': method,
                        'level_learned_at': level
                    })

    save_json(pokemon_list, "pokemon.json")
    save_json(stats_list, "pokemon_stats.json")
    save_json(pokemon_types_list, "pokemon_types.json")
    save_json(species_list, "species.json")
    save_json(flavor_texts_list, "flavor_text.json")
    save_json(pokemon_abilities_list, "pokemon_abilities.json")
    save_json(pokemon_moves_list, "pokemon_moves.json")

def process_moves():
    moves_list = []
    for i in range(1, 951):
        m_data = load_json(os.path.join(RAW_DATA_DIR, f"move_{i}.json"))
        if not m_data: continue
        name_ko = get_korean_name(m_data.get('names', []), m_data['name'])
        
        flavor_text = None
        for f in m_data.get('flavor_text_entries', []):
            if f['language']['name'] == 'ko':
                flavor_text = f['flavor_text'].replace('\n', ' ').replace('\f', ' ').replace('\r', '')
                break
        
        type_id = int(m_data['type']['url'].split('/')[-2]) if m_data.get('type') else None
        meta = m_data.get('meta', {})
        
        moves_list.append({
            'id': m_data['id'],
            'name': name_ko,
            'type_id': type_id,
            'damage_class': m_data['damage_class']['name'] if m_data.get('damage_class') else None,
            'power': m_data.get('power'),
            'accuracy': m_data.get('accuracy'),
            'pp': m_data.get('pp'),
            'priority': m_data.get('priority'),
            'effect_text': flavor_text,
            'ailment': meta.get('ailment', {}).get('name') if meta.get('ailment') else None,
            'ailment_chance': meta.get('ailment_chance'),
            'category': meta.get('category', {}).get('name') if meta.get('category') else None,
            'crit_rate': meta.get('crit_rate'),
            'drain': meta.get('drain'),
            'flinch_chance': meta.get('flinch_chance'),
            'healing': meta.get('healing'),
            'max_hits': meta.get('max_hits'),
            'max_turns': meta.get('max_turns'),
            'min_hits': meta.get('min_hits'),
            'min_turns': meta.get('min_turns'),
            'stat_chance': meta.get('stat_chance'),
            'stat_changes': [(stat_change['stat']['name'], stat_change['change']) for stat_change in m_data.get('stat_changes', [])],
            'target': m_data.get('target', {}).get('name') if m_data.get('target') else None
        })
    save_json(moves_list, "moves.json")

def process_items():
    items_list = []
    for i in range(1, 2251):
        i_data = load_json(os.path.join(RAW_DATA_DIR, f"item_{i}.json"))
        if not i_data: continue
        name_ko = get_korean_name(i_data.get('names', []), i_data['name'])
        
        flavor_text = None
        for f in i_data.get('flavor_text_entries', []):
            if f['language']['name'] == 'ko':
                flavor_text = f['text'].replace('\n', ' ').replace('\f', ' ').replace('\r', '')
                break
        
        category = i_data['category']['name'] if i_data.get('category') else None
        
        items_list.append({
            'id': i_data['id'],
            'name': name_ko,
            'category': category,
            'effect_text': flavor_text
        })
    save_json(items_list, "items.json")

def process_evolutions():
    evolutions_list = []
    for i in range(1, 551):
        e_data = load_json(os.path.join(RAW_DATA_DIR, f"evolution_{i}.json"))
        if not e_data: continue
        
        chain = e_data.get('chain')
        if not chain: continue
        
        queue = [chain]
        while queue:
            current = queue.pop(0)
            from_species_id = int(current['species']['url'].split('/')[-2])
            
            for evolution_to in current.get('evolves_to', []):
                to_species_id = int(evolution_to['species']['url'].split('/')[-2])
                
                details = evolution_to.get('evolution_details', [{}])
                detail = details[0] if details else {}
                min_level = detail.get('min_level')
                
                trigger_item_id = None
                if detail.get('item'):
                    trigger_item_id = int(detail['item']['url'].split('/')[-2])
                
                evolutions_list.append({
                    'from_species_id': from_species_id,
                    'to_species_id': to_species_id,
                    'min_level': min_level,
                    'trigger_item_id': trigger_item_id
                })
                
                queue.append(evolution_to)
                
    save_json(evolutions_list, "evolutions.json")

def process_abilities():
    abilities_list = []
    for i in range(1, 400):
        a_data = load_json(os.path.join(RAW_DATA_DIR, f"ability_{i}.json"))
        if not a_data: continue
        
        name_ko = get_korean_name(a_data.get('names', []), a_data['name'])
        
        flavor_text = None
        for f in a_data.get('flavor_text_entries', []):
            if f['language']['name'] == 'ko':
                flavor_text = f['flavor_text'].replace('\n', ' ').replace('\f', ' ').replace('\r', '')
                break
        
        abilities_list.append({
            'id': a_data['id'],
            'name': name_ko,
            'effect_text': flavor_text
        })
    save_json(abilities_list, "abilities.json")

def process_natures():
    natures_list = []
    for i in range(1, 26):
        n_data = load_json(os.path.join(RAW_DATA_DIR, f"nature_{i}.json"))
        if not n_data: continue
        
        name_ko = get_korean_name(n_data.get('names', []), n_data['name'])
        
        increased_stat = n_data['increased_stat']['name'] if n_data.get('increased_stat') else None
        decreased_stat = n_data['decreased_stat']['name'] if n_data.get('decreased_stat') else None
        
        natures_list.append({
            'id': n_data['id'],
            'name': name_ko,
            'increased_stat': increased_stat,
            'decreased_stat': decreased_stat
        })
    save_json(natures_list, "natures.json")

if __name__ == "__main__":
    ensure_dir()
    print("Processing Types...")
    process_types()
    print("Processing Pokemon...")
    process_pokemon()
    print("Processing Moves...")
    process_moves()
    print("Processing Items...")
    process_items()
    print("Processing Evolutions...")
    process_evolutions()
    print("Processing Abilities...")
    process_abilities()
    print("Processing Natures...")
    process_natures()
    print("Processing Complete.")

