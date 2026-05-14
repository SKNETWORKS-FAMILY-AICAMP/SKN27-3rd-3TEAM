import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui
from teambuilding.styles import apply_page_style
from teambuilding.constants import REQUIRED_TEAM_SIZE
from teambuilding.api import load_pokemon_list, find_selected_pokemon, request_json
from teambuilding.filters import filter_team_pokemon_list
from teambuilding.components import (
    render_pokemon_card,
    render_team_filter_panel,
    render_team_side_panel,
    render_analysis_result,
    render_recommendation_result,
    render_selected_slots,
)

st.set_page_config(
    page_title="팀빌딩",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

inject_common_ui(spacer=True)


def show() -> None:
    apply_page_style()

    if "selected_pokemon_ids" not in st.session_state:
        st.session_state.selected_pokemon_ids = []
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "recommendation_result" not in st.session_state:
        st.session_state.recommendation_result = None

    st.markdown("<div class='main-title'>포켓몬스터 선택</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='sub-title'>({REQUIRED_TEAM_SIZE}마리를 선택해야합니다.)</div>",
        unsafe_allow_html=True,
    )

    try:
        pokemon_list = load_pokemon_list()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    selected_pokemon = find_selected_pokemon(pokemon_list, st.session_state.selected_pokemon_ids)
    generation_values = sorted(
        {p["generation"] for p in pokemon_list if p.get("generation") is not None}
    )

    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        selected_generation = st.selectbox("세대", ["전체"] + generation_values)
    with search_col:
        keyword = st.text_input("검색", placeholder="포켓몬 이름 또는 번호 검색")

    filtered_pokemon = pokemon_list
    if selected_generation != "전체":
        filtered_pokemon = [p for p in filtered_pokemon if p.get("generation") == selected_generation]
    if keyword:
        filtered_pokemon = [
            p for p in filtered_pokemon
            if keyword.lower() in p["name"].lower() or keyword.strip() == str(p["pokemon_id"])
        ]

    st.divider()

    with st.container(height=560, border=True):
        COLS = 6
        for row_start in range(0, len(filtered_pokemon), COLS):
            row_pokemon = filtered_pokemon[row_start:row_start + COLS]
            row_cols = st.columns(COLS)
            for col, p in zip(row_cols, row_pokemon):
                with col:
                    render_pokemon_card(p)

    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])
    with action_col1:
        if st.button("선택 초기화", use_container_width=True):
            st.session_state.selected_pokemon_ids = []
            st.session_state.analysis_result = None
            st.session_state.recommendation_result = None
            st.rerun()

    can_request = len(st.session_state.selected_pokemon_ids) == REQUIRED_TEAM_SIZE
    with action_col2:
        if st.button("덱 분석", disabled=not can_request, use_container_width=True):
            st.session_state.analysis_result = request_json(
                "POST", "/api/v1/team-builder/rag-analyze",
                json={"pokemon_ids": st.session_state.selected_pokemon_ids},
            )
    with action_col3:
        if st.button("추천 받기", disabled=not can_request, use_container_width=True):
            st.session_state.recommendation_result = request_json(
                "POST", "/api/v1/team-builder/rag-recommend",
                json={"pokemon_ids": st.session_state.selected_pokemon_ids, "limit": 3},
            )

    if st.session_state.analysis_result:
        render_analysis_result(st.session_state.analysis_result)
    if st.session_state.recommendation_result:
        render_recommendation_result(st.session_state.recommendation_result)


def show_v2() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    apply_page_style()

    if "selected_pokemon_ids" not in st.session_state:
        st.session_state.selected_pokemon_ids = []
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "recommendation_result" not in st.session_state:
        st.session_state.recommendation_result = None

    try:
        pokemon_list = load_pokemon_list()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    render_team_filter_panel(pokemon_list)
    filtered_pokemon = filter_team_pokemon_list(pokemon_list)

    selected_pokemon = find_selected_pokemon(pokemon_list, st.session_state.selected_pokemon_ids)
    can_request = len(st.session_state.selected_pokemon_ids) == REQUIRED_TEAM_SIZE

    grid_col, panel_col = st.columns([3, 1], gap="medium")

    with grid_col:
        with st.container(height=580, border=False):
            limit = st.session_state.get("team_pokemon_limit", 50)
            chunk = filtered_pokemon[:limit]
            COLS = 5
            for row_start in range(0, len(chunk), COLS):
                row_pokemon = chunk[row_start:row_start + COLS]
                row_cols = st.columns(COLS)
                for col, p in zip(row_cols, row_pokemon):
                    with col:
                        render_pokemon_card(p)

            if len(filtered_pokemon) > limit:
                st.markdown("""
                    <style>
                        .team-load-more-marker + div[data-testid="stButton"] {
                            display: none !important;
                        }
                        .team-infinite-loader {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            padding: 20px 0;
                            gap: 8px;
                            color: #888;
                            font-size: 0.85rem;
                        }
                        .pokeball-loader {
                            width: 30px; height: 30px;
                            border: 2px solid #333;
                            border-radius: 50%;
                            position: relative;
                            background: linear-gradient(to bottom, #EE1515 50%, white 50%);
                            animation: spin 1s linear infinite;
                        }
                        .pokeball-loader::after {
                            content: ''; position: absolute;
                            width: 30px; height: 2px;
                            background: #333; top: 50%;
                            transform: translateY(-50%);
                        }
                        .pokeball-loader::before {
                            content: ''; position: absolute;
                            width: 8px; height: 8px;
                            background: white; border: 2px solid #333;
                            border-radius: 50%; top: 50%; left: 50%;
                            transform: translate(-50%, -50%); z-index: 10;
                        }
                        @keyframes spin {
                            from { transform: rotate(0deg); }
                            to { transform: rotate(360deg); }
                        }
                    </style>
                    <div class="team-load-more-marker"></div>
                    <div class="team-infinite-loader">
                        <div class="pokeball-loader"></div>
                        <span>목록을 더 불러오고 있어요...</span>
                    </div>
                """, unsafe_allow_html=True)

                if st.button("더 보기", key="team_btn_load_more"):
                    st.session_state.team_pokemon_limit += 50
                    st.rerun()

                st.components.v1.html("""
                    <script>
                        function findAndClick() {
                            const buttons = window.parent.document.querySelectorAll('button');
                            for (const btn of buttons) {
                                if (btn.textContent.includes("더 보기")) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                        const observer = new IntersectionObserver((entries) => {
                            entries.forEach(entry => { if (entry.isIntersecting) findAndClick(); });
                        }, { threshold: 0.1 });
                        const interval = setInterval(() => {
                            const marker = window.parent.document.querySelector('.team-load-more-marker');
                            if (marker) { observer.observe(marker); clearInterval(interval); }
                        }, 500);
                    </script>
                """, height=0)

    with panel_col:
        render_team_side_panel(selected_pokemon, can_request)


if __name__ == "__main__":
    show_v2()
