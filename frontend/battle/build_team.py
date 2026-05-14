import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

import streamlit as st

from .pokemon import PokemonDB
from .utils import start_custom_battle, BattlePokemon
from .ui import render_pokemon_status

db = PokemonDB()

def display_builder():
    st.markdown(
            """
            <div class="battle-header">
                <h1>포켓몬 검색 및 팀 구성</h1>
                <p>원하는 포켓몬을 검색하고, 4가지 기술을 선택하여 배틀을 준비하세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
    )
        
    pokemon_list = db.get_all_pokemon_names()
    pokemon_options = {p['name']: p['id'] for p in pokemon_list}
    
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("<hr>", unsafe_allow_html=True)
        if "selected_leader" not in st.session_state:
            st.session_state.selected_leader = "웅이"
        st.info(f"현재 선택된 상대: **{st.session_state.selected_leader}**")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("포켓몬 선택")
        selected_name = st.selectbox(
            "포켓몬 이름을 검색하세요",
            options=list(pokemon_options.keys()),
            index=None,                placeholder="포켓몬 이름 입력..."
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        if selected_name:
            pokemon_id = pokemon_options[selected_name]
            if "selected_pokemon_data" not in st.session_state or st.session_state.get("last_selected_id") != pokemon_id:
                st.session_state.selected_pokemon_data = db.get_pokemon_data(pokemon_id)
                st.session_state.last_selected_id = pokemon_id
                st.session_state.selected_moves = []

            pokemon_data = st.session_state.selected_pokemon_data
            preview = BattlePokemon(
                id=pokemon_data['id'], name=pokemon_data['name'], selected_moves=st.session_state.selected_moves
            )
            render_pokemon_status("PLAYER PREVIEW", preview, show_moves=False)

    with col2:
        st.subheader(f"내 파티 ({len(st.session_state.player_team)}/3)")
        if st.session_state.player_team:
            team_cols = st.columns(len(st.session_state.player_team))
            for i, pt in enumerate(st.session_state.player_team):
                pokemon_data = db.get_pokemon_data(pt['id'])
                with team_cols[i]:
                    img_url = pokemon_data['image_url']
                    st.image(img_url, use_container_width=True)
                    st.markdown(f"<div style='text-align: center; font-size: 0.8rem; margin-bottom: 8px;'>{pt['name']}</div>", unsafe_allow_html=True)
                    if st.button("❌ 제외", key=f"remove_pt_{i}_{pt['name']}", use_container_width=True):
                        st.session_state.player_team.pop(i)
                        st.rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)

        if selected_name:
            st.subheader("기술 선택")
            pokemon_data = st.session_state.selected_pokemon_data
            if "selected_moves" not in st.session_state:
                st.session_state.selected_moves = []
            
            selected_move_names = st.session_state.selected_moves
            
            st.write(f"**선택된 기술 ({len(selected_move_names)}/4)**")
            if selected_move_names:
                cols = st.columns(4)
                for i in range(4):
                    if i < len(selected_move_names):
                        cols[i].info(selected_move_names[i])
                    else:
                        cols[i].write("Empty")
            
            st.write("---")
            move_cols = st.columns(4)
            for i, move in enumerate(pokemon_data['moves']):
                m_name = move['name']
                is_selected = m_name in selected_move_names
                b_type = "primary" if is_selected else "secondary"
                if move_cols[i % 4].button(m_name, key=f"mv_{m_name}", use_container_width=True, type=b_type):
                    if is_selected:
                        st.session_state.selected_moves.remove(m_name)
                    elif len(st.session_state.selected_moves) < 4:
                        st.session_state.selected_moves.append(m_name)
                    st.rerun()

            st.write("---")
            if len(selected_move_names) == 4:
                st.success("모든 기술 선택 완료!")
                if len(st.session_state.player_team) < 3:
                    if st.button("➕ 엔트리에 추가하기", use_container_width=True, type="secondary"):
                        four_moves = [m for m in pokemon_data['moves'] if m['name'] in selected_move_names]
                        player_custom = {"id": pokemon_data['id'], "name": pokemon_data['name'], "moves": four_moves}
                        st.session_state.player_team.append(player_custom)
                        st.session_state.selected_moves = []
                        st.session_state.last_selected_id = None
                        st.rerun()
                else:
                    st.warning("파티가 가득 찼습니다! (최대 3마리)")
            else:
                st.info(f"기술을 {4 - len(selected_move_names)}개 더 선택해주세요.")

    with col2:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("현재 나의 엔트리")
        if not st.session_state.player_team:
            st.info("선택된 포켓몬이 없습니다. 왼쪽에서 검색하여 추가해주세요.")
        else:
            party_cols = st.columns(3)
            for idx, p in enumerate(st.session_state.player_team):
                with party_cols[idx]:
                    p_data = db.get_pokemon_data(p['id'])
                    st.image(p_data['image_url'], use_container_width=True)
                    st.markdown(f"<div style='text-align: center; font-weight: bold;'>{p['name']}</div>", unsafe_allow_html=True)
                    moves_text = ", ".join([m['name'] for m in p['moves']])
                    st.caption(f"기술: {moves_text}")
            
            if st.button("🗑️ 엔트리 전체 비우기", use_container_width=True):
                st.session_state.player_team = []
                st.rerun()

        if len(st.session_state.player_team) > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 포켓몬 선택 완료 및 배틀로 이동", use_container_width=True, type="primary"):
                user = st.session_state.get("user")
                if user and user.get("db_id"):
                    try:
                        payload = {"team_data": st.session_state.player_team}
                        resp = requests.post(f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", json=payload, timeout=3)
                        if resp.status_code == 200:
                            st.success("팀이 성공적으로 저장되었습니다!")
                        else:
                            st.warning("팀 저장에 실패했습니다.")
                    except Exception as e:
                        st.warning(f"팀을 저장하는 중 오류가 발생했습니다: {e}")
                
                if start_custom_battle(st.session_state.player_team, leader_name=st.session_state.selected_leader):
                    st.session_state.battle_stage = "battle"
                    st.rerun()
            
            if st.button("⬅️ 메뉴로 돌아가기", use_container_width=True):
                st.session_state.battle_stage = "menu"
                st.rerun()