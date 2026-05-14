import random

def get_fixed_damage(
    move: dict,
    attacker: dict,
    defender: dict
) -> int:
    """고정 데미지 기술 처리"""
    move_name = move.get("name", "")
    level = attacker.get("level", 50)

    if move_name in ["나이트헤드", "지구던지기"]:
        return level
    elif move_name == "소닉붐":
        return 20
    elif move_name == "용의분노":
        return 40
    elif move_name in ["분노의앞니", "자연의분노", "카타스트로피"]:
        return max(1, defender.get("current_hp", 100) // 2)
    elif move_name == "죽기살기":
        diff = defender.get("current_hp", 100) - attacker.get("current_hp", 100)
        return max(0, diff)
    elif move_name == "목숨걸기":
        return attacker.get("current_hp", 100)
    elif move_name == "사이코웨이브":
        return max(1, int(level * random.uniform(0.5, 1.5)))
    elif move_name in ["카운터", "미러코트", "메탈버스트", "앙갚음"]:
        last_dmg = attacker.get("last_damage_taken", 0)
        last_move = attacker.get("last_move_received")
        
        if last_dmg == 0 or not last_move:
            return 0
            
        if move_name == "카운터":
            if last_move.get("damage_class") == "physical":
                return last_dmg * 2
            return 0
        elif move_name == "미러코트":
            if last_move.get("damage_class") == "special":
                return last_dmg * 2
            return 0
        elif move_name in ["메탈버스트", "앙갚음"]:
            return int(last_dmg * 1.5)
    
    return 0

def get_involved_stats(
    damage_class: str,
    attacker: dict,
    defender: dict
):
    if damage_class == "physical":
        return (
            attacker.get("stats", {}).get("attack", 50),
            defender.get("stats", {}).get("defense", 50),
            attacker.get("attack_stage", 0),
            defender.get("defense_stage", 0)
        )
    elif damage_class == 'special':
        return (
            attacker.get("stats", {}).get("sp_attack", 50),
            defender.get("stats", {}).get("sp_defense", 50),
            attacker.get("sp_attack_stage", 0),
            defender.get("sp_defense_stage", 0)
        )