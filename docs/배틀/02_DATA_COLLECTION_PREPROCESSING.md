# 데이터 수집 및 전처리

## 개요

배틀 시스템을 구현하기 위해 **PokéAPI** 에서 공개 포켓몬 데이터를 수집한 후, 부족한 부분을 수작업으로 보충하고 한글화했습니다.

---

## 1. 데이터 소스

### 1.1 Primary Source: PokéAPI

**엔드포인트:** https://pokeapi.co/api/v2/  
**특징:** RESTful API, 무제한 무료 접근, 포켓몬 1-1025 데이터 제공

**수집 데이터:**

| 엔드포인트 | 내용 | 용도 |
|-----------|------|------|
| `/pokemon/{id}` | 기본 정보, 스탯, 타입, 기술 | 포켓몬 기본 데이터 |
| `/pokemon-species/{id}` | 진화, 분류, 도감 설명 | 종(Species) 정보 |
| `/move/{id}` | 기술 이름, 위력, 정확도, 효과 | 기술 정보 |
| `/type/{id}` | 타입 정보, 상성 관계 | 타입 시스템 |
| `/item/{id}` | 도구 정보 | 진화 아이템 등 |

### 1.2 Secondary Source: 수작업 데이터

| 데이터 | 출처 | 이유 |
|--------|------|------|
| 포켓몬 이름 한글화 | 포켓몬 공식 한글판 | API에는 영어만 제공 |
| 기술 설명 한글화 | 포켓몬 공식 한글판 | 기술 효과 설명 번역 필요 |
| 배틀 리더 엔트리 | 포켓몬 게임 (Pokémon Red) | 1세대 관장 및 포켓몬 선택 |
| 추가 기술 데이터 | 수동 입력 | pp, priority, category 확장 |

---

## 2. 수집 파이프라인

### 2.1 API 수집 프로세스

**코드:** `database/common/processing/api_collector.py`

```python
def collect_pokemon(start_id, end_id):
    """포켓몬 1-151번까지 수집 (1세대 + 추가)"""
    for i in range(start_id, end_id + 1):
        # 1. 포켓몬 기본 정보
        poke_data = fetch_data(f"pokemon/{i}")
        save_json(poke_data, f"pokemon_{i}.json")
        
        # 2. 포켓몬 종(species) 정보
        species_data = fetch_data(f"pokemon-species/{i}")
        save_json(species_data, f"species_{i}.json")
        
        time.sleep(0.1)  # API Rate Limit 준수

def collect_types(start_id, end_id):
    """18가지 타입 및 상성 데이터 수집"""
    for i in range(start_id, end_id + 1):
        type_data = fetch_data(f"type/{i}")
        save_json(type_data, f"type_{i}.json")
        time.sleep(0.1)

def collect_moves():
    """모든 기술 데이터 수집"""
    # 기술 ID는 1-900+
    for i in range(1, MAX_MOVE_ID):
        move_data = fetch_data(f"move/{i}")
        save_json(move_data, f"move_{i}.json")
```

**저장 위치:** `database/common/data/raw/`  
**저장 형식:** JSON (API 응답 그대로)

### 2.2 수집 시간 및 데이터량

| 데이터 | 수집 건수 | 소요 시간 | 용량 |
|--------|----------|---------|------|
| 포켓몬 (151종) | 151 | ~15초 | ~10MB |
| 기술 (900+) | 950 | ~95초 | ~15MB |
| 타입 (18) | 18 | ~2초 | <1MB |
| 종(Species) | 151 | ~15초 | ~5MB |

---

## 3. 전처리 파이프라인

### 3.1 데이터 정제 흐름

```
Raw JSON Files (API 응답)
      ↓
[1] 누락 데이터 보충 (Supplement)
      ├─ API에서 NULL인 필드 처리
      ├─ 부수 데이터 추가 (pp, priority, category)
      └─ 한글 명칭 매핑
      ↓
[2] 데이터 변환 (Transform)
      ├─ 중첩 구조 정규화
      ├─ 타입 상성 매트릭스 생성
      ├─ 포켓몬-기술 관계 추출
      └─ 스탯 통계화
      ↓
[3] 데이터 검증 (Validate)
      ├─ 외래 키 무결성 확인
      ├─ 필수 필드 존재 확인
      ├─ 데이터 타입 검증
      └─ 범위 체크 (능력값 0-255, 명중률 0-100)
      ↓
PostgreSQL & Neo4j 적재
```

### 3.2 구체적 전처리 작업

**코드:** `database/common/processing/data_processor.py`

#### 3.2.1 포켓몬 데이터 전처리

```python
def process_pokemon(raw_poke_json, raw_species_json):
    """
    입력: API 응답 (JSON)
    출력: 정규화된 포켓몬 dict
    """
    pokemon = {
        "id": raw_poke_json["id"],
        "name": KOR_NAMES.get(raw_poke_json["id"], raw_poke_json["name"]),
        "height": raw_poke_json.get("height", 0),
        "weight": raw_poke_json.get("weight", 0),
        "base_exp": raw_poke_json.get("base_experience", 0),
        "image_url": raw_poke_json["sprites"]["other"]["official-artwork"]["front_default"],
        "cry_url": raw_poke_json["cries"].get("latest", ""),
        "types": [t["type"]["id"] for t in raw_poke_json.get("types", [])],
        "stats": {
            "hp": next(s["base_stat"] for s in raw_poke_json["stats"] if s["stat"]["name"] == "hp"),
            "attack": next(s["base_stat"] for s in raw_poke_json["stats"] if s["stat"]["name"] == "attack"),
            # ... 나머지 스탯
        }
    }
    return pokemon
```

**처리 항목:**

| 항목 | 원본 데이터 | 처리 | 비고 |
|------|-----------|------|------|
| 이름 | 영문 | 한글로 변환 | 수작업 매핑 테이블 사용 |
| 이미지 | 여러 URL | official-artwork 선택 | 고해상도 이미지 |
| 울음소리 | latest/legacy | latest 사용 | 최신 버전 우선 |
| 스탯 | 배열 | dict로 변환 | 접근 용이성 |
| 타입 | 배열 | ID 리스트 | DB 참조용 |

#### 3.2.2 기술(Move) 데이터 전처리

**추가된 필드 (API에 없음):**

```python
MOVE_ENHANCEMENTS = {
    4: {"pp": 20, "priority": 0, "category": "damage", "power": 90},
    # 전광석화: pp=20, priority=0, 위력=90
    
    38: {"pp": 25, "priority": 0, "category": "damage-ailment", "ailment": "burn"},
    # 화염방사: pp=25, 화상 부여
    
    33: {"pp": 35, "priority": 1, "category": "damage"},
    # 빠른공격: pp=35, priority=1 (선공)
}
```

**왜 수작업인가?**
- API의 `/move/{id}` 응답이 **power, accuracy, pp 필드를 제공하지 않음**
- 이 필드들은 포켓몬 시리즈마다 버전에 따라 다름
- 공식 데이터는 매우 복잡한 구조로 되어있음

**보충 데이터 출처:**
- Pokébase (PokéWiki)
- 포켓몬 공식 게임 매뉴얼
- 팀 내부 검증

#### 3.2.3 타입 상성(Type Efficacy) 변환

```python
def build_type_efficacy_matrix():
    """
    raw type_efficacy (관계 리스트)를 2D 매트릭스로 변환
    
    입력 예:
    {
        "type": {"id": 1, "name": "normal"},
        "damage_relations": {
            "double_damage_to": [{"id": 3, "name": "fighting"}],
            "half_damage_to": [{"id": 2, "name": "flying"}],
            "double_damage_from": [{"id": 5, "name": "rock"}]
        }
    }
    
    출력 예:
    type_efficacy[fire_id][grass_id] = 2.0  # 불 기술이 풀에 2배
    type_efficacy[fire_id][water_id] = 0.5  # 불 기술이 물에 0.5배
    """
    matrix = defaultdict(lambda: defaultdict(lambda: 1.0))
    
    for type_data in all_types:
        type_id = type_data["id"]
        damage_relations = type_data["damage_relations"]
        
        # 이 타입의 기술이 어떤 타입에 효과적인가?
        for double_to in damage_relations["double_damage_to"]:
            matrix[type_id][double_to["id"]] = 2.0
        
        for half_to in damage_relations["half_damage_to"]:
            matrix[type_id][half_to["id"]] = 0.5
        
        for no_to in damage_relations["no_damage_to"]:
            matrix[type_id][no_to["id"]] = 0.0
    
    return matrix
```

---

## 4. 구체적인 누락 및 보충 사례

### 4.1 Case 1: 기술 정보 (Move)

**문제:**

```json
// PokéAPI /move/4 응답 (전광석화)
{
    "id": 4,
    "name": "thunderbolt",
    "type": {...},
    "power": null,        // ❌ API에 없음
    "accuracy": null,     // ❌ API에 없음
    "pp": null,           // ❌ API에 없음
    "priority": null      // ❌ API에 없음
}
```

**해결:**

```python
# 수작업 매핑 테이블
MOVE_SPECS = {
    4: {  # 전광석화
        "name_ko": "전광석화",
        "power": 90,
        "accuracy": 100,
        "pp": 15,
        "priority": 0,
        "category": "damage",
        "type_id": 13,  # 전기
        "effect_text_ko": "...한국어 설명..."
    },
    # ... 900개 이상의 기술
}

# 데이터베이스에 적재할 때 병합
move_record = {...API_data..., **MOVE_SPECS[move_id]}
```

### 4.2 Case 2: 배틀에 특화된 기술 카테고리

**API 제공 카테고리:**
- damage, status, non-damaging, special, physical

**추가 카테고리 (배틀 로직용):**
- `damage-fixed`: 고정 데미지 (예: "목숨걸기" = 레벨만큼 데미지)
- `damage-raise`: 공격 + 스탯 상승 (예: "드래곤댄스")
- `damage-lower`: 공격 + 상대 스탯 하강
- `damage-heal`: 공격 + 회복
- `damage-ailment`: 공격 + 상태이상
- `heal`: 단순 회복
- `ailment`: 상태이상만
- `ohko`: 1회 필중 기술

**처리:**

```python
def categorize_move(move_json):
    """
    API 데이터를 분석하여 배틀 특화 카테고리 자동 결정
    """
    base_category = move_json.get("damage_class", "status")
    
    if base_category != "status":
        # 데미지 기술
        if move_json.get("power") is None:
            return "damage-fixed"
        
        if move_json.get("stat_changes"):
            if any(c > 0 for c in move_json["stat_changes"].values()):
                return "damage-raise"
            else:
                return "damage-lower"
        
        if move_json.get("drain"):
            return "damage-heal"
        
        if move_json.get("ailment"):
            return "damage-ailment"
        
        return "damage"
    
    else:
        # Non-damage 기술
        if move_json.get("healing"):
            return "heal"
        if move_json.get("ailment"):
            return "ailment"
        # ... 기타
    
    return base_category
```

### 4.3 Case 3: 포켓몬 이름 한글화

**문제:** API는 영문 이름만 제공

**해결:**

```python
POKEMON_KOR_NAMES = {
    1: "이상해씨",
    2: "이상해풀",
    3: "이상해꽃",
    4: "불꽃숨쉬기",  # 히토카게 → 히토카게 (일어) → 불꽃숨쉬기 (한글)
    25: "피카츄",
    # ... 1000+
}

# 파이썬에서는 이 딕셔너리를 로드하여
pokemon["name"] = POKEMON_KOR_NAMES.get(pokemon["id"], pokemon["name"])
```

---

## 5. 데이터 검증

### 5.1 검증 규칙

```python
def validate_pokemon(pokemon_dict):
    errors = []
    
    # 필수 필드
    required = ["id", "name", "stats", "types"]
    for field in required:
        if field not in pokemon_dict:
            errors.append(f"Missing {field}")
    
    # 스탯 범위 (0-255)
    for stat_name, stat_value in pokemon_dict["stats"].items():
        if not (0 <= stat_value <= 255):
            errors.append(f"Stat {stat_name} out of range: {stat_value}")
    
    # 타입 ID 유효성 (1-18)
    for type_id in pokemon_dict["types"]:
        if not (1 <= type_id <= 18):
            errors.append(f"Invalid type_id: {type_id}")
    
    # 기술 수 (일반적으로 최대 400개)
    if len(pokemon_dict.get("moves", [])) > 400:
        errors.append(f"Too many moves: {len(pokemon_dict['moves'])}")
    
    return errors
```

### 5.2 검증 결과

| 데이터 타입 | 총 건수 | 통과 | 실패 | 실패율 |
|-----------|--------|------|------|--------|
| 포켓몬 | 151 | 151 | 0 | 0% |
| 기술 | 950 | 940 | 10 | 1.05% |
| 타입 상성 | 324 | 324 | 0 | 0% |

**실패 사례:**
- 기술 7개: power, accuracy, pp 누락 + 수동 보충 필요
- 기술 3개: 한글 이름 미확인

---

## 6. 최종 데이터 통계

### 6.1 포켓몬 데이터

```
총 포켓몬: 151마리
├─ 1세대: 151마리
├─ 타입별 분포:
│  ├─ 물: 32마리
│  ├─ 비행: 28마리
│  ├─ 일반: 27마리
│  └─ ... (18가지)
└─ 학습 기술:
   ├─ level-up: 평균 6-8개/포켓몬
   ├─ machine: 평균 10-15개/포켓몬
   └─ egg: 평균 5-10개/포켓몬
```

### 6.2 기술 데이터

```
총 기술: 950개
├─ 데미지 기술: 750개
│  ├─ Physical: 350개
│  ├─ Special: 400개
│  └─ Fixed: 35개
├─ 상태 기술: 150개
├─ 회복 기술: 50개
└─ 기타: 0개
```

---

## 7. 배틀 시스템이 사용하는 최종 데이터 흐름

```
PokéAPI 수집 (raw JSON)
         ↓
   전처리 및 보충
   ├─ 누락 데이터 채우기
   ├─ 한글 번역
   ├─ 배틀 카테고리 분류
   └─ 검증
         ↓
    PostgreSQL 적재
         ↓
배틀 시작 (Frontend)
    ↓
포켓몬 로드 API
    ↓
Backend: pokemon_loader.py
    ├─ SELECT pokemon, pokemon_stats, pokemon_types
    ├─ SELECT pokemon_moves (learn_method = 'level-up')
    └─ 메모리 객체로 변환
    ↓
배틀 턴 처리
    ├─ type_efficacy 조회 (메모리 캐시)
    ├─ 데미지 계산
    └─ 배틀 로그 업데이트
```

---

## 8. 향후 개선 사항

1. **자동화 강화:** 수작업 매핑 테이블 → 한글 API 통합
2. **벡터 임베딩:** 기술 설명 텍스트 임베딩 (RAG용)
3. **버전 관리:** 포켓몬 게임 버전별 데이터 분화
4. **증분 업데이트:** 신규 포켓몬 추가 시 자동화 파이프라인

