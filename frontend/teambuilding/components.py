from __future__ import annotations

import os
from html import escape
from typing import Any, Dict, List

import streamlit as st

from .constants import REQUIRED_TEAM_SIZE, TEAM_FILTER_TYPES, TEAM_FILTER_REGIONS, TYPE_BADGE_STYLES
from .filters import (
    ensure_team_filter_state,
    apply_team_search,
    reset_team_filters,
    select_team_region,
    toggle_team_type,
    get_available_abilities,
)
from .api import request_json


# ── Type badge helpers ────────────────────────────────────────────────────

def get_type_badge_style(type_name: str) -> str:
    palette = TYPE_BADGE_STYLES.get(
        type_name, {"bg": "#E5E7EB", "border": "#9CA3AF", "text": "#374151"}
    )
    return (
        f"background: {palette['bg']}; "
        f"border-color: {palette['border']}; "
        f"color: {palette['text']};"
    )


def build_type_badges(type_names: List[str]) -> str:
    badges = [
        f"<span class='type-badge' style='{get_type_badge_style(t)}'>{escape(t)}</span>"
        for t in type_names
    ]
    return "".join(badges) if badges else "<span class='type-placeholder'>타입 정보 없음</span>"


def normalize_html(html: str) -> str:
    return "\n".join(line.lstrip() for line in html.splitlines())


# ── Pokemon selection ─────────────────────────────────────────────────────

def toggle_pokemon(pokemon_id: int) -> None:
    selected_ids: List[int] = st.session_state.selected_pokemon_ids
    if pokemon_id in selected_ids:
        selected_ids.remove(pokemon_id)
        st.session_state.analysis_result = None
        st.session_state.recommendation_result = None
        return
    if len(selected_ids) >= REQUIRED_TEAM_SIZE:
        st.warning("포켓몬은 5마리까지만 선택할 수 있어요.")
        return
    selected_ids.append(pokemon_id)
    st.session_state.analysis_result = None
    st.session_state.recommendation_result = None


def render_pokemon_card(pokemon: Dict[str, Any]) -> None:
    is_selected = pokemon["pokemon_id"] in st.session_state.selected_pokemon_ids
    card_class = "pokemon-card team-picker-card selected-card" if is_selected else "pokemon-card team-picker-card"

    if pokemon["types"]:
        type_badges = "".join(
            f"<span class='type-badge' style='{get_type_badge_style(t)}'>{escape(t)}</span>"
            for t in pokemon["types"]
        )
    else:
        type_badges = "<span class='type-placeholder'>타입 분석 후 확인</span>"

    if pokemon["image_url"]:
        image_html = (
            f"<img class='pokemon-card-image' src='{escape(pokemon['image_url'])}' "
            f"alt='{escape(pokemon['name'])}'>"
        )
    else:
        image_html = "<div class='missing-image'>No Image</div>"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="pokemon-card-marker"></div>
            <div class="pokemon-image-wrapper">{image_html}</div>
            <div class="pokemon-info">
                <div class="pokemon-id-badge">No.{pokemon["pokemon_id"]:04d}</div>
                <div class="pokemon-card-title">{escape(pokemon["name"])}</div>
                <div class="pokemon-type-row">{type_badges}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 투명 버튼 렌더링 (styles.py의 CSS에 의해 카드 전체를 덮게 됨)
    st.button(
        "선택", 
        key=f"toggle_{pokemon['pokemon_id']}",
        on_click=toggle_pokemon,
        args=(pokemon["pokemon_id"],),
        use_container_width=True,
    )


# ── Filter panel ──────────────────────────────────────────────────────────

_TEAM_ICON_FILENAME_OVERRIDE = {"얼음": "아이스"}


@st.cache_data(show_spinner=False)
def load_team_type_icons() -> dict:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_dir = os.path.join(base_path, "img", "type")
    icons: dict = {}
    for ko, _ in TEAM_FILTER_TYPES:
        filename = _TEAM_ICON_FILENAME_OVERRIDE.get(ko, ko)
        path = os.path.join(icon_dir, f"{filename}.svg")
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    icons[ko] = f.read()
            else:
                icons[ko] = ""
        except Exception:
            icons[ko] = ""
    return icons


def render_team_filter_panel(pokemon_list: List[Dict[str, Any]]) -> None:
    ensure_team_filter_state()
    ability_options = get_available_abilities(pokemon_list)
    if st.session_state.get("team_input_ability", "전체") not in ability_options:
        st.session_state.team_input_ability = "전체"
    if st.session_state.get("team_applied_ability", "전체") not in ability_options:
        st.session_state.team_applied_ability = "전체"

    with st.container(border=True):
        st.markdown('<div class="team-filter-panel-marker"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="team-filter-title">
                <img src="https://pokemonkorea.co.kr/img/_con.ico" class="team-filter-title-icon">
                <span>Team Builder</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        search_col, dex_col = st.columns([1, 1])
        with search_col:
            st.text_input(
                "검색",
                key="team_input_keyword",
                placeholder="포켓몬 이름 또는 번호를 입력하세요.",
                value=st.session_state.get("team_input_keyword", ""),
            )
        with dex_col:
            st.slider("도감번호", min_value=1, max_value=1025, key="team_filter_dex_range")

        left_col, right_col = st.columns([1, 1.7])
        with left_col:
            cur_ability = st.session_state.get("team_input_ability", "전체")
            ability_index = ability_options.index(cur_ability) if cur_ability in ability_options else 0
            st.selectbox("특성", ability_options, index=ability_index, key="team_input_ability")

            st.markdown('<div class="team-filter-label">지방</div>', unsafe_allow_html=True)
            region_names = list(TEAM_FILTER_REGIONS.keys())
            for region_row in (region_names[:5], region_names[5:]):
                region_cols = st.columns(len(region_row))
                for region_col, region_name in zip(region_cols, region_row):
                    with region_col:
                        active = "region-active" if st.session_state.team_filter_region == region_name else ""
                        st.markdown(
                            f'<div class="team-region-button {active}">{escape(region_name)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.button(
                            "",
                            key=f"team_region_{region_name}",
                            on_click=select_team_region,
                            args=(region_name,),
                            use_container_width=True,
                        )

        type_icons = load_team_type_icons()
        with right_col:
            st.markdown('<div class="team-filter-label">타입</div>', unsafe_allow_html=True)
            for type_row in (
                TEAM_FILTER_TYPES[:6],
                TEAM_FILTER_TYPES[6:12],
                TEAM_FILTER_TYPES[12:18],
            ):
                type_cols = st.columns(len(type_row))
                for type_col, (type_name, type_key) in zip(type_cols, type_row):
                    with type_col:
                        active = "type-active" if type_name in st.session_state.team_filter_types else ""
                        svg = type_icons.get(type_name, "")
                        icon_html = f'<div class="type-svg-wrap">{svg}</div>' if svg else ""
                        st.markdown(
                            f'<div class="team-type-button type-bg-{type_key} {active}">'
                            f'{icon_html}<span>{escape(type_name)}</span></div>',
                            unsafe_allow_html=True,
                        )
                        st.button(
                            "",
                            key=f"team_type_{type_key}",
                            on_click=toggle_team_type,
                            args=(type_name,),
                            use_container_width=True,
                        )

        _, search_col, reset_col, _ = st.columns([2, 2, 2, 2])
        with search_col:
            st.markdown('<div class="team-filter-search-button"></div>', unsafe_allow_html=True)
            if st.button("검색", key="team_filter_search_action", use_container_width=True):
                apply_team_search()
                st.rerun()
        with reset_col:
            st.markdown('<div class="team-filter-reset-button"></div>', unsafe_allow_html=True)
            st.button(
                "초기화",
                key="team_filter_reset_action",
                on_click=reset_team_filters,
                use_container_width=True,
            )


# ── Analysis & recommendation rendering ──────────────────────────────────

def render_team_insights(insights: Dict[str, Any]) -> None:
    if not insights:
        return

    summary = insights.get("summary", "아직 덱 총평을 만들 수 없습니다.")
    team_identity = insights.get("team_identity", "팀 성격 미확인")
    recommendation_direction = insights.get("recommendation_direction", "")

    st.markdown(
        f"""
        <div class="analysis-summary-card">
            <div class="analysis-kicker">덱 총평</div>
            <div class="analysis-title">{escape(team_identity)}</div>
            <div class="analysis-summary-text">{escape(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    risk_col, strength_col, direction_col = st.columns(3)
    with risk_col:
        st.markdown("**핵심 위험**")
        for item in insights.get("risk_summary", [])[:3]:
            severity = item.get("severity", "medium")
            st.markdown(
                f"""
                <div class="insight-card risk-{escape(severity)}">
                    <div class="insight-card-title">{escape(item.get("title", "위험 요소"))}</div>
                    <div class="insight-card-text">{escape(item.get("detail", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with strength_col:
        st.markdown("**팀 강점**")
        for item in insights.get("strength_summary", [])[:3]:
            st.markdown(
                f"""
                <div class="insight-card strength-card">
                    <div class="insight-card-title">{escape(item.get("title", "강점"))}</div>
                    <div class="insight-card-text">{escape(item.get("detail", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with direction_col:
        st.markdown("**6번째 추천 방향**")
        st.markdown(
            f"""
            <div class="insight-card direction-card">
                <div class="insight-card-title">보완 방향</div>
                <div class="insight-card-text">{escape(recommendation_direction)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        type_balance = insights.get("type_balance", [])
        if type_balance:
            balance_badges = "".join(
                f"<span class='type-badge' style='{get_type_badge_style(item['type_name'])}'>"
                f"{escape(item['type_name'])} {item['count']}</span>"
                for item in type_balance[:6]
            )
            st.markdown(
                f"<div class='analysis-type-balance'>{balance_badges}</div>",
                unsafe_allow_html=True,
            )

    role_summary = insights.get("role_summary", [])
    if role_summary:
        with st.expander("선택한 포켓몬 역할 해석"):
            for p in role_summary:
                st.write(f"- {p['name']} | {p['role']} | {p['detail']}")


def render_rag_final_answer(result: Dict[str, Any]) -> None:
    final_answer = result.get("final_answer")
    if not final_answer:
        return

    paragraphs = [p.strip() for p in str(final_answer).split("\n\n") if p.strip()]
    if not paragraphs:
        return

    conclusion_html = escape(paragraphs[0]).replace(chr(10), "<br>")
    detail_html = "".join(
        f"<p>{escape(p).replace(chr(10), '<br>')}</p>"
        for p in paragraphs[1:]
    )

    st.markdown(
        f"""
        <div class="rag-answer-card">
            <div class="rag-answer-kicker">AI 종합 해설</div>
            <div class="rag-answer-conclusion">{conclusion_html}</div>
            <div class="rag-answer-text">{detail_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_selected_team_cards(selected: List[Dict[str, Any]]) -> None:
    if not selected:
        return

    cards = []
    for p in selected:
        type_names = [t.get("type_name", "") for t in p.get("types", []) if t.get("type_name")]
        image_url = p.get("image_url") or (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
            f"sprites/pokemon/other/official-artwork/{p.get('pokemon_id')}.png"
        )
        image_html = (
            f"<img class='analysis-team-image' src='{escape(image_url)}' "
            f"alt='{escape(p.get('name', ''))}' />"
            if image_url
            else "<div class='analysis-team-image-empty'>?</div>"
        )
        cards.append(
            normalize_html(
                f"""
                <div class="analysis-team-card">
                    <div class="analysis-team-image-wrap">{image_html}</div>
                    <div class="analysis-team-name">#{p.get('pokemon_id', 0):04d} {escape(p.get('name', ''))}</div>
                    <div class="analysis-team-types">{build_type_badges(type_names)}</div>
                </div>
                """
            )
        )

    st.markdown(
        normalize_html(
            f"""
            <div class="analysis-section-header">선택한 포켓몬</div>
            <div class="analysis-team-grid">{''.join(cards)}</div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_analysis_detail_cards(
    weaknesses: List[Dict[str, Any]],
    resistances: List[Dict[str, Any]],
    move_coverage: List[Dict[str, Any]],
) -> None:
    def matchup_rows(items: List[Dict[str, Any]], label: str) -> str:
        if not items:
            return "<div class='analysis-empty-row'>아직 계산된 정보가 부족해요.</div>"
        rows = []
        for item in items[:6]:
            type_name = item.get("type_name", "")
            score = item.get("score", 0)
            avg = item.get("average_multiplier", 0)
            rows.append(normalize_html(f"""
                <div class="analysis-metric-row">
                    <div class="analysis-metric-left">{build_type_badges([type_name])}</div>
                    <div class="analysis-metric-right">
                        <strong>{label} {score}점</strong>
                        <span>평균 {float(avg):.2f}배</span>
                    </div>
                </div>
            """))
        return "".join(rows)

    def coverage_rows(items: List[Dict[str, Any]]) -> str:
        if not items:
            return "<div class='analysis-empty-row'>기술 타입 정보가 아직 부족해요.</div>"
        max_count = max((i.get("move_count", 0) for i in items[:6]), default=1)
        rows = []
        for item in items[:6]:
            type_name = item.get("type_name", "")
            cnt = item.get("move_count", 0)
            width = int((cnt / max_count) * 100) if max_count else 0
            rows.append(normalize_html(f"""
                <div class="coverage-row">
                    <div class="coverage-row-top">
                        {build_type_badges([type_name])}<strong>{cnt}개</strong>
                    </div>
                    <div class="coverage-bar">
                        <div class="coverage-bar-fill" style="width:{width}%"></div>
                    </div>
                </div>
            """))
        return "".join(rows)

    st.markdown(
        normalize_html(f"""
            <div class="analysis-detail-grid">
                <div class="analysis-detail-card danger-panel">
                    <div class="analysis-detail-title">주의할 약점 타입</div>
                    <div class="analysis-detail-caption">상대가 이 타입 기술을 들고 오면 교체와 선봉 선택을 조심해야 해요.</div>
                    {matchup_rows(weaknesses, "위험")}
                </div>
                <div class="analysis-detail-card safe-panel">
                    <div class="analysis-detail-title">방어가 좋은 타입</div>
                    <div class="analysis-detail-caption">이 타입 공격은 비교적 안정적으로 받아낼 가능성이 높아요.</div>
                    {matchup_rows(resistances, "안정")}
                </div>
                <div class="analysis-detail-card coverage-panel">
                    <div class="analysis-detail-title">기술 타입 커버리지</div>
                    <div class="analysis-detail-caption">현재 팀이 어떤 공격 타입을 많이 확보했는지 보여줍니다.</div>
                    {coverage_rows(move_coverage)}
                </div>
            </div>
        """),
        unsafe_allow_html=True,
    )


def render_recommendation_cards(recommendations: List[Dict[str, Any]]) -> None:
    cards = []
    for idx, p in enumerate(recommendations[:3], start=1):
        rank = p.get("rank", idx)
        score = p.get("hybrid_score", p.get("score", 0))
        image_url = p.get("image_url") or (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
            f"sprites/pokemon/other/official-artwork/{p.get('pokemon_id')}.png"
        )
        reasons = p.get("reasons") or []
        reason_rows = "".join(f"<li>{escape(r)}</li>" for r in reasons[:4]) or (
            "<li>현재 팀의 약점을 보완할 수 있는 후보입니다.</li>"
        )
        raw_types = p.get("types", [])
        type_names = [
            t.get("type_name", t.get("name", "")) if isinstance(t, dict) else str(t)
            for t in raw_types
        ]
        image_html = (
            f"<img class='recommend-image' src='{escape(image_url)}' alt='{escape(p.get('name', ''))}' />"
            if image_url else "<div class='recommend-image-empty'>?</div>"
        )
        cards.append(normalize_html(f"""
            <div class="recommend-card rank-{rank}">
                <div class="recommend-rank">{rank}순위</div>
                <div class="recommend-image-wrap">{image_html}</div>
                <div class="recommend-name">#{p.get('pokemon_id', 0):04d} {escape(p.get('name', ''))}</div>
                <div class="recommend-types">{build_type_badges([n for n in type_names if n])}</div>
                <div class="recommend-score">추천 점수 <strong>{score}</strong></div>
                <ul class="recommend-reasons">{reason_rows}</ul>
            </div>
        """))

    st.markdown(
        normalize_html(f"<div class='recommend-grid'>{''.join(cards)}</div>"),
        unsafe_allow_html=True,
    )


def render_analysis_result(result: Dict[str, Any]) -> None:
    st.subheader("포켓몬 덱 분석")
    analysis = result.get("graph_result", result)
    render_team_insights(analysis.get("insights", {}))
    render_rag_final_answer(result)
    render_selected_team_cards(analysis.get("selected_pokemon", []))

    weaknesses = sorted(
        analysis.get("weak_types", analysis.get("weaknesses", [])),
        key=lambda x: x.get("score", 0), reverse=True,
    )
    resistances = sorted(
        analysis.get("resistant_types", analysis.get("resistances", [])),
        key=lambda x: x.get("score", 0), reverse=True,
    )
    move_coverage = sorted(
        analysis.get("move_type_coverage", []),
        key=lambda x: x.get("move_count", 0), reverse=True,
    )
    render_analysis_detail_cards(weaknesses, resistances, move_coverage)


def render_recommendation_result(result: Dict[str, Any]) -> None:
    st.subheader("포켓몬 추천")
    rec = result.get("reranked_result", result.get("graph_result", result))
    render_rag_final_answer(result)
    recommendations = rec.get("recommendations", [])
    if not recommendations:
        st.info("추천 결과가 아직 없어요.")
        return
    render_recommendation_cards(recommendations)


# ── Team side panel ───────────────────────────────────────────────────────

def render_team_side_panel(
    selected_pokemon: List[Dict[str, Any]],
    can_request: bool,
) -> None:
    count = len(selected_pokemon)

    slot_cells = []
    for i in range(REQUIRED_TEAM_SIZE):
        if i < count:
            p = selected_pokemon[i]
            img = escape(p.get("image_url", ""))
            name = escape(p.get("name", ""))
            slot_cells.append(
                f'<div class="ts-slot filled">'
                f'<span class="ts-num">{i + 1}</span>'
                f'<img class="ts-img" src="{img}" alt="{name}">'
                f'<div class="ts-name">{name}</div>'
                f'</div>'
            )
        else:
            slot_cells.append(
                f'<div class="ts-slot">'
                f'<span class="ts-num">{i + 1}</span>'
                f'<div class="ts-empty-circle">＋</div>'
                f'<div class="ts-empty-text">대기</div>'
                f'</div>'
            )

    slot_cells.append(
        f'<div class="ts-slot ts-slot-locked">'
        f'<span class="ts-num">6</span>'
        f'<div class="ts-lock-circle">?</div>'
        f'<div class="ts-empty-text">자유석</div>'
        f'</div>'
    )

    if count == 0:
        hint, hint_color = "왼쪽에서 포켓몬을 선택하세요", "#555"
    elif count < REQUIRED_TEAM_SIZE:
        hint, hint_color = f"{REQUIRED_TEAM_SIZE - count}마리 더 선택하세요", "#888"
    else:
        hint, hint_color = "팀 분석을 시작하세요!", "#FFCB05"

    st.markdown(
        f"""
        <div class="ts-panel">
            <div class="ts-header">
                <img src="https://pokemonkorea.co.kr/img/_con.ico" class="ts-icon">
                <span class="ts-title">나의 팀</span>
                <span class="ts-badge">{count} / {REQUIRED_TEAM_SIZE}</span>
            </div>
            <div class="ts-grid">{"".join(slot_cells)}</div>
            <div class="ts-hint" style="color:{hint_color};">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="tb-act-reset">', unsafe_allow_html=True)
    
    # 초기화 확인 상태 확인
    if st.session_state.get("confirm_reset_team"):
        st.markdown("<div style='text-align:center; margin-bottom:5px; font-size:0.85rem; color:#ff4d4d; font-weight:bold;'>정말 초기화하시겠습니까?</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("예", key="reset_yes", use_container_width=True):
                st.session_state.selected_pokemon_ids = []
                st.session_state.analysis_result = None
                st.session_state.recommendation_result = None
                st.session_state.confirm_reset_team = False
                st.rerun()
        with c2:
            if st.button("아니오", key="reset_no", use_container_width=True):
                st.session_state.confirm_reset_team = False
                st.rerun()
    else:
        if st.button("선택 초기화", use_container_width=True, key="side_reset"):
            st.session_state.confirm_reset_team = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="tb-act-analyze">', unsafe_allow_html=True)
    if st.button("팀 분석 & 추천", use_container_width=True, disabled=not can_request, key="side_analyze"):
        ids = st.session_state.selected_pokemon_ids
        st.markdown(
            """
            <style>
            @keyframes tb-spin { to { transform: rotate(360deg); } }
            @keyframes tb-pulse-ring {
                0%   { transform: scale(0.8); opacity: 0.8; }
                100% { transform: scale(1.6); opacity: 0; }
            }
            .tb-overlay {
                position: fixed; inset: 0;
                background: rgba(5, 5, 15, 0.97);
                z-index: 999999;
                display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                gap: 26px;
            }
            .tb-ball-ring {
                position: relative;
                width: 120px; height: 120px;
                display: flex; align-items: center; justify-content: center;
            }
            .tb-ball-ring::before {
                content: '';
                position: absolute;
                width: 120px; height: 120px;
                border-radius: 50%;
                background: rgba(255, 203, 5, 0.18);
                animation: tb-pulse-ring 1.4s ease-out infinite;
            }
            .tb-ball {
                width: 90px; height: 90px;
                animation: tb-spin 1s linear infinite;
                filter: drop-shadow(0 0 18px rgba(255, 203, 5, 0.35));
                position: relative; z-index: 1;
            }
            .tb-loading-title {
                font-family: 'Outfit', sans-serif;
                font-size: 1.6rem; font-weight: 900;
                color: #ffffff; letter-spacing: 2px;
            }
            .tb-loading-sub {
                font-family: 'Inter', sans-serif;
                font-size: 0.92rem;
                color: rgba(255,255,255,0.35);
                margin-top: -14px;
            }
            </style>
            <div class="tb-overlay">
                <div class="tb-ball-ring">
                    <svg class="tb-ball" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="50" cy="50" r="45" fill="white" stroke="#333" stroke-width="2"/>
                        <path d="M5 50A45 45 0 0 1 95 50H70A20 20 0 0 0 30 50H5" fill="#E33535" stroke="#333" stroke-width="2"/>
                        <circle cx="50" cy="50" r="15" fill="white" stroke="#333" stroke-width="2"/>
                        <circle cx="50" cy="50" r="8" fill="white" stroke="#333" stroke-width="1"/>
                    </svg>
                </div>
                <div class="tb-loading-title">분석 중...</div>
                <div class="tb-loading-sub">팀 전력 분석 및 추천 포켓몬을 계산하고 있어요</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        from concurrent.futures import ThreadPoolExecutor

        # user_id는 메인 스레드에서 미리 캡처 (스레드 내 session_state 접근 불안정 방지)
        _uid = get_current_user_id()

        def _analyze() -> Any:
            payload: Dict[str, Any] = {"pokemon_ids": ids}
            if _uid is not None:
                payload["user_id"] = _uid
            return request_json("POST", "/api/v1/team-builder/rag-analyze", json=payload)

        def _recommend() -> Any:
            payload: Dict[str, Any] = {"pokemon_ids": ids, "limit": 3}
            if _uid is not None:
                payload["user_id"] = _uid
            return request_json("POST", "/api/v1/team-builder/rag-recommend", json=payload)

        # ThreadPoolExecutor를 제거하고 순차 실행합니다.
        # 이유:
        # 1. 백그라운드 스레드에서 st.session_state 접근 시 Streamlit Thread Context 예외가 발생하여 화면이 무한 로딩에 빠집니다.
        # 2. _recommend() 내부(api.py)에서 DB 저장을 위해 직전의 analysis_result를 필요로 하므로 _analyze()가 먼저 완료되어야 합니다.
        st.session_state.analysis_result = _analyze()
        st.session_state.recommendation_result = _recommend()

        st.session_state.team_result_type = "both"
        st.switch_page("pages/team_result.py")
    st.markdown("</div>", unsafe_allow_html=True)


# ── Legacy selected slots (used by show()) ────────────────────────────────

def render_selected_slots(selected_pokemon: List[Dict[str, Any]]) -> None:
    st.markdown(
        f"<p class='selected-count'>현재 선택: {len(selected_pokemon)} / {REQUIRED_TEAM_SIZE}</p>",
        unsafe_allow_html=True,
    )
    columns = st.columns(REQUIRED_TEAM_SIZE)
    for index, column in enumerate(columns):
        with column:
            if index < len(selected_pokemon):
                p = selected_pokemon[index]
                st.markdown(
                    f"""
                    <div class="selected-slot">
                        <img class="selected-slot-image" src="{escape(p['image_url'])}" alt="{escape(p['name'])}">
                        <div class="selected-slot-name">{escape(p['name'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="empty-slot">선택 대기</div>', unsafe_allow_html=True)
