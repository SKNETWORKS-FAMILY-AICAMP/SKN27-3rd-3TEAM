import streamlit as st
import requests
import random
import os
import sys
import base64
import json

# Ensure utils is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

# ── Backend Configuration ─────────────────────────────────────
BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"
API_V1_STR = "/api/v1/pokemon"
LOG_API_STR = "/api/v1/users/game-log"

# ── Image Assets ──────────────────────────────────────────────
ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 미니 게임",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_base64_img(file_name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

bg_img = get_base64_img("mini_game.png")
inject_common_ui(spacer=False)

# ── Session State ─────────────────────────────────────────────
if "game_mode" not in st.session_state:
    st.session_state.game_mode = None

# ── Styles ───────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

:root {{
    --glass-bg: rgba(20, 20, 20, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
    --poke-red: #E33535;
}}

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
    background: url('{bg_img}') center/cover no-repeat fixed !important;
    background-color: #000000 !important;
}}

[data-testid="stAppViewBlockContainer"], .main {{ background-color: transparent !important; }}
.game-container {{ max-width: 1400px; margin: 0 auto; padding: 10px 20px; text-align: center; }}

.game-card {{
    background: var(--glass-bg); backdrop-filter: blur(20px); border: 1px solid var(--glass-border);
    border-radius: 40px; width: 95%; margin: 0 auto; padding: 40px 20px 65px;
    display: flex; flex-direction: column; align-items: center;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    cursor: pointer; position: relative; overflow: hidden;
    box-shadow: 0 30px 100px rgba(0,0,0,0.6);
}}

div[data-testid="stColumn"]:hover .game-card {{
    transform: translateY(-15px) scale(1.02);
    border-color: var(--poke-red);
    box-shadow: 0 30px 80px rgba(227, 53, 53, 0.3);
}}

.game-card img {{ width: 250px; height: 250px; object-fit: contain; margin-bottom: 15px; filter: drop-shadow(0 15px 35px rgba(0,0,0,0.4)); }}
.game-title {{ font-family: 'Outfit', sans-serif; font-size: 2.0rem; font-weight: 900; color: #fff; margin-bottom: 5px; }}
.game-desc {{ font-family: 'Inter', sans-serif; color: #ccc; font-size: 1.0rem; line-height: 1.5; opacity: 0; transform: translateY(10px); transition: all 0.5s ease; }}
div[data-testid="stColumn"]:hover .game-desc {{ opacity: 1; transform: translateY(0); margin-top: 20px; }}

.header-card {{ background: var(--glass-bg); backdrop-filter: blur(15px); border: 1px solid var(--glass-border); border-radius: 25px; padding: 20px 60px; display: inline-block; margin-bottom: 45px; }}

/* Overlay Button Click */
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div {{ position: relative !important; height: 100%; }}
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] .element-container:has(button) {{
    position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important; z-index: 1000 !important; margin: 0 !important;
}}
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] button {{
    width: 100% !important; height: 100% !important; min-height: 350px !important; opacity: 0 !important; cursor: pointer !important;
}}
</style>
""", unsafe_allow_html=True)

def show_selector():
    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="header-card">
        <h1 style="font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 3rem; color: white; margin: 0;">Pokémon Mini Games</h1>
        <p style="color: #ccc; font-size: 1.1rem; margin: 5px 0 0;">즐기고 싶은 게임을 선택하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    _, col1, col2, _ = st.columns([1, 5, 5, 1])
    
    with col1:
        st.markdown(f"""
        <div class="game-card">
            <img src="{ART_URL}/25.png" style="filter: brightness(0);">
            <div class="game-title">실루엣 퀴즈</div>
            <div class="game-desc">그림자만 보고 어떤 포켓몬인지 맞혀보세요!<br>포켓몬 박사라면 식은 죽 먹기죠?</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Silhouette", key="start_sil"):
            st.switch_page("pages/game_1.py")

    with col2:
        st.markdown(f"""
        <div class="game-card">
            <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png">
            <div class="game-title">포켓몬 랩배틀</div>
            <div class="game-desc">포켓몬들의 찰진 디스전!<br>상성과 설정을 이용한 영혼의 랩 배틀을 감상하세요.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Battle", key="start_battle"):
            st.switch_page("pages/game_2.py")
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    show_selector()

if __name__ == "__main__":
    main()
