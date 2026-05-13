import random

from dataclasses import dataclass, field
from .pokemon import PokemonDB

def get_pokemon_data(id: int) -> dict:
    """
    포켓몬 id를 통해 포켓몬의 데이터를 조회합니다.
    """
    db = PokemonDB()
    pokemon_data = db.get_pokemon_data(id)
    db.close()
    return pokemon_data

def get_max_hp(base_hp: int, level: int = 50) -> int:
    """
    레벨에 따라 보정된 최대 HP 계산 (개체치, 노력치 제외)
    공식: ((BaseHP × 2) + 100) × Level / 100 + 10
    """
    return int((((base_hp * 2) + 100) * (level / 100)) + 10)

def get_stats(base_stats: dict, level: int = 50) -> dict:
    """
    레벨에 따라 보정된 나머지 능력치 계산
    공식: ((BaseStat × 2) + 5) × Level / 100 + 5
    """
    new_stats = {}
    for stat, value in base_stats.items():
        if stat == 'hp':
            new_stats[stat] = get_max_hp(value, level)
        else:
            new_stats[stat] = int((((value * 2) + 5) * (level / 100)) + 5)
    return new_stats

def normalize(n):
    return n.replace(" ", "").lower() if n else ""

@dataclass
class BattlePokemon:
    """
    배틀에서 사용되는 포켓몬 객체입니다.
    """
    id: int
    name: str
    selected_moves: list[str]
    multiplier: float = 1.0
    
    # DB에서 불러올 정보들
    image_url: str = field(init=False)
    types: list[int] = field(init=False)
    type_names: list[str] = field(init=False)
    stats: dict[str, int] = field(init=False)
    max_hp: int = field(init=False)
    moves: list[dict] = field(init=False)
    
    # 배틀 상태 정보
    current_hp: int = field(init=False)
    attack_stage: int = 0
    sp_attack_stage: int = 0
    defense_stage: int = 0
    sp_defense_stage: int = 0
    speed_stage: int = 0
    ailment: str = None
    sleep_turns: int = 0

    def __post_init__(self):
        """
        포켓몬 id를 기반으로 추가 정보를 DB에서 조회하여 초기화합니다.
        """
        data = get_pokemon_data(self.id)
        if not data:
            raise ValueError(f"ID {self.id}에 해당하는 포켓몬 데이터를 찾을 수 없습니다.")

        self.image_url = data['image_url']
        self.types = data['types']
        self.type_names = data['type_names']

        # 배틀 포켓몬의 multiplier 적용
        if self.multiplier != 1.0:
            base_stats = get_stats(data['stats'])
            self.stats = {s: int(v * self.multiplier) for s, v in base_stats.items()}
        else:
            self.stats = get_stats(data['stats'])
            
        self.max_hp = self.stats['hp']
        self.current_hp = self.stats['hp']
        
        # 1. 전달받은 selected_moves에서 이름만 추출하여 표준화 (문자열 또는 딕셔너리 대응)
        target_move_names = []
        for mv in self.selected_moves:
            if isinstance(mv, dict):
                target_move_names.append(mv.get('name'))
            else:
                target_move_names.append(mv)

        # 2. 공백 제거 및 소문자화를 통한 견고한 이름 비교
        normalized_targets = [normalize(n) for n in target_move_names if n]
        self.moves = [m for m in data['moves'] if normalize(m['name']) in normalized_targets]
        
        # 만약 기술이 하나도 매칭되지 않는다면 (DB 업데이트 등의 이유), 랜덤으로 4개 선택
        if not self.moves:
            self.moves = random.sample(data['moves'], min(4, len(data['moves'])))