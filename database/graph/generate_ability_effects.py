import json

# 대상 포켓몬 이름 목록
TARGET_POKEMON_NAMES = [
    "한카리아스", "리자몽", "망나뇽", "마스카나", "핫삼", "루카리오",
    "마기라스", "드래펄트", "거북왕", "잠만보", "아머까오", "마폭시",
    "스코빌런", "대검귀", "독침붕", "다크라이", "누오", "님피아",
    "이상해꽃", "피카츄", "드닐레이브"
]

# 파일 로드
BASE = r"c:\dev\project\SKN27-3rd-3TEAM\database\common\data\processed"
GRAPH = r"c:\dev\project\SKN27-3rd-3TEAM\database\graph"

with open(f"{BASE}/pokemon.json", encoding="utf-8") as f:
    pokemons = json.load(f)

with open(f"{BASE}/pokemon_abilities.json", encoding="utf-8") as f:
    pokemon_abilities = json.load(f)

with open(f"{BASE}/abilities.json", encoding="utf-8") as f:
    abilities = json.load(f)

# abilities id -> 정보 맵
ability_map = {a["id"]: a for a in abilities}

# 대상 포켓몬 ID 수집 (히스이폼 포함)
target_pokemon_ids = set()
for p in pokemons:
    name = p["name"]
    for target in TARGET_POKEMON_NAMES:
        if target in name:
            target_pokemon_ids.add(p["id"])
            print(f"  매칭: {name} (id={p['id']}) <- {target}")

print(f"\n총 {len(target_pokemon_ids)}개 포켓몬 ID: {sorted(target_pokemon_ids)}")

# 해당 포켓몬들의 ability_id 수집 (중복 제거)
target_ability_ids = set()
for pa in pokemon_abilities:
    if pa["pokemon_id"] in target_pokemon_ids:
        target_ability_ids.add(pa["ability_id"])

print(f"총 {len(target_ability_ids)}개 특성 ID: {sorted(target_ability_ids)}")

# ──────────────────────────────────────────────
# ability_id -> effect_id, phase_id, ... 매핑 규칙
# effects.json:
#   1=상태이상 부여, 2=상태이상 면역, 3=능력치 랭크 변화, 4=능력치 배율 변화
#   5=데미지 배율 변화, 6=기술 위력 변화, 7=특정 타입 무효화, 8=타입 상성 변경
#   9=HP 회복, 10=우선도 변화, 11=명중률 변화, 12=급소율 변화
#   13=날씨 변화, 14=필드 변화, 15=도구 소모, 16=방어 효과, 17=강제 교체
#
# phases.json:
#   1=on_switch_in, 2=before_turn, 3=action_order, 4=before_move,
#   5=accuracy_check, 6=before_damage, 7=damage_calculation, 8=after_damage,
#   9=after_move, 10=end_turn, 11=on_faint
#
# stats.json:
#   1=hp, 2=attack, 3=defense, 4=sp_attack, 5=sp_defense, 6=speed
#   7=accuracy, 8=evasion, 9=critical
#
# status_conditions.json:
#   1=마비, 2=잠듦, 3=얼음, 4=화상, 5=독, 6=혼란, 7=헤롱헤롱
# ──────────────────────────────────────────────

ABILITY_EFFECT_RULES = {
    # 루카리아스(한카리아스) 특성: 모래의힘(159), 두꺼운지방(47), 모래날림(45)
    # 잠만보: 두꺼운지방(47), 저수(11), 무기력(129)
    # 망나뇽: 이너포커스(39), 멀티스케일(136)
    # ...
    # ability_id: [(effect_id, phase_id, ailment_id, stat_id, target, chance, value), ...]

    # 위협(22) - 상대 공격 -1
    22: [(3, 1, None, 2, "opponent", 100, -1)],

    # 부유(26) - 땅타입 무효
    26: [(7, 6, None, None, "self", None, None)],

    # 정전기(9) - 접촉시 마비 30%
    9: [(1, 8, 1, None, "opponent", 30, None)],

    # 맹화(66) - HP 1/3↓ 불꽃위력 1.5배
    66: [(6, 6, None, None, "self", None, None)],

    # 급류(67) - HP 1/3↓ 물위력 1.5배
    67: [(6, 6, None, None, "self", None, None)],

    # 심록(65) - HP 1/3↓ 풀위력 1.5배
    65: [(6, 6, None, None, "self", None, None)],

    # 두꺼운지방(47) - 불꽃/얼음 타입 상성 변경
    47: [(8, 6, None, None, "self", None, None)],

    # 저수(11) - 물 타입 흡수 → HP 회복
    11: [(7, 6, None, None, "self", None, None), (9, 8, None, 1, "self", 100, None)],

    # 모래날림(45) - 등장시 모래바람
    45: [(13, 1, None, None, "all", 100, None)],

    # 모래의힘(159) - 모래바람시 바위/강철/땅 위력↑
    159: [(6, 6, None, None, "self", None, None)],

    # 이너포커스(39) - 풀죽지 않음
    39: [(2, 8, None, None, "self", None, None)],

    # 멀티스케일(136) - HP 만땅시 데미지 절반
    136: [(5, 6, None, None, "self", None, None)],

    # 가속(3) - 매 턴 스피드 +1
    3: [(3, 10, None, 6, "self", 100, 1)],

    # 불꽃몸(49) - 접촉시 화상 30%
    49: [(1, 8, 4, None, "opponent", 30, None)],

    # 내열(85) - 불꽃 위력 절반
    85: [(5, 6, None, None, "self", None, None)],

    # 선파워(94) - 맑을때 sp_attack↑, HP↓
    94: [(3, 10, None, 4, "self", 100, 1)],

    # 벌레의알림(68) - HP 1/3↓ 벌레위력 1.5배
    68: [(6, 6, None, None, "self", None, None)],

    # 독가시(38) - 접촉시 독 30%
    38: [(1, 8, 5, None, "opponent", 30, None)],

    # 철주먹(89) - 펀치기술 위력↑
    89: [(6, 6, None, None, "self", None, None)],

    # 적응력(91) - 자타입일치 보정 강화
    91: [(6, 6, None, None, "self", None, None)],

    # 천진(109) - 상대 능력변화 무시
    109: [(3, 6, None, None, "opponent", None, None)],

    # 방탄(171) - 탄환/구슬 타입 무효
    171: [(7, 6, None, None, "self", None, None)],

    # 마중물(114) - 물타입 흡수→sp_attack↑
    114: [(7, 6, None, None, "self", None, None), (3, 8, None, 4, "self", 100, 1)],

    # 저주받은바디(130) - 공격받으면 기술봉인
    130: [(1, 8, 11, None, "opponent", 30, None)],

    # 흡반(21) - 강제교체 무효
    21: [(16, 4, None, None, "self", None, None)],

    # 수의베일(41) - 화상 면역
    41: [(2, 1, 4, None, "self", None, None)],

    # 둔감(12) - 헤롱헤롱/도발 면역
    12: [(2, 1, 7, None, "self", None, None)],

    # 습기(6) - 폭발기술 무효
    6: [(7, 4, None, None, "all", None, None)],

    # 마그마의무장(40) - 얼음 면역
    40: [(2, 1, 3, None, "self", None, None)],

    # 불면(15) - 잠듦 면역
    15: [(2, 1, 2, None, "self", None, None)],

    # 면역(17) - 독 면역
    17: [(2, 1, 5, None, "self", None, None)],

    # 자연회복(30) - 교체시 상태이상 회복
    30: [(9, 1, None, None, "self", 100, None)],

    # 수포(199) - 불꽃 위력↓, 화상 면역
    199: [(5, 6, None, None, "self", None, None), (2, 1, 4, None, "self", None, None)],

    # 옹골참(5) - 1격 방지
    5: [(16, 7, None, None, "self", None, None)],

    # 클리어바디(29) - 능력 하락 방지
    29: [(3, 1, None, None, "self", None, None)],

    # 하얀연기(73) - 능력 하락 방지
    73: [(3, 1, None, None, "self", None, None)],

    # 잔비(2) - 등장시 비
    2: [(13, 1, None, None, "all", 100, None)],

    # 가뭄(70) - 등장시 맑음
    70: [(13, 1, None, None, "all", 100, None)],

    # 타오르는불꽃(18) - 불꽃기술 받으면 위력↑
    18: [(6, 8, None, None, "self", None, None)],

    # 포이즌힐(90) - 독 상태시 HP 회복
    90: [(9, 10, None, 1, "self", 100, None)],

    # 피뢰침(31) - 전기 흡수→sp_attack↑
    31: [(7, 6, None, None, "self", None, None), (3, 8, None, 4, "self", 100, 1)],

    # 일찍기상(48) - 잠듦에서 빨리 깸
    48: [(2, 2, 2, None, "self", None, None)],

    # 근성(62) - 상태이상시 공격↑
    62: [(3, 10, None, 2, "self", 100, 1)],

    # 이상한비늘(63) - 상태이상시 방어↑
    63: [(3, 10, None, 3, "self", 100, 1)],

    # 탈피(61) - 매 턴 상태이상 회복 확률
    61: [(9, 10, None, None, "self", 30, None)],

    # 하늘의은총(32) - 추가효과 2배
    32: [(1, 8, None, None, "opponent", None, None)],

    # 쓱쓱(33) - 비올때 스피드↑
    33: [(3, 10, None, 6, "self", 100, 2)],

    # 엽록소(34) - 맑을때 스피드↑
    34: [(3, 10, None, 6, "self", 100, 2)],

    # 프레셔(46) - PP 2배 소모
    46: [(6, 4, None, None, "opponent", None, None)],

    # 싱크로(28) - 상태이상 전파
    28: [(1, 8, None, None, "opponent", 100, None)],

    # 악취(1) - 접촉시 풀죽음 10%
    1: [(1, 8, None, None, "opponent", 10, None)],

    # 독수(143) - 접촉시 독 30%
    143: [(1, 8, 5, None, "opponent", 30, None)],

    # 독폭주(137) - 독 상태시 물리공격↑
    137: [(3, 7, None, 2, "self", 100, 1)],

    # 부식(212) - 강철/독도 독상태 가능
    212: [(1, 8, 5, None, "opponent", 100, None)],

    # 다운로드(88) - 등장시 공격/특공↑
    88: [(3, 1, None, 2, "self", 100, 1)],

    # 천하장사(37) - 물리공격↑
    37: [(4, 6, None, 2, "self", 100, None)],

    # 순수한힘(74) - 물리공격↑
    74: [(4, 6, None, 2, "self", 100, None)],

    # 까칠한피부(24) - 접촉시 데미지
    24: [(5, 8, None, None, "opponent", 100, None)],

    # 나쁜손버릇(124) - 접촉시 도구 훔침
    124: [(15, 8, None, None, "opponent", 100, None)],

    # 심술꾸러기(126) - 능력변화 역전
    126: [(3, 1, None, None, "all", None, None)],

    # 재생력(144) - 교체시 HP 회복
    144: [(9, 1, None, 1, "self", 100, None)],

    # 짓궂은마음(158) - 변화기술 우선도+1
    158: [(10, 3, None, None, "self", None, None)],

    # 매직미러(156) - 변화기술 반사
    156: [(16, 4, None, None, "self", None, None)],

    # 아로마베일(165) - 멘탈기술 무효
    165: [(7, 4, None, None, "self", None, None)],

    # 님피아 관련 - 페어리스킨(182): 노말->페어리
    182: [(8, 6, None, None, "self", None, None)],

    # 드닐레이브 관련 - 독조종(307): 독+혼란
    307: [(1, 8, 6, None, "opponent", 100, None)],

    # 독사슬(302) - 공격시 맹독 확률
    302: [(1, 8, 5, None, "opponent", 20, None)],

    # 퍼코트(169) - 물리데미지 절반
    169: [(5, 7, None, None, "self", None, None)],

    # 스웜체인지(211) - HP절반시 폼체인지
    211: [(6, 7, None, None, "self", None, None)],

    # 방음(43) - 소리기술 무효
    43: [(7, 4, None, None, "self", None, None)],

    # 자기과신(153) - 쓰러뜨리면 공격↑
    153: [(3, 11, None, 2, "self", 100, 1)],

    # 질풍날개(177) - 비행기술 우선도+1
    177: [(10, 3, None, None, "self", None, None)],

    # 리밋실드(197) - HP절반시 특성 강화
    197: [(3, 8, None, 2, "self", 100, 2)],

    # 강철술사(200) - 강철기술 위력↑
    200: [(6, 6, None, None, "self", None, None)],

    # 드래곤의턱(263) - 드래곤기술 위력↑
    263: [(6, 6, None, None, "self", None, None)],

    # 역린(255=무아지경) - 공격↑ but 기술 고정
    255: [(3, 1, None, 2, "self", 100, 6)],

    # 다크라이 관련 - 나쁜꿈(123)
    123: [(1, 10, 9, None, "opponent", 100, None)],

    # 프레셔(46) 이미 위에 있음

    # 마스카나: 마성의몸(=헤롱헤롱바디 56)
    56: [(1, 8, 7, None, "opponent", 30, None)],

    # 핫삼: 테크니션(101)
    101: [(6, 6, None, None, "self", None, None)],

    # 핫삼: 근성(62) 이미 있음

    # 아머까오: 옹골찬턱(173) - 무는 기술 위력↑
    173: [(6, 6, None, None, "self", None, None)],

    # 아머까오: 위협(22) 이미 있음

    # 스코빌런: 맹화(66) 이미 있음
    # 스코빌런: 벌레의알림(68) 이미 있음

    # 마폭시: 매지션(170) - 기술 맞추면 도구 빼앗음
    170: [(15, 8, None, None, "opponent", 100, None)],

    # 마폭시: 심록(65) 이미 있음

    # 마기라스: 모래날림(45) 이미 있음
    # 마기라스: 두꺼운지방(47) 이미 있음

    # 드래펄트: 저주받은바디(130) 이미 있음
    # 드래펄트: 침투(151=틈새포착) - 방어 무시
    151: [(16, 4, None, None, "self", None, None)],

    # 한카리아스: 두꺼운피부(=까칠한피부 24) 이미 있음
    # 한카리아스: 모래의힘(159) 이미 있음

    # 누오: 물흡수(=저수 11) 이미 있음
    # 누오: 습기(6) 이미 있음

    # 이상해꽃: 심록(65), 엽록소(34) 이미 있음

    # 피카츄: 정전기(9) 이미 있음
    # 피카츄: 피뢰침(31) 이미 있음

    # 거북왕: 급류(67) 이미 있음
    # 거북왕: 젖은접시(44) - 비올때 HP 회복
    44: [(9, 10, None, 1, "self", 100, None)],

    # 루카리오: 강의 의지(=정의의마음 154) - 악기술받으면 공격↑
    154: [(3, 8, None, 2, "self", 100, 2)],
    # 루카리오: 이너포커스(39) 이미 있음
    # 루카리오: 적응력(91) 이미 있음

    # 잠만보: 무기력(129) - HP절반시 능력하락
    129: [(3, 8, None, 2, "self", 100, -2)],

    # 독침붕: 독가시(38) 이미 있음
    # 독침붕: 벌레의알림(68) 이미 있음
    # 독침붕: 압도하다(=의기양양 72) - 잠듦면역
    72: [(2, 1, 2, None, "self", None, None)],

    # 大검귀(히스이폼): 날카로운눈(51) - 명중률 하락 방지
    51: [(11, 1, None, 7, "self", None, None)],
    # 大검귀: 이판사판(120) - 반동기술 강화
    120: [(6, 6, None, None, "self", None, None)],
    # 大검귀: 무아지경(255) 이미 있음

    # 님피아: 픽시(=아로마베일 165) 이미 있음
    # 님피아: 페어리스킨(182) 이미 있음
    # 님피아: 큐피드(=달콤한꿈=없음) -> 프렌드가드(132)
    132: [(5, 7, None, None, "all", None, None)],
}

# 수집된 ability_id 중 규칙에 없는 것은 기본값으로 처리
def get_rules(ability_id):
    if ability_id in ABILITY_EFFECT_RULES:
        return ABILITY_EFFECT_RULES[ability_id]
    # 기본: effect_id=3(능력치 랭크 변화), phase_id=1(등장시), 나머지 null
    return [(3, 1, None, None, "self", None, None)]

result = []
seen = set()

for ability_id in sorted(target_ability_ids):
    rules = get_rules(ability_id)
    for (effect_id, phase_id, ailment_id, stat_id, target, chance, value) in rules:
        key = (ability_id, effect_id, phase_id)
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "ability_id": ability_id,
            "effect_id": effect_id,
            "phase_id": phase_id,
            "ailment_id": ailment_id,
            "stat_id": stat_id,
            "target": target,
            "chance": chance,
            "value": value
        })

out_path = f"{GRAPH}/ability_effects.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print(f"\n✅ 완료: {len(result)}개 레코드 -> {out_path}")

# 어떤 ability_id가 매핑됐는지 확인
print("\n[ ability_id | ability_name | effect_count ]")
for ability_id in sorted(target_ability_ids):
    name = ability_map.get(ability_id, {}).get("name", "?")
    cnt = sum(1 for r in result if r["ability_id"] == ability_id)
    print(f"  {ability_id:4d} | {name:15s} | {cnt}개")
