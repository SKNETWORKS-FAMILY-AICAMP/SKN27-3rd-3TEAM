import streamlit as st
import os
import sys

# Ensure frontend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import inject_common_ui
from game1.logic import show_game
from game1.styles import inject_game_1_style

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 비공식 실루엣",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Common UI & Style ─────────────────────────────────────────
inject_common_ui(spacer=False)
inject_game_1_style()

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    show_game()
