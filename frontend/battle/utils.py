import re
import random
import requests
import streamlit as st

from dataclasses import dataclass, field, asdict
from types import SimpleNamespace
from .pokemon import PokemonDB, BotPokemonDB

import os
BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

def get_pokemon_data(id: int) -> dict:
    """
    [플레이어용] level-up 기술만 포함된 포켓몬 데이터를 조회합니다.
    """
    db = PokemonDB()
    pokemon_data = db.get_pokemon_data(id)
    db.close()
    return pokemon_data

def get_bot_pokemon_data(id: int) -> dict:
    """
    [봇용] 모든 learn_method 기술을 포함한 포켓몬 데이터를 조회합니다.
    """
    db = BotPokemonDB()
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


@dataclass
class BotBattlePokemon(BattlePokemon):
    """
    봇 전용 배틀 포켓몬 클래스입니다.
    BotPokemonDB를 사용하여 learn_method 제한 없이 모든 기술을 조회합니다.
    """
    def __post_init__(self):
        """
        봇 포켓몬 id를 기반으로 BotPokemonDB에서 추가 정보를 조회하여 초기화합니다.
        """
        data = get_bot_pokemon_data(self.id)
        if not data:
            raise ValueError(f"ID {self.id}에 해당하는 포켓몬 데이터를 찾을 수 없습니다.")

        self.image_url = data['image_url']
        self.types = data['types']
        self.type_names = data['type_names']

        if self.multiplier != 1.0:
            base_stats = get_stats(data['stats'])
            self.stats = {s: int(v * self.multiplier) for s, v in base_stats.items()}
        else:
            self.stats = get_stats(data['stats'])

        self.max_hp = self.stats['hp']
        self.current_hp = self.stats['hp']

        # 전달받은 selected_moves에서 이름 추출
        target_move_names = []
        for mv in self.selected_moves:
            if isinstance(mv, dict):
                target_move_names.append(mv.get('name'))
            else:
                target_move_names.append(mv)

        normalized_targets = [normalize(n) for n in target_move_names if n]
        self.moves = [m for m in data['moves'] if normalize(m['name']) in normalized_targets]

        # 매칭되는 기술이 없으면 랜덤 선택
        if not self.moves:
            self.moves = random.sample(data['moves'], min(4, len(data['moves'])))

def _to_ns(d: dict) -> SimpleNamespace:
    """봇 포켓몬 dict → attribute 접근 가능한 SimpleNamespace"""
    return SimpleNamespace(**d)

def _to_dict(obj) -> dict:
    """BattlePokemon(dataclass) 또는 SimpleNamespace → dict"""
    if isinstance(obj, SimpleNamespace):
        return vars(obj)
    return asdict(obj)

def prepare_bot_move():
    """
    [다음 턴을 위한 봇 행동 사전 결정 — API 호출]
    POST /api/v1/battle/decide_bot_move 를 호출하여 봇 행동을 미리 계산하고 세션에 저장합니다.
    """
    bot = st.session_state.battle_bot
    player = st.session_state.battle_player
    bot_party = st.session_state.bot_party
    bot_strategy = st.session_state.get("bot_strategy", "llm")

    payload = {
        "bot_pokemon": _to_dict(bot),
        "player_pokemon": _to_dict(player),
        "bot_party": [_to_dict(bp) for bp in bot_party],
        "strategy": bot_strategy
    }
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/battle/decide_bot_move",
            json=payload,
            timeout=15
        )
        resp.raise_for_status()
        st.session_state.pending_bot_move = resp.json()["bot_move"]
    except Exception as e:
        import random
        print(f"[prepare_bot_move] API error, falling back to random: {e}")
        st.session_state.pending_bot_move = random.choice(list(bot.moves))

def find_player_action(text: str, player: BattlePokemon, player_party: list):
    normalized = re.sub(r"\s+", "", text.strip().lower())
    
    # 교체 시도 확인
    for idx, p in enumerate(player_party):
        if p.id == player.id or p.current_hp <= 0: continue
        p_name = re.sub(r"\s+", "", p.name.lower())
        if p_name in normalized:
            return {"name": f"{p.name}(으)로 교체", "category": "switch", "target_index": idx, "priority": 6}

    # 기술 시도 확인
    for move in player.moves:
        move_name = re.sub(r"\s+", "", move["name"].lower())
        if normalized == move_name or move_name in normalized:
            return move
    return None

def start_custom_battle(player_team_data, leader_name="웅이"):
    """
    [API 호출] 봇 파티 초기화 및 배틀 시작.
    플레이어 파티는 기존과 동일하게 로컬에서 BattlePokemon으로 생성하고,
    봇 파티는 POST /api/v1/battle/start 를 통해 백엔드에서 조회합니다.
    """
    with st.spinner("배틀 데이터를 준비 중..."):
        # 1. 플레이어 파티 구성 (기존과 동일)
        player_party = [
            BattlePokemon(id=p["id"], name=p["name"], selected_moves=p["moves"])
            for p in player_team_data
        ]
        st.session_state.player_party = player_party
        st.session_state.battle_player = player_party[0]

        # 2. 봇 파티 구성 → 백엔드 API 호출
        #    응답: {bot_party: [...], first_bot_move: {...}, quotes: {start, defeat}}
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/v1/battle/start",
                json={"leader_name": leader_name},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            st.error(f"배틀 초기화에 실패했습니다: {e}")
            return False

        bot_party = [_to_ns(bp) for bp in data["bot_party"]]
        st.session_state.bot_party = bot_party
        st.session_state.battle_bot = bot_party[0]
        st.session_state.leader_name = leader_name

        # 3. 관장 대사 및 배틀 메시지 초기화
        quotes = data["quotes"]
        st.session_state.leader_quotes = quotes  # 승리 시 패배 대사 재사용
        first_content = (
            f"<div style='font-style: italic; color: #94a3b8; margin-bottom: 10px;'>"
            f"{leader_name}: \"{quotes['start']}\""
            f"</div>"
        )
        st.session_state.battle_messages = [{"role": "assistant", "content": first_content}]

        st.session_state.battle_started = True
        st.session_state.battle_over = False
        st.session_state.turn_count = 0

        # 4. 첫 턴 봇 행동은 API가 미리 계산하여 반환 (prepare_bot_move 불필요)
        st.session_state.pending_bot_move = data["first_bot_move"]
        
        return True

def process_turn(player_move):
    """
    [한 턴의 배틀 진행 처리 — API 호출]
    봇 행동은 prepare_bot_move()에서 미리 계산된 것을 사용하고,
    POST /api/v1/battle/process_turn 을 통해 배틀 로직을 실행합니다.
    봇 사망 시 강제 교체 메시지도 API가 생성하여 반환합니다.
    """
    # 1. 플레이어 교체 처리
    if player_move.get("category") == "switch":
        target_idx = player_move["target_index"]
        st.session_state.battle_player = st.session_state.player_party[target_idx]

    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    bot_party = st.session_state.bot_party

    # 2. 미리 계산된 봇 행동 가져오기 (없으면 즉시 API 호출)
    bot_move = st.session_state.pop("pending_bot_move", None)
    if bot_move is None:
        try:
            fallback_payload = {
                "bot_pokemon": _to_dict(bot),
                "player_pokemon": _to_dict(player),
                "bot_party": [_to_dict(bp) for bp in bot_party],
                "strategy": st.session_state.get("bot_strategy", "llm")
            }
            resp = requests.post(f"{BACKEND_URL}/api/v1/battle/decide_bot_move", json=fallback_payload, timeout=15)
            bot_move = resp.json()["bot_move"]
        except Exception as e:
            import random
            bot_move = random.choice(list(bot.moves))

    # 3. 봇 교체 행동이라면 플레이어 입력 이후인 지금 battle_bot 갱신
    if bot_move and bot_move.get("category") == "switch" and bot_move.get("is_bot"):
        target_idx = bot_move["target_index"]
        st.session_state.battle_bot = st.session_state.bot_party[target_idx]

    bot = st.session_state.battle_bot

    # 4. 배틀 로직 실행 → 백엔드 API 호출
    #    bot_party와 player_party의 현재 HP를 함께 전송하여 배틀 종료 여부를 백엔드가 판단
    payload = {
        "user_pokemon": _to_dict(player),
        "bot_pokemon": _to_dict(bot),
        "bot_party": [_to_dict(bp) for bp in bot_party],
        "player_party": [_to_dict(pp) for pp in st.session_state.player_party],
        "user_move": player_move,
        "bot_move": bot_move,
        "leader_name": st.session_state.get("leader_name", "관장")
    }
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/battle/process_turn",
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        st.session_state.pending_messages = result["messages"]
        st.session_state.pending_battle_over = result.get("battle_over", False)
        st.session_state.pending_winner = result.get("winner", None)
    except Exception as e:
        st.error(f"배틀 서버와 통신할 수 없습니다: {e}")