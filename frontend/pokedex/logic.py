import streamlit as st
from pokedex.constants import REGION_RANGES


def toggle_type(en):
    lst = st.session_state.selected_types
    if en in lst:
        lst.remove(en)
    else:
        lst.append(en)


def do_reset():
    st.session_state.search_query = ""
    st.session_state.selected_types = []
    st.session_state.region_filter = "전체"
    st.session_state.dex_start = 1
    st.session_state.dex_end = 1025
    st.session_state.dex_range_slider = (1, 1025)
    st.session_state.ability_filter = "전체"


def load_more():
    st.session_state.pokemon_limit += 50


def select_region(region):
    st.session_state.region_filter = region
    start, end = REGION_RANGES.get(region, (1, 1025))
    st.session_state.dex_start = start
    st.session_state.dex_end = end
    st.session_state.dex_range_slider = (start, end)


def handle_search():
    st.session_state.search_query = st.session_state.search_input
    if "ability_sel" in st.session_state:
        st.session_state.ability_filter = st.session_state.ability_sel
    if "dex_range_slider" in st.session_state:
        st.session_state.dex_start = st.session_state.dex_range_slider[0]
        st.session_state.dex_end = st.session_state.dex_range_slider[1]
