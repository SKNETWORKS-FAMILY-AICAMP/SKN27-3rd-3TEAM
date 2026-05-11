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
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_V1_STR = "/api/v1/pokemon"
LOG_API_STR = "/api/v1/users/game-log"

# ── Image Assets ──────────────────────────────────────────────
ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"
GIF_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown"

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

def save_game_log(game_type, pokemon_id=None, is_correct=True, hint_used=False, log_data=None):
    user = st.session_state.get("user")
    user_id = user.get("db_id") if user else None
    
    payload = {
        "user_id": user_id,
        "game_type": game_type,
        "pokemon_id": pokemon_id,
        "is_correct": is_correct,
        "hint_used": hint_used,
        "log_data": json.dumps(log_data) if log_data else None
    }
    try:
        resp = requests.post(f"{BACKEND_URL}{LOG_API_STR}", json=payload, timeout=3)
        if resp.status_code != 200:
            st.warning(f"⚠️ 로그 저장 실패 (HTTP {resp.status_code}): {resp.text}")
    except Exception as e:
        st.warning(f"⚠️ 백엔드 연결 실패: {str(e)}")

bg_img = get_base64_img("mini_game.png")
inject_common_ui(spacer=False)

# ── Session State Initialization ──────────────────────────────
if "game_mode" not in st.session_state:
    st.session_state.game_mode = None
if "mem_cards" not in st.session_state:
    st.session_state.mem_cards = []
if "mem_flipped" not in st.session_state:
    st.session_state.mem_flipped = []
if "mem_matched" not in st.session_state:
    st.session_state.mem_matched = set()
if "mem_moves" not in st.session_state:
    st.session_state.mem_moves = 0
if "mem_logged" not in st.session_state:
    st.session_state.mem_logged = False

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

.memory-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; max-width: 600px; margin: 0 auto; }}
.mem-card {{
    aspect-ratio: 1; background: rgba(255, 255, 255, 0.1); border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px; display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: all 0.3s ease;
}}
.mem-card.flipped {{ background: white; transform: rotateY(180deg); }}
.mem-card img {{ width: 80%; height: 80%; object-fit: contain; }}

.header-card {{ background: var(--glass-bg); backdrop-filter: blur(15px); border: 1px solid var(--glass-border); border-radius: 25px; padding: 20px 60px; display: inline-block; margin-bottom: 45px; }}

/* Overlay Button */
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div {{ position: relative !important; height: 100%; }}
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] .element-container:has(button) {{
    position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important; z-index: 1000 !important; margin: 0 !important;
}}
[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] button {{
    width: 100% !important; height: 100% !important; min-height: 350px !important; opacity: 0 !important; cursor: pointer !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Helper Functions ──────────────────────────────────────────

def reset_memory():
    ids = random.sample(range(1, 152), 8)
    cards = []
    for pid in ids:
        cards.append({"id": pid, "img": f"{ART_URL}/{pid}.png"})
        cards.append({"id": pid, "img": f"{ART_URL}/{pid}.png"})
    random.shuffle(cards)
    st.session_state.mem_cards = cards
    st.session_state.mem_flipped = []
    st.session_state.mem_matched = set()
    st.session_state.mem_moves = 0
    st.session_state.mem_logged = False

# ── Game Views ────────────────────────────────────────────────

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
            <div class="game-title">포켓몬 짝 맞추기</div>
            <div class="game-desc">숨겨진 포켓몬들의 짝을 찾아보세요!<br>기억력 테스트의 시간입니다.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Memory", key="start_mem"):
            st.session_state.game_mode = "memory"
            reset_memory()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_memory_game():
    _, back_col, _ = st.columns([1, 8, 1])
    with back_col:
        if st.button("← 메뉴로 돌아가기", key="back_to_menu_mem"):
            st.session_state.game_mode = None
            st.rerun()

    st.markdown('<div class="game-container">', unsafe_allow_html=True)
    st.markdown('<h2 style="color: white; font-family: \'Outfit\'; font-weight: 900; font-size: 2.5rem;">포켓몬 짝 맞추기</h2>', unsafe_allow_html=True)
    st.markdown(f'<div style="background: rgba(255,255,255,0.1); border-radius: 15px; padding: 10px; display: inline-block; margin-bottom: 20px;"><p style="color: #FFCB05; font-weight: 800; font-size: 1.2rem; margin: 0;">시도 횟수: {st.session_state.mem_moves} | 맞춘 개수: {len(st.session_state.mem_matched)//2}/8</p></div>', unsafe_allow_html=True)

    # Grid logic
    cols = st.columns(4)
    for i, card in enumerate(st.session_state.mem_cards):
        with cols[i % 4]:
            is_flipped = i in st.session_state.mem_flipped or i in st.session_state.mem_matched
            if is_flipped:
                st.markdown(f'<div class="mem-card flipped"><img src="{card["img"]}"></div>', unsafe_allow_html=True)
            else:
                if st.button("?", key=f"card_{i}", use_container_width=True):
                    if len(st.session_state.mem_flipped) < 2 and i not in st.session_state.mem_flipped:
                        st.session_state.mem_flipped.append(i)
                        
                        if len(st.session_state.mem_flipped) == 2:
                            st.session_state.mem_moves += 1
                            idx1, idx2 = st.session_state.mem_flipped
                            if st.session_state.mem_cards[idx1]["id"] == st.session_state.mem_cards[idx2]["id"]:
                                st.session_state.mem_matched.add(idx1)
                                st.session_state.mem_matched.add(idx2)
                                st.session_state.mem_flipped = []
                                st.rerun()
                        st.rerun()

    if len(st.session_state.mem_flipped) == 2:
        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        if st.button("카드가 맞지 않습니다 (다음 시도)", key="clear_flipped", use_container_width=True):
            st.session_state.mem_flipped = []
            st.rerun()

    if len(st.session_state.mem_matched) == 16:
        st.balloons()
        st.success(f"축하합니다! {st.session_state.mem_moves}번 만에 모두 맞추셨습니다!")
        
        # 로그 저장 (한 번만)
        if not st.session_state.mem_logged:
            save_game_log("memory", is_correct=True, log_data={"moves": st.session_state.mem_moves})
            st.session_state.mem_logged = True
            
        if st.button("다시 하기", key="reset_mem_btn", use_container_width=True):
            reset_memory()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def main():
    if st.session_state.game_mode == "memory":
        show_memory_game()
    else:
        show_selector()

if __name__ == "__main__":
    main()
