import random
import re
from typing import Dict, List, Optional, Tuple
import streamlit as st
from .data import BattlePokemon, STATUS_MOVES, ATTACK_BUFFS, HEAL_MOVES
from .ui import fmt_player, fmt_bot, fmt_move

STAT_MAP = {
    "attack": "attack_stage",
    "defense": "defense_stage",
    "special-attack": "sp_attack_stage",
    "special-defense": "sp_defense_stage",
    "speed": "speed_stage",
    "accuracy": "accuracy_stage",
    "evasion": "evasion_stage"
}

AILMENT_MAP = {
    1: "마비",
    2: "잠자기",
    3: "얼음",
    4: "화상",
    5: "독"
}

def stage_multiplier(stage: int, is_acc_eva: bool = False) -> float:
    stage = max(-6, min(6, stage))
    base = 3 if is_acc_eva else 2
    if stage >= 0:
        return (base + stage) / base
    else:
        return base / (base - stage)

def get_status_penalty(pokemon: BattlePokemon, key: str) -> float:
    """상태 이상에 따른 능력치 보정을 반환합니다."""
    if pokemon.status == "마비" and key == "speed":
        return 0.5
    if pokemon.status == "화상" and key == "attack":
        return 0.5
    return 1.0

def stat_value(pokemon: BattlePokemon, key: str) -> int:
    # key: attack, defense, sp_attack, sp_defense, speed
    api_key = key.replace("_", "-")
    stage_key = STAT_MAP.get(api_key)
    
    value = int(pokemon.stats.get(key) or 80)
    # 랭크 보정
    if stage_key:
        is_acc_eva = api_key in ["accuracy", "evasion"]
        value = int(value * stage_multiplier(getattr(pokemon, stage_key), is_acc_eva))
    
    # 상태 이상 보정 (마비, 화상)
    value = int(value * get_status_penalty(pokemon, key))
    
    return max(1, value)

def type_multiplier(move_type_id: int, defender: BattlePokemon, efficacy: Dict[Tuple[int, int], float]) -> float:
    multiplier = 1.0
    for target_type_id in defender.types:
        multiplier *= efficacy.get((move_type_id, target_type_id), 1.0)
    return multiplier

def apply_stat_changes(target: BattlePokemon, stats: List[str], values: List[int]) -> List[str]:
    messages = []
    is_player = target is st.session_state.get("battle_player")
    name = fmt_player(target.name) if is_player else fmt_bot(target.name)
    
    for s_name, val in zip(stats, values):
        attr = STAT_MAP.get(s_name)
        if not attr: continue
        
        current = getattr(target, attr)
        new_val = max(-6, min(6, current + val))
        setattr(target, attr, new_val)
        
        diff = new_val - current
        if diff == 0:
            if val > 0: messages.append(f"{name}의 {s_name}가 이미 최대치입니다!")
            else: messages.append(f"{name}의 {s_name}가 이미 최저치입니다!")
        else:
            abs_diff = abs(diff)
            change_str = "올랐습니다" if diff > 0 else "떨어졌습니다"
            if abs_diff == 2: change_str = "크게 " + change_str
            elif abs_diff >= 3: change_str = "배로 " + change_str
            
            # 가독성을 위해 한글 이름 매핑
            k_map = {"attack": "공격", "defense": "방어", "special-attack": "특수공격", 
                     "special-defense": "특수방어", "speed": "스피드", 
                     "accuracy": "명중률", "evasion": "회피율"}
            korean_stat = k_map.get(s_name, s_name)
            josa = "이" if korean_stat in ["공격", "방어", "특수방어"] else "가"
            messages.append(f"{name}의 {korean_stat}{josa} {change_str}!")
            
    return messages

def apply_status_move(user: BattlePokemon, move: Dict, defender: BattlePokemon) -> str:
    name = move["name"]
    is_player = user is st.session_state.get("battle_player")
    colored_user = fmt_player(user.name) if is_player else fmt_bot(user.name)
    effect = move.get("effect", {})
    
    logs = [f"{colored_user}의 {fmt_move(name)}!"]
    
    # 스탯 변화 적용
    stat_ids = effect.get("stat_id")
    values = effect.get("value")
    if stat_ids and values:
        target_poke = defender if effect.get("target") == "opponent" else user
        logs.extend(apply_stat_changes(target_poke, stat_ids, values))
        
    # 상태 이상 적용
    aid = effect.get("ailment_id")
    if aid in AILMENT_MAP:
        status_name = AILMENT_MAP[aid]
        if name == "맹독":
            status_name = "맹독"
            
        if not defender.status:
            defender.status = status_name
            defender.status_turns = 0 # 맹독 데미지 등을 위해 초기화
            logs.append(f"{fmt_bot(defender.name) if is_player else fmt_player(defender.name)}는 {status_name} 상태에 빠졌다!")
        else:
            logs.append("하지만 이미 상태 이상에 걸려 있다!")

    # 특수 기술 처리
    if name == "잠자기":
        user.current_hp = user.max_hp
        user.status = "잠자기"
        user.status_turns = 2
        logs.append(f"{colored_user}는 잠들어서 HP를 모두 회복했다!")
    elif name in ["날개쉬기", "광합성", "HP회복"]:
        healed = min(user.max_hp - user.current_hp, user.max_hp // 2)
        user.current_hp += healed
        logs.append(f"{colored_user}는 HP를 {healed} 회복했다!")
    elif name == "대타출동":
        logs.append("대타출동은 아직 구현되지 않았습니다.")

    return "\n".join(logs)

def estimate_damage(attacker: BattlePokemon, defender: BattlePokemon, move: Dict, efficacy: Dict[Tuple[int, int], float], is_crit: bool = False) -> int:
    if move.get("damage_class") == "status":
        return 0
    
    # 일격필살
    if move["name"] in ["땅가르기", "절대영도"]:
        return defender.max_hp

    power = int(move.get("power") or 40)
    damage_class = move.get("damage_class") or "physical"
    
    # 바디프레스: 공격력 대신 방어력 사용
    if move["name"] == "바디프레스":
        attack_key = "defense"
    else:
        attack_key = "sp_attack" if damage_class == "special" else "attack"
    
    defense_key = "sp_defense" if damage_class == "special" else "defense"
    
    # 급소일 경우 스탯 랭크 하락 무시 (공격자 하락, 방어자 상승 무시)
    attack = stat_value(attacker, attack_key)
    defense = stat_value(defender, defense_key)
    
    # 병상첨병: 상대가 상태 이상이면 데미지 2배
    if move["name"] == "병상첨병" and defender.status:
        power *= 2
        
    stab = 1.5 if move.get("type_id") in attacker.types else 1.0
    multiplier = type_multiplier(move.get("type_id"), defender, efficacy)
    
    level = 50
    base_damage = (((2 * level / 5 + 2) * power * attack / defense) / 50) + 2
    final = int(base_damage * stab * multiplier)
    
    if is_crit:
        final = int(final * 1.5)
        
    return max(1, final)

def resolve_attack(attacker: BattlePokemon, defender: BattlePokemon, move: Dict, efficacy: Dict[Tuple[int, int], float], opponent_move: Optional[Dict] = None) -> str:
    is_attacker_player = attacker is st.session_state.get("battle_player")
    attacker_name = fmt_player(attacker.name) if is_attacker_player else fmt_bot(attacker.name)
    defender_name = fmt_player(defender.name) if not is_attacker_player else fmt_bot(defender.name)
    move_name = fmt_move(move["name"])
    
    # 행동 제약 (상태 이상)
    if attacker.status == "잠자기":
        attacker.status_turns -= 1
        if attacker.status_turns <= 0:
            attacker.status = None
            return f"{attacker_name}는 잠에서 깨어났다!"
        return f"{attacker_name}는 깊이 잠들어 있다..."
    
    if attacker.status == "마비" and random.random() < 0.25:
        return f"{attacker_name}는 몸이 저려 움직일 수 없다!"

    # 특수 기술 판정: 기습
    if move["name"] == "기습":
        if not opponent_move or opponent_move.get("damage_class") == "status":
            return f"{attacker_name}의 기습! 하지만 실패했다..."
            
    # 특수 기술 판정: 속이다 (첫 턴에만 성공)
    if move["name"] == "속이다":
        if st.session_state.get("turn_count", 0) > 1:
            return f"{attacker_name}의 속이다! 하지만 첫 턴이 아니라 실패했다..."

    # 특수 기술 판정: 방어
    if defender.status == "방어":
        return f"{defender_name}은(는) {fmt_move('방어')}로 공격을 막아냈다!"
    if move["name"] == "방어":
        attacker.status = "방어" # 임시 상태로 방어 설정
        return f"{attacker_name}의 {fmt_move('방어')}! 공격을 막을 준비를 했다."

    # 명중 판정
    accuracy = int(move.get("accuracy") or 100)
    # 파동탄 등 필중기 처리 (accuracy가 None인 경우나 101 이상으로 설정된 경우 등)
    if move["name"] in ["파동탄", "신속", "제비반환"]:
        final_accuracy = 101
    else:
        acc_multiplier = stage_multiplier(attacker.accuracy_stage, True)
        eva_multiplier = stage_multiplier(defender.evasion_stage, True)
        final_accuracy = accuracy * (acc_multiplier / eva_multiplier)
    
    if final_accuracy <= 100 and random.randint(1, 100) > final_accuracy:
        return f"{attacker_name}의 {move_name}! 빗나갔습니다."

    if move.get("damage_class") == "status":
        return apply_status_move(attacker, move, defender)

    # 급소 판정
    is_crit = random.randint(1, 24) == 1
    # 트릭플라워 등 확정 급소 기술
    if move["name"] in ["트릭플라워", "암흑강타"]:
        is_crit = True
    # 급소율 높은 기술
    elif move["name"] in ["스톤에지", "드릴라이너"]:
        is_crit = random.randint(1, 8) == 1
    
    # 다회 공격 처리 (드래곤애로 2회, 트리플악셀 3회 등)
    hit_count = 1
    if move["name"] in ["드래곤애로", "비검천중파"]: hit_count = 2
    elif move["name"] in ["트리플악셀"]: hit_count = 3
    elif move["name"] == "스케일샷": hit_count = random.choice([2, 2, 3, 3, 4, 5])

    total_damage = 0
    for _ in range(hit_count):
        damage = max(1, int(estimate_damage(attacker, defender, move, efficacy, is_crit) * random.uniform(0.85, 1.0)))
        total_damage += damage
        if defender.current_hp <= damage:
            defender.current_hp = 0
            break
        defender.current_hp -= damage

    logs = [f"{attacker_name}의 {move_name}! {defender_name}에게 {total_damage} 데미지."]
    if hit_count > 1: logs[0] = f"{attacker_name}의 {move_name}! {hit_count}번 맞았습니다! 총 {total_damage} 데미지."
    if is_crit: logs.append(" 급소에 맞았다!")
    
    # 흡수기 처리 (기가드레인 등)
    if move["name"] in ["기가드레인", "드레인펀치", "흡수"]:
        healed = int(total_damage * 0.5)
        attacker.current_hp = min(attacker.max_hp, attacker.current_hp + healed)
        logs.append(f"{attacker_name}는 {defender_name}로부터 HP를 {healed} 흡수했다!")
    
    # 상성 메시지
    multiplier = type_multiplier(move.get("type_id"), defender, efficacy)
    if multiplier == 0: logs.append(" 효과가 없는 듯하다...")
    elif multiplier >= 2: logs.append(" 효과가 굉장했다!")
    elif 0 < multiplier < 1: logs.append(" 효과가 별로인 듯하다.")

    # 부가 효과 처리
    effect = move.get("effect", {})
    chance = effect.get("chance")
    if chance is True: chance = 100
    if chance and random.randint(1, 100) <= int(chance):
        stat_ids = effect.get("stat_id")
        values = effect.get("value")
        if stat_ids and values:
            target_poke = defender if effect.get("target") != "user" else attacker
            logs.extend(apply_stat_changes(target_poke, stat_ids, values))
            
        aid = effect.get("ailment_id")
        if aid in AILMENT_MAP and not defender.status:
            defender.status = AILMENT_MAP[aid]
            defender.status_turns = 0
            logs.append(f"{defender_name}는 {defender.status} 상태가 되었다!")

    return "\n".join(logs)

def apply_end_of_turn_effects(pokemon: BattlePokemon) -> List[str]:
    """턴 종료 시 발생하는 효과(독, 화상 등)를 처리합니다."""
    logs = []
    is_player = pokemon is st.session_state.get("battle_player")
    name = fmt_player(pokemon.name) if is_player else fmt_bot(pokemon.name)
    
    if pokemon.current_hp <= 0:
        return logs

    if pokemon.status == "독":
        damage = max(1, pokemon.max_hp // 8)
        pokemon.current_hp = max(0, pokemon.current_hp - damage)
        logs.append(f"{name}는 독 데미지를 입었다! ({damage} 데미지)")
    
    elif pokemon.status == "맹독":
        # 맹독은 턴마다 데미지 증가 (1/16 * n)
        pokemon.status_turns += 1
        damage = max(1, (pokemon.max_hp * pokemon.status_turns) // 16)
        pokemon.current_hp = max(0, pokemon.current_hp - damage)
        logs.append(f"{name}는 맹독 데미지를 입었다! ({damage} 데미지)")
        
    elif pokemon.status == "화상":
        damage = max(1, pokemon.max_hp // 16)
        pokemon.current_hp = max(0, pokemon.current_hp - damage)
        logs.append(f"{name}는 화상 데미지를 입었다! ({damage} 데미지)")
        
    # 씨뿌리기 등 추가 효과도 여기서 처리 가능
    
    return logs

def find_player_move(text: str, player: BattlePokemon) -> Optional[Dict]:
    normalized = re.sub(r"\s+", "", text.strip().lower())
    for move in player.moves:
        move_name = re.sub(r"\s+", "", move["name"].lower())
        if normalized == move_name or move_name in normalized:
            return move
    return None
