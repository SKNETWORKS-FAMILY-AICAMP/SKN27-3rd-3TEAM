from battle.common.utils.calculator import get_involved_stats, get_fixed_damage
from battle.common.utils import calculate_type_multiplier, calculate_stab_multiplier
from battle.common.constants.stats import STAT_STAGE_MAP, STAT_KOR_NAMES
from battle.common.constants.ailments import AILMENT_KOR_NAMES

import random
from copy import deepcopy
from typing import List, Dict, Any

class MoveProcessor:
    def __init__(self, attacker: dict, defender: dict, move: dict, user_pokemon: dict, bot_pokemon: dict, leader_name: str = "관장"):
        self.attacker = attacker # 기술을 사용하는 포켓몬의 현재 상태
        self.defender = defender # 기술을 맞는 포켓몬의 현재 상태
        self.move = move         # 시전된 기술
        self.user_pokemon = user_pokemon
        self.bot_pokemon = bot_pokemon
        self.leader_name = leader_name
        self.category = move.get("category", "damage")
        self.messages = []
    
    def log(self, message: str):
        """로그 메시지를 기록합니다."""
        self.messages.append({
            "message": message,
            "player_state": deepcopy(self.user_pokemon),
            "bot_state": deepcopy(self.bot_pokemon)
        })
    
    def calculate_damage(self) -> int:
        """공격자가 시전한 기술의 원래 데미지를 계산합니다."""
        level = self.attacker.get("level", 50)
        power = self.move.get("power")
        damage_class = self.move.get("damage_class", "physical")
        
        if not power:
            # 고정 데미지 기술 처리
            power = get_fixed_damage(self.move, self.attacker, self.defender)
            return power
        
        # 원래 데미지 계산에 필요한 스탯 게산
        if damage_class == "status":
            return 0
        base_a, base_d, a_stage, d_stage = get_involved_stats(damage_class, self.attacker, self.defender)

        a = base_a * (2 + max(0, a_stage)) / (2 - min(0, a_stage))
        d = base_d * (2 + max(0, d_stage)) / (2 - min(0, d_stage))

        # base_damage: 스탯 기반 원래 데미지
        base_damage = (((2 * level / 5 + 2) * power * (a / d)) / 50 + 2)
        
        attack_type_id = self.move.get("type_id")
        attacker_type_ids = self.attacker.get("types", [])
        defender_type_ids = self.defender.get("types", [])
        
        # 자속 보정
        stab = calculate_stab_multiplier(attack_type_id, attacker_type_ids)
        # 타입 상성
        type_eff = calculate_type_multiplier(attack_type_id, defender_type_ids)
        
        if type_eff > 1.0:
            self.log("효과가 굉장했다!")
        elif type_eff < 1.0 and type_eff > 0:
            self.log("효과가 별로인 듯하다")
        elif type_eff == 0:
            self.log(f"{self.defender.get('name', '상대')}에게는 효과가 없는 것 같다...")
            return 0

        # 화상 상태 여부
        burn_multiplier = 1.0
        if damage_class == "physical" and self.attacker.get("ailment") == "burn":
            burn_multiplier = 0.5
        
        # 최종 데미지
        damage = int(base_damage * stab * type_eff * burn_multiplier)
        return damage
    
    def apply_damage(self, damage: int):
        """
        데미지를 적용합니다. 단, 낮은 확률로 급소에 맞으면 데미지가 1.5배로 적용됩니다.
        급소에 맞을 확률은 기술의 급소율에 따라 달라집니다.
        """
        current_hp = self.defender.get("current_hp", self.defender.get("stats", {}).get("hp", 100))

        if self.category == "damage-fixed":
            self.defender["current_hp"] = max(0, current_hp - damage)
            self.defender["last_damage_taken"] = damage
            self.defender["last_move_received"] = self.move
            self.log(f"{self.defender.get('name', '상대')}에게 {damage}의 데미지!")
            
            if self.move.get("name", "") == "목숨걸기":
                self.attacker["current_hp"] = 0
                self.log(f"{self.attacker.get('name', '자신')}은(는) 쓰러졌다!")
        else:
            critical_prob = {0: 0.0417, 1: 0.125, 2: 0.5, 3: 1.0}.get(self.move.get("crit_rate", 0), 0.0417)
            if random.random() < critical_prob:
                damage = int(damage * 1.5)
                self.defender["current_hp"] = max(0, current_hp - damage)
                self.log(f"급소에 맞았다! {self.defender.get('name', '상대')}에게 {damage}의 데미지!")
            else:
                self.defender["current_hp"] = max(0, current_hp - damage)
                self.log(f"{self.defender.get('name', '상대')}에게 {damage}의 데미지!")

            self.defender["last_damage_taken"] = damage
            self.defender["last_move_received"] = self.move

            drain = self.move.get("drain", 0)
            if drain < 0:
                # 반동 데미지
                recoil_dmg = abs(int(damage * drain / 100))
                attacker_hp = self.attacker.get("current_hp", 100)
                self.attacker["current_hp"] = max(0, attacker_hp - recoil_dmg)
                self.log(f"{self.attacker.get('name', '자신')}은(는) 반동으로 데미지를 입었다!")

                if self.attacker["current_hp"] == 0:
                    self.log(f"{self.attacker.get('name', '자신')}은(는) 쓰러졌다!")
    
    def apply_stat_changes(self, target: dict, stat_changes: list):
        """스탯 변화를 적용합니다."""
        if not stat_changes:
            return
        
        target_name = target.get("name", "포켓몬")
        for stat, change in stat_changes:
            stat_name = STAT_STAGE_MAP.get(stat) # special-attack -> sp_attack_stage
            if not stat_name:
                continue
                
            stat_kor = STAT_KOR_NAMES.get(stat, stat)
                
            # 현재 랭크 가져오기 및 변화 적용 (-6 ~ +6 제한)
            current_stage = target.get(stat_name, 0)
            new_stage = max(-6, min(6, current_stage + change))
            
            if new_stage == current_stage:
                if change > 0:
                    self.log(f"{target_name}의 {stat_kor}이(가) 더 이상 올라갈 수 없다!")
                else:
                    self.log(f"{target_name}의 {stat_kor}이(가) 더 이상 떨어질 수 없다!")
            else:
                target[stat_name] = new_stage
                direction = "올라갔다!" if change > 0 else "떨어졌다!"
                if abs(change) >= 2:
                    direction = "크게 " + direction
                self.log(f"{target_name}의 {stat_kor}이(가) {direction}")

    def apply_ailment(self, target: dict, ailment: str):
        """상태이상을 적용합니다."""
        if ailment and ailment != "none":
            target_name = target.get("name", "포켓몬")
            
            if target.get("ailment"):
                return
            
            if ailment not in AILMENT_KOR_NAMES or ailment == "none":
                ailment = "etc"
                
            target["ailment"] = ailment
            if ailment == "sleep":
                target["sleep_turns"] = random.randint(1, 3)
                
            self.log(f"{target_name}은(는) {AILMENT_KOR_NAMES.get(ailment, ailment)} 상태가 되었다!")
    
    def execute(self) -> List[Dict[str, Any]]:
        """기술의 효과를 처리하고 메시지(상태) 리스트를 반환합니다."""
        attacker_name = self.attacker.get("name", "포켓몬")
        move_name = self.move.get("name", "기술")
        
        if self.category == "switch":
            if self.move.get("is_bot"):
                self.log(f"{self.leader_name}은(는) {attacker_name}으(로) 교체했다!")
            else:
                self.log(f"가라! {attacker_name}!")
            return self.messages

        # 0. 혼란 처리 (혼란 자해 확인)체크
        ailment = self.attacker.get("ailment")
        if ailment == "paralysis":
            if random.random() < 0.125:
                self.log(f"{attacker_name}은(는) 몸이 저려서 움직일 수 없다!")
                return self.messages
        elif ailment == "sleep":
            turns_left = self.attacker.get("sleep_turns", 0)
            if turns_left > 0:
                self.log(f"{attacker_name}은(는) 쿨쿨 잠들어 있다.")
                self.attacker["sleep_turns"] = turns_left - 1
                return self.messages
            else:
                self.attacker["ailment"] = None
                self.log(f"{attacker_name}은(는) 잠에서 깨어났다!")
        elif ailment == "freeze":
            if random.random() < 0.2:
                self.attacker["ailment"] = None
                self.log(f"{attacker_name}의 얼음이 녹았다!")
            else:
                self.log(f"{attacker_name}은(는) 얼어붙어서 움직일 수 없다!")
                return self.messages
        elif ailment == "confusion":
            if random.random() < 0.333:
                self.log(f"{attacker_name}은(는) 영문도 모르고 자신을 공격했다!")
                level = self.attacker.get("level", 50)
                base_a = self.attacker.get("stats", {}).get("attack", 50)
                base_d = self.attacker.get("stats", {}).get("defense", 50)
                a_stage = self.attacker.get("attack_stage", 0)
                d_stage = self.attacker.get("defense_stage", 0)
                a = base_a * (2 + max(0, a_stage)) / (2 - min(0, a_stage))
                d = base_d * (2 + max(0, d_stage)) / (2 - min(0, d_stage))
                damage = int((((2 * level / 5 + 2) * 40 * (a / d)) / 50 + 2))
                current_hp = self.attacker.get("current_hp", self.attacker.get("stats", {}).get("hp", 100))
                self.attacker["current_hp"] = max(0, current_hp - damage)
                self.log(f"{attacker_name}에게 {damage}의 데미지!")
                if self.attacker["current_hp"] == 0:
                    self.log(f"{attacker_name}은(는) 쓰러졌다!")
                return self.messages

        self.log(f"{attacker_name}의 {move_name}!")
        
        # 명중률 계산: 최종 명중률 = 기술의 명중률 * (3 + max(0, 공격자 명중률 랭크)) / (3 + min(0, 수비자 회피율 랭크))
        # 기술의 명중률이 없으면 반드시 기술 성공
        move_accuracy = self.move.get("accuracy")
        if move_accuracy and move_accuracy < 100:
            attacker_accuracy_stage = self.attacker.get(STAT_STAGE_MAP.get("accuracy"), 0)
            defender_evasion_stage = self.defender.get(STAT_STAGE_MAP.get("evasion"), 0)
            stage = sorted([-6, 6, attacker_accuracy_stage - defender_evasion_stage])[1]
            accuracy = round(move_accuracy * (3 + max(0, stage)) / (3 - min(0, stage)))

            if random.randint(1, 100) > accuracy:
                self.log("그러나 공격은 빗나갔다!")
                return self.messages

        # ---------------------------------------------------------
        # 1. Damage 있음 (데미지를 주는 기술들)
        # ---------------------------------------------------------
        damage_categories = [
            "damage", "damage-raise", "damage-lower", 
            "damage-ailment", "damage-heal", "ohko", "damage-fixed"
        ]
        
        if self.category in damage_categories:
            if self.category == "ohko":
                damage = self.defender.get("current_hp", self.defender.get("stats", {}).get("hp", 100))
                self.log("일격필살!")
            else:
                damage = self.calculate_damage()
                
            # 데미지 적용
            self.apply_damage(damage)

            # 대상이 쓰러졌다면 부가 효과(상태이상, 스탯 하락 등) 무시
            if self.defender.get("current_hp", 0) == 0:
                self.log(f"{self.defender.get('name', '상대')}은(는) 쓰러졌다!")
                return self.messages

            # 풀죽음 판정
            flinch_chance = self.move.get("flinch_chance", 0)
            if flinch_chance > 0 and random.random() < (flinch_chance / 100.0):
                self.defender["flinched"] = True

            # stat_changes 있음
            if self.category == "damage-raise":
                # 적에게 데미지를 주고 내 스탯의 변화가 발생할 수 있음
                stat_chance = self.move.get("stat_chance", 0)
                if stat_chance == 0: stat_chance = 100
                if random.randint(1, 100) <= stat_chance:
                    self.apply_stat_changes(self.attacker, self.move.get("stat_changes", []))
                    
            elif self.category == "damage-lower":
                # 적에게 데미지를 주고 상대 스탯의 변화가 발생할 수 있음
                stat_chance = self.move.get("stat_chance", 0)
                if stat_chance == 0: stat_chance = 100
                if random.randint(1, 100) <= stat_chance:
                    self.apply_stat_changes(self.defender, self.move.get("stat_changes", []))
            
            # ailment가 있음
            elif self.category == "damage-ailment":
                # 적에게 데미지를 주고 상대에게 ailment를 부여할 수 있음
                ailment_chance = self.move.get("ailment_chance", 0)
                if ailment_chance == 0: ailment_chance = 100
                if random.randint(1, 100) <= ailment_chance:
                    self.apply_ailment(self.defender, self.move.get("ailment"))
                    
            # stat_changes와 ailment 모두 없음
            elif self.category == "damage-heal":
                # 적에게 데미지를 주고, 데미지*(drain/100) 만큼 HP를 회복함
                drain = self.move.get("drain", 0)
                heal_amount = int(damage * (drain / 100.0))
                
                max_hp = self.attacker.get("max_hp", 100)
                current_hp = self.attacker.get("current_hp", max_hp)
                self.attacker["current_hp"] = min(max_hp, current_hp + heal_amount)
                self.log(f"{attacker_name}의 체력이 {heal_amount}만큼 회복되었다!")
                
            elif self.category == "damage":
                # 적에게 데미지를 줌 (이미 위에서 처리됨)
                pass

        # ---------------------------------------------------------
        # 2. Damage 없음 (변화기)
        # ---------------------------------------------------------
        else:
            # stat_changes 있음
            if self.category == "net-good-stats":
                # stat_changes를 기준으로 target의 스탯을 변화시킴
                target_type = self.move.get("target")
                target = self.attacker if target_type == "user" else self.defender
                
                stat_chance = self.move.get("stat_chance", 0)
                if stat_chance == 0: stat_chance = 100
                
                if random.randint(1, 100) <= stat_chance:
                    self.apply_stat_changes(target, self.move.get("stat_changes", []))
                    
            # ailment 있음
            elif self.category == "ailment":
                # 상대에게 ailment를 부여함
                ailment_chance = self.move.get("ailment_chance", 0)
                if ailment_chance == 0: ailment_chance = 100
                
                if random.randint(1, 100) <= ailment_chance:
                    self.apply_ailment(self.defender, self.move.get("ailment"))
                    
            # stat_changes와 ailment 모두 없음
            elif self.category == "heal":
                # 최대 HP * (healing/100) 만큼 HP를 회복함
                healing = self.move.get("healing", 0)
                max_hp = self.attacker.get("max_hp", 100)
                current_hp = self.attacker.get("current_hp", max_hp)
                
                heal_amount = int(max_hp * (healing / 100.0))
                self.attacker["current_hp"] = min(max_hp, current_hp + heal_amount)
                self.log(f"{attacker_name}의 체력이 {heal_amount}만큼 회복되었다!")

        return self.messages

def run_battle_logic(user_pokemon: dict, bot_pokemon: dict, user_move: dict, bot_move: dict, leader_name: str = "관장") -> list:
    """
    양측의 포켓몬과 선택한 기술을 받아 1턴을 진행하고 로그 메시지 리스트를 반환합니다.
    """
    messages = []
    
    user_speed_base = user_pokemon.get("stats", {}).get("speed", 50)
    user_speed_stage = user_pokemon.get("speed_stage", 0)
    user_speed = user_speed_base * (2 + max(0, user_speed_stage)) / (2 - min(0, user_speed_stage))
    
    bot_speed_base = bot_pokemon.get("stats", {}).get("speed", 50)
    bot_speed_stage = bot_pokemon.get("speed_stage", 0)
    bot_speed = bot_speed_base * (2 + max(0, bot_speed_stage)) / (2 - min(0, bot_speed_stage))
    
    if user_pokemon.get("ailment") == "paralysis":
        user_speed *= 0.5
    if bot_pokemon.get("ailment") == "paralysis":
        bot_speed *= 0.5
    
    user_priority = user_move.get("priority", 0)
    bot_priority = bot_move.get("priority", 0)
    
    if user_priority > bot_priority:
        user_goes_first = True
    elif user_priority < bot_priority:
        user_goes_first = False
    else:
        if user_speed >= bot_speed:
            user_goes_first = True
        else:
            user_goes_first = False
            
    if user_goes_first:
        first_attacker, first_defender, first_move = user_pokemon, bot_pokemon, user_move
        second_attacker, second_defender, second_move = bot_pokemon, user_pokemon, bot_move
    else:
        first_attacker, first_defender, first_move = bot_pokemon, user_pokemon, bot_move
        second_attacker, second_defender, second_move = user_pokemon, bot_pokemon, user_move
        
    first_attacker["flinched"] = False
    first_defender["flinched"] = False
    
    processor1 = MoveProcessor(first_attacker, first_defender, first_move, user_pokemon, bot_pokemon, leader_name)
    messages.extend(processor1.execute())
    
    if first_defender.get("current_hp", 1) > 0 and first_attacker.get("current_hp", 1) > 0:
        if first_defender.get("flinched"):
            messages.append({
                "message": f"{first_defender.get('name')}은(는) 풀이 죽어 기술을 쓸 수 없다!",
                "player_state": deepcopy(user_pokemon),
                "bot_state": deepcopy(bot_pokemon)
            })
            first_defender["flinched"] = False
        else:
            processor2 = MoveProcessor(second_attacker, second_defender, second_move, user_pokemon, bot_pokemon, leader_name)
            messages.extend(processor2.execute())
        
    for pokemon in [user_pokemon, bot_pokemon]:
        if pokemon.get("current_hp", 1) <= 0:
            continue
        ailment = pokemon.get("ailment")
        if ailment in ["burn", "poison"]:
            max_hp = pokemon.get("stats", {}).get("hp", 100)
            current_hp = pokemon.get("current_hp", max_hp)
            name = pokemon.get("name", "포켓몬")
            if ailment == "burn":
                dmg = max(1, max_hp // 16)
                msg = f"{name}은(는) 화상 데미지를 입었다!"
            else:
                dmg = max(1, max_hp // 8)
                msg = f"{name}은(는) 독 데미지를 입었다!"
            
            pokemon["current_hp"] = max(0, current_hp - dmg)
            messages.append({
                "message": msg,
                "player_state": deepcopy(user_pokemon),
                "bot_state": deepcopy(bot_pokemon)
            })
            if pokemon["current_hp"] == 0:
                messages.append({
                    "message": f"{name}은(는) 쓰러졌다!",
                    "player_state": deepcopy(user_pokemon),
                    "bot_state": deepcopy(bot_pokemon)
                })
        
    return messages