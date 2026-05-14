import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"

from battle.battle import display_battle
from battle.build_team import display_builder
from battle.menu import display_menu
from battle.pokemon import PokemonDB
from battle.ui import inject_battle_styles
from utils.ui import inject_common_ui

# 페이지 설정
st.set_page_config(
    page_title="Battle - Pokemon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True)
inject_battle_styles()

# streamlit 페이지에서 DB 연결 (팀빌딩 화면용)
db = PokemonDB()

def show():
    if "player_team" not in st.session_state:
        st.session_state.player_team = []
    if "battle_stage" not in st.session_state:
        st.session_state.battle_stage = "menu"

    gym_leaders = ["웅이", "이슬이", "아이리스", "민화", "풍란", "채두", "순무", "지우", "N"]

    if st.session_state.battle_stage == "menu":
        display_menu()

    elif st.session_state.battle_stage == "teambuilding":
        display_builder()
    
    elif st.session_state.battle_stage == "battle":
        display_battle()

if __name__ == "__main__":
    show()
