import streamlit as st
import os
import sys

# Ensure frontend is in path
# Ensure frontend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from utils.ui import inject_common_ui
from minigame.ui import show_selector
from minigame.styles import inject_mini_game_style
from minigame.ui import show_selector
from pages.style.mini_game import inject_mini_game_style

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 미니 게임",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Common UI & Style ─────────────────────────────────────────
# ── Common UI & Style ─────────────────────────────────────────
inject_common_ui(spacer=False)
inject_mini_game_style()
inject_mini_game_style()

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    show_selector()
