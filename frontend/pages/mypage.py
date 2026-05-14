import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui
from mypage.styles import inject_mypage_styles
from mypage.api import _b64_img
from mypage.ui import show

st.set_page_config(
    page_title="마이페이지",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_mypage_styles(_b64_img("img/mypage.png"))
inject_common_ui(spacer=False)
show()
