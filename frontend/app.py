import streamlit as st
from utils.ui import inject_common_ui
from utils.images import load_backgrounds, load_characters
from landing.styles import get_landing_css
from landing.sections import get_home_html, get_home_js

st.set_page_config(
    page_title="포켓몬 비공식 사이트",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui()

bg    = load_backgrounds()
chars = load_characters()

st.markdown(get_landing_css(bg),          unsafe_allow_html=True)
st.markdown(get_home_html(bg, chars),     unsafe_allow_html=True)
st.markdown(get_home_js(),                unsafe_allow_html=True)
