import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

import streamlit as st

from .constants import GYM_NAME_MAP, LEADERS
from .pokemon import PokemonDB
from .utils import start_custom_battle
from .ui import get_trainer_image_base64

db = PokemonDB()

# ── 세션당 로스터 이미지 캐싱 (Neo4j 중복 쿼리 방지) ──
def _get_roster_image(pokemon_id: int) -> str:
    cache_key = f"roster_img_{pokemon_id}"
    if cache_key not in st.session_state:
        data = db.get_pokemon_data(pokemon_id)
        st.session_state[cache_key] = data["image_url"] if data else ""
    return st.session_state[cache_key]


def display_menu():
    # ── 헤더 ──
    st.markdown(
        """
        <div class="battle-header" style="text-align:center; padding:32px 0 28px;">
            <h1>포켓몬 배틀 아레나</h1>
            <p>관장을 선택하고, 팀을 구성한 뒤 배틀에 도전하세요!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 체육관 / 관장 매핑 ──
    gym_options = list(GYM_NAME_MAP.values())
    GYM_TO_LEADER = {v: k for k, v in GYM_NAME_MAP.items()}

    current_leader = st.session_state.get("selected_leader", "웅이")
    current_gym = GYM_NAME_MAP.get(current_leader, gym_options[0])
    default_idx = gym_options.index(current_gym) if current_gym in gym_options else 0

    # ── 2-column: 왼쪽(선택+로스터+버튼) | 오른쪽(관장 포트레이트) ──
    left_col, right_col = st.columns([3, 2], gap="large")

    with left_col:
        # 관장 선택 섹션
        st.markdown('<div class="battle-section-title">관장 선택</div>', unsafe_allow_html=True)
        selected_gym = st.selectbox(
            "대결할 체육관을 선택하세요",
            options=gym_options,
            index=default_idx,
            label_visibility="collapsed",
        )
        selected_leader = GYM_TO_LEADER[selected_gym]
        st.session_state.selected_leader = selected_leader

        # 관장 로스터 (캐싱으로 빠르게 로드)
        leader_roster = LEADERS[selected_leader]["roster"]
        if leader_roster:
            roster_cards = ""
            for p in leader_roster:
                img_url = _get_roster_image(p["id"])
                roster_cards += (
                    f'<div class="gym-roster-card">'
                    f'<img src="{img_url}" alt="{p["name"]}">'
                    f'<div class="gym-roster-name">{p["name"]}</div>'
                    f'</div>'
                )
            st.markdown(
                f'<div style="color:rgba(203,213,225,0.72); font-size:0.8rem; font-weight:700; '
                f'text-transform:uppercase; letter-spacing:1px; margin:14px 0 8px;">'
                f'{selected_leader} 의 엔트리</div>'
                f'<div class="gym-roster-wrap">{roster_cards}</div>',
                unsafe_allow_html=True,
            )

        # 액션 버튼
        st.markdown('<div class="battle-divider"></div>', unsafe_allow_html=True)
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("🛠️ 팀 구성하기", use_container_width=True, type="primary"):
                user = st.session_state.get("user")
                if user and user.get("db_id"):
                    try:
                        resp = requests.get(
                            f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", timeout=3
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data and "team_data" in data:
                                st.session_state.player_team = data["team_data"]
                    except Exception:
                        pass
                st.session_state.battle_stage = "teambuilding"
                st.rerun()
        with btn2:
            if st.button("⚔️ 저장된 팀으로 배틀", use_container_width=True, type="secondary"):
                user = st.session_state.get("user")
                if user and user.get("db_id"):
                    try:
                        resp = requests.get(
                            f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team", timeout=3
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data and "team_data" in data and data["team_data"]:
                                st.session_state.player_team = data["team_data"]
                            else:
                                st.warning("저장된 팀이 없습니다. '팀 구성하기'를 먼저 해주세요.")
                                return
                        else:
                            st.warning("저장된 팀을 불러올 수 없습니다.")
                            return
                    except Exception as e:
                        st.error(f"서버와 통신할 수 없습니다: {e}")
                        return

                if len(st.session_state.player_team) > 0:
                    success = start_custom_battle(
                        st.session_state.player_team,
                        leader_name=st.session_state.selected_leader,
                    )
                    if success:
                        st.session_state.battle_stage = "battle"
                        st.rerun()
                else:
                    st.warning("자신의 포켓몬을 먼저 선택해주세요!")

    with right_col:
        # 관장 포트레이트 + 정보 카드
        trainer_img = get_trainer_image_base64(selected_leader)
        quote = LEADERS[selected_leader]["quotes"]["start"]
        if trainer_img:
            st.markdown(
                f'<div class="leader-info-card">'
                f'<img src="{trainer_img}" class="leader-portrait-big" alt="{selected_leader}">'
                f'<div class="leader-name-big">{selected_leader}</div>'
                f'<div class="leader-gym-name">{selected_gym}</div>'
                f'<div class="leader-quote-text">"{quote}"</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="leader-info-card">'
                f'<div style="font-size:4rem; margin:20px 0;">🏆</div>'
                f'<div class="leader-name-big">{selected_leader}</div>'
                f'<div class="leader-gym-name">{selected_gym}</div>'
                f'<div class="leader-quote-text">"{quote}"</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
