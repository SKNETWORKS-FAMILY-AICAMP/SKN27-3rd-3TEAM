import streamlit as st
import sys
import os

# Ensure utils is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

st.set_page_config(
    page_title="Team Builder - Pokémon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
)

# Inject common UI (Header, Follower, Global Styles)
inject_common_ui(spacer=True)

def show():
    st.title("팀 빌딩")
    
if __name__ == "__main__":
    show()
