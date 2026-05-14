import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui
from game2.styles import inject_game2_styles
from game2.template import GAME_HTML

st.set_page_config(
    page_title="포켓몬 메모리 게임",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_base64_img(file_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for sub in ("main_background", "main_character", ""):
        path = (
            os.path.join(base_dir, "img", sub, file_name)
            if sub
            else os.path.join(base_dir, "img", file_name)
        )
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""


inject_common_ui(spacer=False)
inject_game2_styles(get_base64_img("minigame_background.png"))
components.html(GAME_HTML, height=900, scrolling=False)
