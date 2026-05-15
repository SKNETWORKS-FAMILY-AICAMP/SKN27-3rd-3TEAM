import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("BACKEND_API_URL") or "http://localhost:8000"

import streamlit as st

from .pokemon import PokemonDB
from .utils import start_custom_battle, BattlePokemon
from .ui import render_pokemon_status

db = PokemonDB()


# ── 세션당 DB 캐싱 헬퍼 (재렌더링마다 Neo4j 쿼리 방지) ──
def _all_pokemon_names():
    if "pokemon_names_cache" not in st.session_state:
        st.session_state.pokemon_names_cache = db.get_all_pokemon_names()
    return st.session_state.pokemon_names_cache


def _pokemon_data(pokemon_id: int):
    key = f"pdata_{pokemon_id}"
    if key not in st.session_state:
        st.session_state[key] = db.get_pokemon_data(pokemon_id)
    return st.session_state[key]


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

    if "selected_moves" not in st.session_state:
        st.session_state.selected_moves = []

    pokemon_list = _all_pokemon_names()
    pokemon_options = {p["name"]: p["id"] for p in pokemon_list}

    # ════════════════════════════════
    #  TOP: 현재 파티 (항상 표시)
    # ════════════════════════════════
    party = st.session_state.player_team
    st.markdown(
        f'<div class="battle-section-title">현재 파티 '
        f'<span style="opacity:0.5; font-size:0.88em;">({len(party)}/3)</span></div>',
        unsafe_allow_html=True,
    )

    p_col1, p_col2, p_col3 = st.columns(3)
    for slot_idx, slot_col in enumerate([p_col1, p_col2, p_col3]):
        with slot_col:
            if slot_idx < len(party):
                pt = party[slot_idx]
                p_data = _pokemon_data(pt["id"])
                img_url = p_data["image_url"] if p_data else ""
                moves_txt = " / ".join(m["name"] for m in pt["moves"])
                st.image(img_url, use_container_width=True)
                st.markdown(
                    f"<div style='text-align:center; font-weight:900; color:#f8fafc; "
                    f"font-size:0.9rem; margin-bottom:2px;'>{pt['name']}</div>"
                    f"<div style='text-align:center; font-size:0.7rem; color:rgba(148,163,184,0.8); "
                    f"margin-bottom:6px;'>{moves_txt}</div>",
                    unsafe_allow_html=True,
                )
                if st.button("× 제외", key=f"rm_{slot_idx}_{pt['name']}", use_container_width=True):
                    st.session_state.player_team.pop(slot_idx)
                    st.rerun()
            else:
                st.markdown(
                    f'<div class="party-slot-empty">'
                    f'<div style="font-size:1.8rem; opacity:0.4;">＋</div>'
                    f'<div>슬롯 {slot_idx + 1}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="battle-divider"></div>', unsafe_allow_html=True)

    # ════════════════════════════════
    #  MAIN: 왼쪽(STEP1 검색+프리뷰) | 오른쪽(STEP2 기술 선택)
    # ════════════════════════════════
    col1, col2 = st.columns([2, 3], gap="large")

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
            # 새 포켓몬 선택 시 기존 기술 초기화
            if st.session_state.get("last_selected_id") != pokemon_id:
                st.session_state.selected_pokemon_data = _pokemon_data(pokemon_id)
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
        st.markdown(
            '<div class="battle-section-title" style="font-size:0.95rem;">STEP 2 &nbsp;—&nbsp; 기술 선택 (4개)</div>',
            unsafe_allow_html=True,
        )

        if selected_name and st.session_state.get("selected_pokemon_data"):
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
            st.markdown(
                '<div class="search-placeholder-card">'
                '<div class="placeholder-icon">⚔️</div>'
                '<div class="placeholder-text">왼쪽에서 포켓몬을 선택하면<br>기술 목록이 나타납니다</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ════════════════════════════════
    #  BOTTOM: 네비게이션 버튼
    # ════════════════════════════════
    st.markdown('<div class="battle-divider"></div>', unsafe_allow_html=True)

    nav1, nav2, nav3 = st.columns([1, 1, 2])
    with nav1:
        if st.button("⬅️ 메뉴로", use_container_width=True):
            st.session_state.battle_stage = "menu"
            st.rerun()
    with nav2:
        if st.button("🗑️ 파티 초기화", use_container_width=True):
            st.session_state.player_team = []
            st.rerun()
    with nav3:
        if len(party) > 0:
            if st.button("💾 팀 저장 후 배틀 시작  ▶", use_container_width=True, type="primary"):
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
