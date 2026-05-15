import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

import streamlit as st

from .utils import BattlePokemon, start_custom_battle, get_pokemon_data, get_all_pokemon_names
from .ui import render_pokemon_status

def display_builder():
    selected_leader = st.session_state.get("selected_leader", "웅이")

    # ── 헤더 ──
    st.markdown(
        f"""
        <div class="battle-header">
            <h1>팀 구성</h1>
            <p>포켓몬을 고르고, 4가지 기술을 선택해 파티를 완성하세요.&nbsp;
            <span style="color:rgba(56,189,248,0.9); font-weight:900;">상대: {selected_leader}</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
        
    pokemon_list = get_all_pokemon_names()
    pokemon_options = {p['name']: p['id'] for p in pokemon_list}
    
    col1, col2 = st.columns([1, 1.2])

    # ── STEP 1: 포켓몬 선택 ──
    with col1:
        st.markdown(
            '<div class="battle-section-title" style="font-size:0.95rem;">STEP 1 &nbsp;—&nbsp; 포켓몬 선택</div>',
            unsafe_allow_html=True,
        )
        selected_name = st.selectbox(
            "포켓몬 검색",
            options=list(pokemon_options.keys()),
            index=None,
            placeholder="이름을 입력하세요...",
            label_visibility="collapsed",
        )

        st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)

        if selected_name:
            pokemon_id = pokemon_options[selected_name]
            if "selected_pokemon_data" not in st.session_state or st.session_state.get("last_selected_id") != pokemon_id:
                st.session_state.selected_pokemon_data = get_pokemon_data(pokemon_id)
                st.session_state.last_selected_id = pokemon_id
                st.session_state.selected_moves = []

            pokemon_data = st.session_state.selected_pokemon_data
            preview = BattlePokemon(
                id=pokemon_data["id"],
                name=pokemon_data["name"],
                selected_moves=st.session_state.selected_moves,
            )
            render_pokemon_status("PREVIEW", preview, show_moves=False)
        else:
            st.markdown(
                '<div class="search-placeholder-card">'
                '<div class="placeholder-icon">🔍</div>'
                '<div class="placeholder-text">포켓몬을 검색하면<br>프리뷰가 표시됩니다</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ── STEP 2: 기술 선택 ──
    with col2:
        st.subheader(f"내 파티 ({len(st.session_state.player_team)}/3)")
        if st.session_state.player_team:
            team_cols = st.columns(len(st.session_state.player_team))
            for i, pt in enumerate(st.session_state.player_team):
                pokemon_data = get_pokemon_data(pt['id'])
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
            selected_move_names = st.session_state.selected_moves

            # 선택 현황 뱃지
            badges = ""
            for j in range(4):
                if j < len(selected_move_names):
                    badges += f'<span class="move-selected-badge">✓ {selected_move_names[j]}</span> '
                else:
                    badges += f'<span class="move-empty-badge">슬롯 {j + 1}</span> '
            st.markdown(
                f'<div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px;">{badges}</div>',
                unsafe_allow_html=True,
            )

            # 기술 버튼 — 2컬럼 그리드 (넓은 버튼)
            mv_col1, mv_col2 = st.columns(2)
            for i, move in enumerate(pokemon_data["moves"]):
                m_name = move["name"]
                is_selected = m_name in selected_move_names
                target_col = mv_col1 if i % 2 == 0 else mv_col2
                with target_col:
                    btn_type = "primary" if is_selected else "secondary"
                    if st.button(
                        f"{'✓ ' if is_selected else ''}{m_name}",
                        key=f"mv_{m_name}",
                        use_container_width=True,
                        type=btn_type,
                    ):
                        if is_selected:
                            st.session_state.selected_moves.remove(m_name)
                        elif len(st.session_state.selected_moves) < 4:
                            st.session_state.selected_moves.append(m_name)
                        st.rerun()

            # 4개 완성 → 파티 추가 버튼
            if len(selected_move_names) == 4:
                st.markdown('<div class="battle-divider"></div>', unsafe_allow_html=True)
                if len(party) < 3:
                    if st.button(
                        "➕ 파티에 추가",
                        use_container_width=True,
                        type="primary",
                        key="add_to_party",
                    ):
                        four_moves = [m for m in pokemon_data["moves"] if m["name"] in selected_move_names]
                        st.session_state.player_team.append(
                            {"id": pokemon_data["id"], "name": pokemon_data["name"], "moves": four_moves}
                        )
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
                    p_data = get_pokemon_data(p['id'])
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
                        resp = requests.post(
                            f"{BACKEND_URL}/api/v1/users/{user['db_id']}/battle-team",
                            json=payload,
                            timeout=3,
                        )
                        if resp.status_code == 200:
                            st.toast("팀이 저장되었습니다!", icon="💾")
                        else:
                            st.warning("팀 저장에 실패했습니다.")
                    except Exception as e:
                        st.warning(f"팀 저장 중 오류: {e}")

                if start_custom_battle(st.session_state.player_team, leader_name=selected_leader):
                    st.session_state.battle_stage = "battle"
                    st.rerun()
        else:
            st.markdown(
                '<div style="color:#000000; font-size:0.82rem; font-weight:700; '
                'text-align:center; padding:10px;">파티에 포켓몬을 추가하면 배틀을 시작할 수 있습니다</div>',
                unsafe_allow_html=True,
            )
