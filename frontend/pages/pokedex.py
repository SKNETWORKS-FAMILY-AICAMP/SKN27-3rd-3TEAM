import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui
from pokedex.ui import show

st.set_page_config(
    page_title="포켓몬 비공식 도감",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True)
show()
