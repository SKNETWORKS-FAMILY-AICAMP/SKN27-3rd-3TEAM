import streamlit as st
import sys
import os

# Ensure utils is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

st.set_page_config(
    page_title="Pokedex - Pokémon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
)

# Inject common UI (Header, Follower, Global Styles)
inject_common_ui(spacer=True)

st.title("포켓몬 도감")
st.write("전국 도감의 모든 포켓몬 정보를 확인하세요.")
