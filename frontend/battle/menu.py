import os
import requests
BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

import streamlit as st

from .constants import GYM_NAME_MAP, LEADERS
from .pokemon import PokemonDB
from .utils import start_custom_battle

db = PokemonDB()

def display_menu():
    st.markdown(
            """
            <div class="battle-header" style="text-align:center; padding: 40px 0;">
                <h1>포켓몬 배틀 아레나</h1>
                <p>나만의 팀을 구성하거나 즉시 배틀을 시작하세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    st.subheader("관장 선택")
    # 체육관 이름을 선택지에 노출
    gym_options = list(GYM_NAME_MAP.values())
    # 역매핑 (체육관 이름 -> 관장 이름)
    GYM_TO_LEADER = {v: k for k, v in GYM_NAME_MAP.items()}
    
    # 현재 세션의 선택된 관장에 해당하는 체육관 이름 찾기
    current_leader = st.session_state.get("selected_leader", "웅이")
    current_gym = GYM_NAME_MAP.get(current_leader, gym_options[0])
    default_idx = gym_options.index(current_gym) if current_gym in gym_options else 0

    selected_gym = st.selectbox("대결할 체육관을 선택하세요", options=gym_options, index=default_idx)
    selected_leader = GYM_TO_LEADER[selected_gym]
    st.session_state.selected_leader = selected_leader
    
    leader_roster = LEADERS[selected_leader]["roster"]
    if leader_roster:
        st.caption(f"**{selected_leader}({selected_gym})의 엔트리:**")
        cols = st.columns(len(leader_roster))
        for idx, p in enumerate(leader_roster):
            pokemon_data = db.get_pokemon_data(p['id'])
            with cols[idx]:
                img_url = pokemon_data['image_url']
                st.image(img_url, use_container_width=True)
                st.markdown(f"<div style='text-align: center; font-size: 0.85rem; font-weight: 700; color: #cbd5e1;'>{p['name']}</div>", unsafe_allow_html=True)
                
    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛠️ 팀 구성하기", use_container_width=True, type="primary"):
            user = st.session_state.get("user")
            if user and user.get("db_id"):
                try:
                    resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and "team_data" in data:
                            st.session_state.player_team = data["team_data"]
                except:
                    pass # 불러오기 실패해도 빈 팀으로 시작
            st.session_state.battle_stage = "teambuilding"
            st.rerun()
    with col2:
        if st.button("⚔️ 배틀 시작하기", use_container_width=True, type="secondary"):
            user = st.session_state.get("user")
            if user and user.get("db_id"):
                try:
                    resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and "team_data" in data and data["team_data"]:
                            st.session_state.player_team = data["team_data"]
                        else:
                            st.warning("저장된 팀이 없습니다. '팀 구성하기'를 통해 팀을 먼저 구성해주세요.")
                            return
                    else:
                        st.warning("저장된 팀을 불러올 수 없습니다. 팀을 먼저 구성해주세요.")
                        return
                except Exception as e:
                    st.error(f"서버와 통신할 수 없습니다: {e}")
                    return
            
            if len(st.session_state.player_team) > 0:
                success = start_custom_battle(st.session_state.player_team, leader_name=st.session_state.selected_leader)
                if success:
                    st.session_state.battle_stage = "battle"
                    st.rerun()
            else:
                st.warning("자신의 포켓몬을 선택해주세요!")