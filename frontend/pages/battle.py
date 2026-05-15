import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"

from battle.battle import display_battle
from battle.build_team import display_builder
from battle.menu import display_menu
from battle.ui import inject_battle_styles, get_gym_bg_base64
from utils.ui import inject_common_ui

st.set_page_config(
    page_title="Battle - Pokemon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True)

# 선택된 관장에 맞는 체육관 배경 적용
# base64를 session_state에 캐싱 → 매 rerun에 동일 문자열 유지 → React style 태그 재렌더링 방지 → 깜빡임 제거
_leader = st.session_state.get("leader_name") or st.session_state.get("selected_leader", "웅이")
_bg_cache_key = f"_gym_bg_b64_{_leader}"
if _bg_cache_key not in st.session_state:
    st.session_state[_bg_cache_key] = get_gym_bg_base64(_leader)
inject_battle_styles(bg_url=st.session_state[_bg_cache_key])


def show():
    if "player_team" not in st.session_state:
        st.session_state.player_team = []
    if "battle_stage" not in st.session_state:
        st.session_state.battle_stage = "menu"

    if st.session_state.battle_stage == "menu":
        display_menu()
    elif st.session_state.battle_stage == "teambuilding":
        display_builder()
    elif st.session_state.battle_stage == "battle":
        display_battle()


if __name__ == "__main__":
    show()
