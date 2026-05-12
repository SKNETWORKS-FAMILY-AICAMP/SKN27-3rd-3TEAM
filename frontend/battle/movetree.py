import random

class MoveProcessor:
    def __init__(self, attacker: dict, defender: dict, move: dict):
        self.attacker = attacker
        self.defender = defender
        self.move = move
        self.category = move.get("category", "damage")
        self.messages = []

    def log(self, message: str):
        """로그 메시지를 기록합니다."""
        self.messages.append(message)

    def calculate_damage(self) -> int:
        """데미지를 계산합니다. (간이 공식)"""
        power = self.move.get("power")
        if not power:
            return 0
        
        level = self.attacker.get("level", 50)
        
        damage_class = self.move.get("damage_class", "physical")
        if damage_class == "physical":
            a = self.attacker.get("stats", {}).get("attack", 50)
            d = self.defender.get("stats", {}).get("defense", 50)
        elif damage_class == "special":
            a = self.attacker.get("stats", {}).get("sp_attack", 50)
            d = self.defender.get("stats", {}).get("sp_defense", 50)
        else:
            return 0
            
        # 기본 데미지 공식: (((2 * Level / 5 + 2) * Power * A / D) / 50 + 2)
        damage = int((((2 * level / 5 + 2) * power * (a / d)) / 50 + 2))
        
        # 자속 보정(STAB)이나 상성(Type Effectiveness) 등은 별도로 추가해야 합니다.
        return damage

    def apply_damage(self, damage: int):
        """데미지를 적용합니다."""
        current_hp = self.defender.get("current_hp", self.defender.get("stats", {}).get("hp", 100))
        self.defender["current_hp"] = max(0, current_hp - damage)
        self.log(f"{self.defender.get('name', '상대')}에게 {damage}의 데미지!")

    def apply_stat_changes(self, target: dict, stat_changes: list):
        """스탯 변화를 적용합니다."""
        if not stat_changes:
            return
            
        target_name = target.get("name", "포켓몬")
        for stat, change in stat_changes:
            direction = "올라갔다" if change > 0 else "떨어졌다"
            self.log(f"{target_name}의 {stat}이(가) {direction}!")
            # 실제 스탯 랭크 변화 적용 로직은 배틀 상태 관리쪽에 추가해야 합니다.

    def apply_ailment(self, target: dict, ailment: str):
        """상태이상을 적용합니다."""
        if ailment and ailment != "none":
            target_name = target.get("name", "포켓몬")
            self.log(f"{target_name}은(는) {ailment} 상태가 되었다!")
            # 실제 상태이상 기록 로직 추가 필요

    def execute(self) -> list:
        """기술의 카테고리에 따라 효과를 실행합니다."""
        move_name = self.move.get("name", "기술")
        attacker_name = self.attacker.get("name", "포켓몬")
        self.log(f"{attacker_name}의 {move_name}!")
        
        # 명중률 체크
        accuracy = self.move.get("accuracy")
        if accuracy and accuracy < 100:
            if random.randint(1, 100) > accuracy:
                self.log("그러나 공격은 빗나갔다!")
                return self.messages

        # ---------------------------------------------------------
        # 1. Damage 있음 (데미지를 주는 기술들)
        # ---------------------------------------------------------
        damage_categories = [
            "damage", "damage-raise", "damage-lower", 
            "damage-ailment", "damage-heal", "ohko"
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
                
                max_hp = self.attacker.get("stats", {}).get("hp", 100)
                current_hp = self.attacker.get("current_hp", max_hp)
                self.attacker["current_hp"] = min(max_hp, current_hp + heal_amount)
                self.log(f"{attacker_name}의 체력이 회복되었다!")
                
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
                max_hp = self.attacker.get("stats", {}).get("hp", 100)
                current_hp = self.attacker.get("current_hp", max_hp)
                
                heal_amount = int(max_hp * (healing / 100.0))
                self.attacker["current_hp"] = min(max_hp, current_hp + heal_amount)
                self.log(f"{attacker_name}의 체력이 회복되었다!")

        return self.messages


def process_turn(user_pokemon: dict, bot_pokemon: dict, user_move: dict, bot_move: dict) -> list:
    """
    양측의 포켓몬과 선택한 기술을 받아 1턴을 진행하고 로그 메시지 리스트를 반환합니다.
    (스피드와 우선도에 따른 선후공 결정 포함)
    """
    messages = []
    
    user_speed = user_pokemon.get("stats", {}).get("speed", 50)
    bot_speed = bot_pokemon.get("stats", {}).get("speed", 50)
    
    user_priority = user_move.get("priority", 0)
    bot_priority = bot_move.get("priority", 0)
    
    # 선공 결정 (1순위: 기술 우선도, 2순위: 스피드)
    if user_priority > bot_priority:
        user_goes_first = True
    elif user_priority < bot_priority:
        user_goes_first = False
    else:
        # 우선도가 같으면 스피드 비교
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
        
    # 첫 번째 공격
    processor1 = MoveProcessor(first_attacker, first_defender, first_move)
    messages.extend(processor1.execute())
    
    # 두 번째 공격 (첫 번째 공격으로 쓰러지지 않았을 경우에만)
    if first_defender.get("current_hp", 1) > 0:
        processor2 = MoveProcessor(second_attacker, second_defender, second_move)
        messages.extend(processor2.execute())
        
    return messages