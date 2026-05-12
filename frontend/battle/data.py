import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import streamlit as st

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend/battle
frontend_dir = os.path.dirname(current_dir)               # frontend
root_dir = os.path.dirname(frontend_dir)                 # root
data_dir = os.path.join(root_dir, "database", "common", "data", "processed")

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
    ailment: Optional[str] = None
    sleep_turns: int = 0

@st.cache_data(show_spinner=False)
def load_json(filename: str):
    path = os.path.join(data_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_battle_data():
    pokemon = {p["id"]: p for p in load_json("pokemon.json") if p.get("is_default", True)}
    stats = {s["pokemon_id"]: s for s in load_json("pokemon_stats.json")}
    types = {t["id"]: t["name"] for t in load_json("types.json")}
    moves = {m["id"]: m for m in load_json("moves.json")}
    moves_by_name = {m["name"]: m for m in moves.values()}
    moves_by_name.update(CUSTOM_MOVES)

    pokemon_types = {}
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
