import json
import os
import random
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(frontend_dir)
data_dir = os.path.join(root_dir, "database", "common", "data", "processed")

load_dotenv(os.path.join(root_dir, ".env"))

if frontend_dir not in sys.path:
    sys.path.append(frontend_dir)

from utils.ui import inject_common_ui

ROSTER = [
    {"pokemon_id": 445, "name": "한카리아스", "moves": ["지진", "스케일샷", "칼춤", "암석봉인"]},
    {"pokemon_id": 6, "name": "리자몽", "moves": ["솔라빔", "화염방사", "용의춤", "에어슬래시"]},
    {"pokemon_id": 149, "name": "망나뇽", "moves": ["용성군", "신속", "10만볼트", "화염방사"]},
    {"pokemon_id": 908, "name": "마스카나", "moves": ["트릭플라워", "트리플악셀", "기습", "치근거리기"]},
    {"pokemon_id": 212, "name": "핫삼", "moves": ["칼춤", "불릿펀치", "인파이트", "날개쉬기"]},
    {"pokemon_id": 448, "name": "루카리오", "moves": ["인파이트", "불릿펀치", "칼춤", "지진"]},
    {"pokemon_id": 248, "name": "마기라스", "moves": ["스톤에지", "지진", "용의춤", "깨물어부수기"]},
    {"pokemon_id": 887, "name": "드래펄트", "moves": ["드래곤애로", "유턴", "고스트다이브", "기습"]},
    {"pokemon_id": 9, "name": "거북왕", "moves": ["껍질깨기", "물의파동", "파동탄", "냉동빔"]},
    {"pokemon_id": 143, "name": "잠만보", "moves": ["지진", "누르기", "잠자기", "땅가르기"]},
]

CUSTOM_MOVES = {
    "트릭플라워": {
        "id": 90001,
        "name": "트릭플라워",
        "type_id": 12,
        "power": 70,
        "accuracy": 100,
        "damage_class": "physical",
        "effect_text": "마스카나의 필살기. 꽃다발에 숨긴 폭탄으로 공격한다.",
    }
}

PRIORITY_MOVES = {"신속": 2, "기습": 1, "불릿펀치": 1}
ATTACK_BUFFS = {"칼춤", "용의춤", "껍질깨기"}
HEAL_MOVES = {"잠자기", "날개쉬기"}
STATUS_MOVES = ATTACK_BUFFS | HEAL_MOVES

st.set_page_config(
    page_title="Battle - Pokemon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True)


@dataclass
class BattlePokemon:
    id: int
    name: str
    image_url: str
    types: List[int]
    type_names: List[str]
    stats: Dict[str, int]
    moves: List[Dict]
    current_hp: int
    max_hp: int
    attack_stage: int = 0
    sp_attack_stage: int = 0
    defense_stage: int = 0
    sp_defense_stage: int = 0
    speed_stage: int = 0


@st.cache_data(show_spinner=False)
def load_json(filename: str):
    with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_battle_data():
    pokemon = {p["id"]: p for p in load_json("pokemon.json") if p.get("is_default", True)}
    stats = {s["pokemon_id"]: s for s in load_json("pokemon_stats.json")}
    types = {t["id"]: t["name"] for t in load_json("types.json")}
    moves = {m["id"]: m for m in load_json("moves.json")}
    moves_by_name = {m["name"]: m for m in moves.values()}
    moves_by_name.update(CUSTOM_MOVES)

    pokemon_types: Dict[int, List[Tuple[int, int]]] = {}
    for item in load_json("pokemon_types.json"):
        pokemon_types.setdefault(item["pokemon_id"], []).append((item["slot"], item["type_id"]))

    efficacy = {}
    for item in load_json("type_efficacy.json"):
        efficacy[(item["damage_type_id"], item["target_type_id"])] = float(item["damage_factor"])

    return pokemon, stats, types, moves_by_name, pokemon_types, efficacy


def get_roster_entry(pokemon_id: int) -> Dict:
    return next(entry for entry in ROSTER if entry["pokemon_id"] == pokemon_id)


def display_name(entry: Dict) -> str:
    return f"No.{entry['pokemon_id']:04d} {entry['name']}"


def build_battle_pokemon(entry: Dict, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types) -> BattlePokemon:
    base = all_pokemon[entry["pokemon_id"]]
    raw_stats = all_stats.get(
        entry["pokemon_id"],
        {"hp": 80, "attack": 80, "defense": 80, "sp_attack": 80, "sp_defense": 80, "speed": 80},
    )
    type_ids = [tid for _, tid in sorted(pokemon_types.get(entry["pokemon_id"], []))]
    selected_moves = []
    for move_name in entry["moves"]:
        if move_name not in moves_by_name:
            raise ValueError(f"기술 데이터를 찾을 수 없습니다: {move_name}")
        selected_moves.append(dict(moves_by_name[move_name]))

    max_hp = int(raw_stats.get("hp") or 80) * 2
    return BattlePokemon(
        id=entry["pokemon_id"],
        name=entry["name"],
        image_url=base.get("image_url") or "",
        types=type_ids,
        type_names=[all_types.get(tid, str(tid)) for tid in type_ids],
        stats=dict(raw_stats),
        moves=selected_moves,
        current_hp=max_hp,
        max_hp=max_hp,
    )


def reset_battle():
    for key in [
        "battle_player",
        "battle_bot",
        "battle_messages",
        "battle_over",
        "winner",
        "turn_count",
        "hidden_bot_entry",
    ]:
        st.session_state.pop(key, None)


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
    if move["name"] == "트리플악셀":
        power = 60
    elif move["name"] == "스케일샷":
        power = 75
    elif move["name"] == "드래곤애로":
        power = 100

    damage_class = move.get("damage_class") or "physical"
    attack_key = "sp_attack" if damage_class == "special" else "attack"
    defense_key = "sp_defense" if damage_class == "special" else "defense"
    attack = stat_value(attacker, attack_key)
    defense = stat_value(defender, defense_key)
    stab = 1.5 if move.get("type_id") in attacker.types else 1.0
    multiplier = type_multiplier(move.get("type_id"), defender, efficacy)
    base = (((2 * 50 / 5 + 2) * power * attack / defense) / 50) + 2
    return max(1, int(base * stab * multiplier))


def heuristic_score(attacker: BattlePokemon, defender: BattlePokemon, move: Dict, efficacy: Dict[Tuple[int, int], float]) -> float:
    name = move["name"]
    if name in HEAL_MOVES:
        return 95 * (1 - attacker.current_hp / attacker.max_hp)
    if name in ATTACK_BUFFS:
        boosted = attacker.attack_stage + attacker.sp_attack_stage + attacker.speed_stage
        return 52 if boosted <= 1 and attacker.current_hp > attacker.max_hp * 0.38 else 14
    return estimate_damage(attacker, defender, move, efficacy) * ((move.get("accuracy") or 100) / 100)


def heuristic_best_move(attacker: BattlePokemon, defender: BattlePokemon, efficacy: Dict[Tuple[int, int], float]) -> Dict:
    return max(attacker.moves, key=lambda move: heuristic_score(attacker, defender, move, efficacy))


def call_llm_for_move(bot: BattlePokemon, player: BattlePokemon, efficacy: Dict[Tuple[int, int], float]) -> Tuple[Dict, str]:
    fallback = heuristic_best_move(bot, player, efficacy)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return fallback, "OPENAI_API_KEY가 없어 전술 폴백 AI가 선택했습니다."

    try:
        from openai import OpenAI

        move_context = [
            {
                "id": move["id"],
                "name": move["name"],
                "power": move.get("power"),
                "accuracy": move.get("accuracy"),
                "damage_class": move.get("damage_class"),
                "type_multiplier": type_multiplier(move.get("type_id"), player, efficacy),
                "estimated_damage": estimate_damage(bot, player, move, efficacy),
                "tactical_score": round(heuristic_score(bot, player, move, efficacy), 2),
            }
            for move in bot.moves
        ]
        prompt = {
            "bot": {
                "name": bot.name,
                "hp": bot.current_hp,
                "max_hp": bot.max_hp,
                "types": bot.type_names,
                "attack_stage": bot.attack_stage,
                "sp_attack_stage": bot.sp_attack_stage,
                "speed_stage": bot.speed_stage,
            },
            "opponent": {
                "name": player.name,
                "hp": player.current_hp,
                "max_hp": player.max_hp,
                "types": player.type_names,
                "speed": stat_value(player, "speed"),
            },
            "available_moves": move_context,
            "instruction": "Choose exactly one move id. Use Korean in reason. Return JSON only.",
        }
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_BATTLE_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a competitive Pokemon battle AI. Return compact JSON: {\"move_id\": number, \"reason\": string}."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            temperature=0.2,
            timeout=15,
        )
        content = response.choices[0].message.content or ""
        match = re.search(r"\{.*\}", content, flags=re.S)
        parsed = json.loads(match.group(0) if match else content)
        selected_id = int(parsed.get("move_id"))
        selected = next((m for m in bot.moves if m["id"] == selected_id), fallback)
        return selected, parsed.get("reason") or "LLM이 현재 HP, 랭크, 상성, 예상 데미지를 기준으로 선택했습니다."
    except Exception as exc:
        return fallback, f"LLM 호출 실패로 전술 폴백 AI를 사용했습니다. ({exc})"


def fmt_player(name: str) -> str:
    return f"<span class='player-text'>{name}</span>"


def fmt_bot(name: str) -> str:
    return f"<span class='bot-text'>{name}</span>"


def fmt_move(name: str) -> str:
    return f"<span class='move-text'>{name}</span>"


def apply_status_move(user: BattlePokemon, move: Dict) -> str:
    name = move["name"]
    colored_user = fmt_player(user.name) if user is st.session_state.get("battle_player") else fmt_bot(user.name)
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

    attacker_name = fmt_player(attacker.name) if attacker is st.session_state.get("battle_player") else fmt_bot(attacker.name)
    defender_name = fmt_player(defender.name) if defender is st.session_state.get("battle_player") else fmt_bot(defender.name)
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
    if multiplier == 0:
        effect_text = " 효과가 없습니다."
    elif multiplier >= 2:
        effect_text = " 효과가 굉장했습니다!"
    elif 0 < multiplier < 1:
        effect_text = " 효과가 별로인 듯합니다."

    return f"{attacker_name}의 {move_name}! {defender_name}에게 {damage} 데미지.{effect_text}"


def find_player_move(text: str, player: BattlePokemon) -> Optional[Dict]:
    normalized = re.sub(r"\s+", "", text.strip().lower())
    for move in player.moves:
        move_name = re.sub(r"\s+", "", move["name"].lower())
        if normalized == move_name or move_name in normalized:
            return move
    return None


def process_turn(player_move: Dict, efficacy):
    player = st.session_state.battle_player
    bot = st.session_state.battle_bot
    bot_move, _ = call_llm_for_move(bot, player, efficacy)

    st.session_state.turn_count += 1
    lines = [
        f"Turn {st.session_state.turn_count}",
        f"당신: {fmt_player(player.name)}에게 {fmt_move(player_move['name'])}을 지시했습니다.",
        f"LLM Bot: {fmt_bot(bot.name)}은 {fmt_move(bot_move['name'])}을 선택했습니다.",
    ]

    player_priority = PRIORITY_MOVES.get(player_move["name"], 0)
    bot_priority = PRIORITY_MOVES.get(bot_move["name"], 0)
    order = [(player, bot, player_move), (bot, player, bot_move)]
    if bot_priority > player_priority:
        order.reverse()
    elif bot_priority == player_priority:
        if stat_value(bot, "speed") > stat_value(player, "speed"):
            order.reverse()
        elif stat_value(bot, "speed") == stat_value(player, "speed"):
            random.shuffle(order)

    for attacker, defender, move in order:
        if attacker.current_hp <= 0:
            continue
        lines.append(resolve_attack(attacker, defender, move, efficacy))
        if defender.current_hp <= 0:
            defender_name = fmt_player(defender.name) if defender is player else fmt_bot(defender.name)
            winner_label = "USER" if attacker is player else "LLM"
            lines.append(f"{defender_name}이 쓰러졌습니다.")
            st.session_state.battle_over = True
            st.session_state.winner = winner_label
            lines.append(f"승리: {winner_label}")
            break

    st.session_state.battle_messages.append({"role": "assistant", "content": "\n\n".join(lines)})


def inject_battle_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background: #0f172a;
        }
        [data-testid="stAppViewBlockContainer"] {
            max-width: 1180px;
            padding-top: 1.2rem;
        }
        .battle-header {
            border: 1px solid rgba(148, 163, 184, .28);
            border-radius: 8px;
            padding: 18px;
            background: rgba(15, 23, 42, .78);
            margin-bottom: 16px;
        }
        .battle-header h1 {
            margin: 0;
            color: #f8fafc;
            font-size: 2rem;
            letter-spacing: 0;
        }
        .battle-header p {
            color: rgba(226, 232, 240, .78);
            margin: 8px 0 0;
        }
        .status-card {
            border: 1px solid rgba(148, 163, 184, .24);
            border-radius: 8px;
            background: rgba(30, 41, 59, .7);
            padding: 14px;
            min-height: 245px;
            text-align: center;
        }
        .status-card img {
            width: 150px;
            height: 150px;
            object-fit: contain;
            filter: drop-shadow(0 16px 24px rgba(0,0,0,.38));
        }
        .pokemon-name {
            color: #fff;
            font-weight: 900;
            font-size: 1.2rem;
        }
        .type-pill {
            display: inline-flex;
            padding: 3px 9px;
            margin: 6px 3px 0;
            border-radius: 999px;
            background: rgba(15, 23, 42, .85);
            color: #e5e7eb;
            font-size: .8rem;
            font-weight: 800;
        }
        .hp-label {
            color: #e5e7eb;
            font-weight: 800;
            font-size: .88rem;
            margin-top: 8px;
        }
        .move-chip {
            display: inline-flex;
            margin: 3px;
            padding: 5px 9px;
            border-radius: 999px;
            background: rgba(59, 130, 246, .18);
            border: 1px solid rgba(96, 165, 250, .28);
            color: #dbeafe;
            font-size: .84rem;
            font-weight: 800;
        }
        .secret-card {
            height: 235px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            border: 1px dashed rgba(226, 232, 240, .35);
            background: rgba(30, 41, 59, .52);
            color: #e5e7eb;
            font-size: 1.8rem;
            font-weight: 900;
            text-align: center;
        }
        .chat-tip {
            color: rgba(226,232,240,.72);
            font-size: .9rem;
            margin: 8px 0 14px;
        }
        div[data-testid="stChatMessage"] {
            background: #ffffff;
            border: 1px solid rgba(15, 23, 42, .16);
            border-radius: 8px;
            color: #000000 !important;
        }
        div[data-testid="stChatMessage"] * {
            color: #000000 !important;
        }
        div[data-testid="stChatMessage"] p {
            color: #000000 !important;
            font-weight: 650;
            line-height: 1.58;
        }
        .player-text {
            color: #0066ff !important;
            font-weight: 900;
        }
        .bot-text {
            color: #e11d48 !important;
            font-weight: 900;
        }
        .move-text {
            color: #c2410c !important;
            font-weight: 950;
        }
        div[data-testid="stChatMessage"] .player-text {
            color: #0066ff !important;
            font-weight: 900;
        }
        div[data-testid="stChatMessage"] .bot-text {
            color: #e11d48 !important;
            font-weight: 900;
        }
        div[data-testid="stChatMessage"] .move-text {
            color: #c2410c !important;
            font-weight: 950;
        }
        h2, h3, label, p { color: #f8fafc; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_pokemon_status(title: str, pokemon: BattlePokemon, reveal_details: bool = True):
    type_html = "".join(f"<span class='type-pill'>{type_name}</span>" for type_name in pokemon.type_names)
    move_html = "".join(f"<span class='move-chip'>{move['name']}</span>" for move in pokemon.moves) if reveal_details else ""
    hp_text = f"HP {pokemon.current_hp}/{pokemon.max_hp}" if reveal_details else "HP"
    st.markdown(
        f"""
        <div class="status-card">
            <div style="color:rgba(226,232,240,.72);font-weight:900;">{title}</div>
            <img src="{pokemon.image_url}" alt="{pokemon.name}">
            <div class="pokemon-name">{pokemon.name}</div>
            <div>{type_html}</div>
            <div class="hp-label">{hp_text}</div>
            <div style="margin-top:8px;">{move_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(max(0.0, min(1.0, pokemon.current_hp / pokemon.max_hp)))


def start_battle(selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types):
    reset_battle()
    candidates = [entry for entry in ROSTER if entry["pokemon_id"] != selected_player_entry["pokemon_id"]]
    bot_entry = random.choice(candidates)
    st.session_state.hidden_bot_entry = bot_entry
    st.session_state.battle_player = build_battle_pokemon(
        selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types
    )
    st.session_state.battle_bot = build_battle_pokemon(
        bot_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types
    )
    st.session_state.battle_messages = [
        {
            "role": "assistant",
            "content": (
                "배틀이 시작되었습니다.\n\n"
                f"상대 LLM Bot의 포켓몬은 {fmt_bot(bot_entry['name'])}입니다.\n\n"
                "이제 채팅창에 사용할 기술명을 입력해 주세요."
            ),
        }
    ]
    st.session_state.battle_over = False
    st.session_state.winner = None
    st.session_state.turn_count = 0


def show():
    all_pokemon, all_stats, all_types, moves_by_name, pokemon_types, efficacy = load_battle_data()
    inject_battle_styles()

    st.markdown(
        """
        <div class="battle-header">
            <h1>Pokemon 1대1 LLM 채팅 배틀</h1>
            <p>내 포켓몬을 고르고 배틀을 시작하세요. 상대는 시작 전까지 비공개이며, 이후 채팅창에 기술명을 입력해 턴을 진행합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_player_id = st.selectbox(
        "내 포켓몬",
        [entry["pokemon_id"] for entry in ROSTER],
        format_func=lambda pid: display_name(get_roster_entry(pid)),
        disabled="battle_player" in st.session_state,
    )
    selected_player_entry = get_roster_entry(selected_player_id)

    if "battle_player" not in st.session_state:
        preview = build_battle_pokemon(selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types)
        left, right = st.columns([1, 1])
        with left:
            render_pokemon_status("PLAYER ENTRY", preview)
        with right:
            st.markdown("<div class='secret-card'>LLM BOT<br>???</div>", unsafe_allow_html=True)
            st.markdown("<div class='chat-tip'>배틀 시작 버튼을 누르면 상대 포켓몬이 공개됩니다.</div>", unsafe_allow_html=True)

        if st.button("배틀 시작", use_container_width=True):
            start_battle(selected_player_entry, all_pokemon, all_stats, all_types, moves_by_name, pokemon_types)
            st.rerun()
        return

    player = st.session_state.battle_player
    bot = st.session_state.battle_bot

    top_cols = st.columns([1, 1])
    with top_cols[0]:
        render_pokemon_status("PLAYER", player)
    with top_cols[1]:
        render_pokemon_status("LLM BOT", bot, reveal_details=False)

    if st.button("새 배틀 준비"):
        reset_battle()
        st.rerun()

    st.markdown(
        "<div class='chat-tip'>사용 가능한 내 기술: "
        + " / ".join(move["name"] for move in player.moves)
        + "</div>",
        unsafe_allow_html=True,
    )

    for message in st.session_state.get("battle_messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    if st.session_state.get("battle_over"):
        st.info(f"배틀 종료. 승리: {st.session_state.winner}")
        return

    prompt = st.chat_input(f"{player.name}에게 지시를 내리세요!")
    if prompt:
        st.session_state.battle_messages.append({"role": "user", "content": prompt})
        player_move = find_player_move(prompt, player)
        if not player_move:
            st.session_state.battle_messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "그 기술은 현재 사용할 수 없습니다. 사용 가능한 기술은 "
                        + " / ".join(fmt_move(move["name"]) for move in player.moves)
                        + " 입니다."
                    ),
                }
            )
        else:
            process_turn(player_move, efficacy)
        st.rerun()


if __name__ == "__main__":
    show()
