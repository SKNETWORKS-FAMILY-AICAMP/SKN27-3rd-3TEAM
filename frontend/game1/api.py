import os
import requests
import json
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"
API_V1_STR = "/api/v1/pokemon"
LOG_API_STR = "/api/v1/users/game-log"

def load_pokemon_data():
    """포켓몬 목록을 세션당 1회만 로드해서 캐시합니다."""
    if "_pokemon_data" in st.session_state:
        return st.session_state["_pokemon_data"]
    try:
        resp = requests.get(
            f"{BACKEND_URL}{API_V1_STR}/",
            params={"limit": 2000, "max_id": 1025},
            timeout=15,
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            data = [
                {"id": item["id"], "name": item["name"], "types": item.get("types", [])}
                for item in items
                if 1 <= item["id"] <= 1025 and item.get("name")
            ]
            if data:
                st.session_state["_pokemon_data"] = data
                return data
    except Exception:
        pass
    fallback = [{"id": 25, "name": "피카츄", "types": [{"slot": 1, "type_": {"id": 13, "name": "전기"}}]}]
    st.session_state["_pokemon_data"] = fallback
    return fallback

def save_game_log(game_type, pokemon_id, is_correct, hint_used=False, wrong_answer_name=None, log_data=None):
    user = st.session_state.get("user")
    user_id = user.get("db_id") if user else None

    extra = log_data or {}
    if wrong_answer_name:
        extra["wrong_name"] = wrong_answer_name

    payload = {
        "user_id": user_id,
        "game_type": game_type,
        "pokemon_id": pokemon_id,
        "is_correct": is_correct,
        "hint_used": hint_used,
        "log_data": json.dumps(extra) if extra else None,
    }

    try:
        requests.post(f"{BACKEND_URL}{LOG_API_STR}", json=payload, timeout=3)
    except Exception:
        pass
