import random
import re
from typing import Dict, List, Optional, Tuple
import streamlit as st
from .data import BattlePokemon, STATUS_MOVES, ATTACK_BUFFS, HEAL_MOVES
from .ui import fmt_player, fmt_bot, fmt_move

def stage_multiplier(stage: int) -> float:
    stage = max(-6, min(6, stage))
    return (2 + stage) / 2 if stage >= 0 else 2 / (2 - stage)

def stat_value(pokemon: BattlePokemon, key: str) -> int:
    stage_key = {
        "attack": "attack_stage",
        "sp_attack": "sp_attack_stage",
        "defense": "defense_stage",
        "sp_defense": "sp_defense_stage",
        "speed": "speed_stage",
    }.get(key)
    value = int(pokemon.stats.get(key) or 80)
    if stage_key:
        value = int(value * stage_multiplier(getattr(pokemon, stage_key)))
    return max(1, value)

def type_multiplier(move_type_id: int, defender: BattlePokemon, efficacy: Dict[Tuple[int, int], float]) -> float:
    multiplier = 1.0
    for target_type_id in defender.types:
        multiplier *= efficacy.get((move_type_id, target_type_id), 1.0)
    return multiplier

def estimate_damage(attacker: BattlePokemon, defender: BattlePokemon, move: Dict, efficacy: Dict[Tuple[int, int], float]) -> int:
    if move["name"] in STATUS_MOVES:
        return 0
    if move["name"] == "땅가르기":
        return defender.current_hp

    power = int(move.get("power") or 40)
    if move["name"] == "트리플악셀": power = 60
    elif move["name"] == "스케일샷": power = 75
    elif move["name"] == "드래곤애로": power = 100

    damage_class = move.get("damage_class") or "physical"
    attack_key = "sp_attack" if damage_class == "special" else "attack"
    defense_key = "sp_defense" if damage_class == "special" else "defense"
    attack = stat_value(attacker, attack_key)
    defense = stat_value(defender, defense_key)
    stab = 1.5 if move.get("type_id") in attacker.types else 1.0
    multiplier = type_multiplier(move.get("type_id"), defender, efficacy)
    base = (((2 * 50 / 5 + 2) * power * attack / defense) / 50) + 2
    return max(1, int(base * stab * multiplier))

def apply_status_move(user: BattlePokemon, move: Dict) -> str:
    name = move["name"]
    is_player = user is st.session_state.get("battle_player")
    colored_user = fmt_player(user.name) if is_player else fmt_bot(user.name)
    
    if name == "칼춤":
        user.attack_stage = min(6, user.attack_stage + 2)
        return f"{colored_user}의 {fmt_move('칼춤')}! 공격이 크게 올랐습니다."
    if name == "용의춤":
        user.attack_stage = min(6, user.attack_stage + 1)
        user.speed_stage = min(6, user.speed_stage + 1)
        return f"{colored_user}의 {fmt_move('용의춤')}! 공격과 스피드가 올랐습니다."
    if name == "껍질깨기":
        user.attack_stage = min(6, user.attack_stage + 2)
        user.sp_attack_stage = min(6, user.sp_attack_stage + 2)
        user.speed_stage = min(6, user.speed_stage + 2)
        user.defense_stage = max(-6, user.defense_stage - 1)
        user.sp_defense_stage = max(-6, user.sp_defense_stage - 1)
        return f"{colored_user}의 {fmt_move('껍질깨기')}! 공격, 특수공격, 스피드가 크게 올랐고 방어가 내려갔습니다."
    if name == "잠자기":
        healed = user.max_hp - user.current_hp
        user.current_hp = user.max_hp
        return f"{colored_user}의 {fmt_move('잠자기')}! HP를 {healed} 회복했습니다."
    if name == "날개쉬기":
        healed = min(user.max_hp - user.current_hp, user.max_hp // 2)
        user.current_hp += healed
        return f"{colored_user}의 {fmt_move('날개쉬기')}! HP를 {healed} 회복했습니다."
    return f"{colored_user}의 {fmt_move(name)}!"

def resolve_attack(attacker: BattlePokemon, defender: BattlePokemon, move: Dict, efficacy: Dict[Tuple[int, int], float]) -> str:
    if move["name"] in STATUS_MOVES:
        return apply_status_move(attacker, move)

    is_attacker_player = attacker is st.session_state.get("battle_player")
    attacker_name = fmt_player(attacker.name) if is_attacker_player else fmt_bot(attacker.name)
    defender_name = fmt_player(defender.name) if not is_attacker_player else fmt_bot(defender.name)
    move_name = fmt_move(move["name"])

    accuracy = int(move.get("accuracy") or 100)
    if random.randint(1, 100) > accuracy:
        return f"{attacker_name}의 {move_name}! 빗나갔습니다."

    if move["name"] == "땅가르기":
        defender.current_hp = 0
        return f"{attacker_name}의 {fmt_move('땅가르기')}! 일격필살이 적중했습니다."

    damage = max(1, int(estimate_damage(attacker, defender, move, efficacy) * random.uniform(0.85, 1.0)))
    defender.current_hp = max(0, defender.current_hp - damage)

    if move["name"] == "암석봉인":
        defender.speed_stage = max(-6, defender.speed_stage - 1)
    elif move["name"] == "스케일샷":
        attacker.speed_stage = min(6, attacker.speed_stage + 1)
        attacker.defense_stage = max(-6, attacker.defense_stage - 1)

    multiplier = type_multiplier(move.get("type_id"), defender, efficacy)
    effect_text = ""
    if multiplier == 0: effect_text = " 효과가 없습니다."
    elif multiplier >= 2: effect_text = " 효과가 굉장했습니다!"
    elif 0 < multiplier < 1: effect_text = " 효과가 별로인 듯합니다."

    return f"{attacker_name}의 {move_name}! {defender_name}에게 {damage} 데미지.{effect_text}"

def find_player_move(text: str, player: BattlePokemon) -> Optional[Dict]:
    normalized = re.sub(r"\s+", "", text.strip().lower())
    for move in player.moves:
        move_name = re.sub(r"\s+", "", move["name"].lower())
        if normalized == move_name or move_name in normalized:
            return move
    return None
