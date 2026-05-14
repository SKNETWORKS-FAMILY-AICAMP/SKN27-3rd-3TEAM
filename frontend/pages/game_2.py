import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import base64
import json

# Ensure frontend is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import inject_common_ui
from game2.styles import inject_game2_styles
from game2.template import get_game_html

st.set_page_config(
    page_title="포켓몬 메모리 게임",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

@st.cache_data
def get_base64_img(file_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for sub in ("main_background", "main_character", ""):
        path = os.path.join(base_dir, "img", sub, file_name)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

# ── Assets ───────────────────────────────────────────────────
bg_img = get_base64_img("minigame2_background.png")
char_img = get_base64_img("minigame2.png") # 카드 뒷면용 캐릭터 이미지

inject_common_ui(spacer=False)
inject_game2_styles(bg_img)

ARTWORK = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

POKEMON_POOL = [
    (1, "이상해씨"), (4, "파이리"),    (7, "꼬부기"),   (25, "피카츄"),
    (39, "푸린"),    (52, "나옹"),     (54, "고라파덕"), (94, "팬텀"),
    (131, "라프라스"),(133, "이브이"), (143, "잠만보"), (149, "망나뇽"),
    (150, "뮤츠"),   (6, "리자몽"),    (9, "거북왕"),
]

pool_json = json.dumps(
    [{"id": pid, "name": name, "img": f"{ARTWORK}/{pid}.png"} for pid, name in POKEMON_POOL],
    ensure_ascii=False,
)

# ── Main UI ──────────────────────────────────────────────────
_, col_main, _ = st.columns([1, 2.5, 1])

with col_main:
    # Header Title (Outside Card/Iframe)
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
    </div>
    """, unsafe_allow_html=True)

    GAME_HTML = get_game_html(char_img, pool_json)
    components.html(GAME_HTML, height=880, scrolling=False)
