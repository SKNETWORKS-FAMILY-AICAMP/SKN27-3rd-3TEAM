"""팀 분석·추천 결과 전용 페이지 — 포켓몬 디테일 페이지 스타일 기반."""

from __future__ import annotations

import os
import re
import sys
from html import escape
from typing import Any, Dict, List

import streamlit as st

st.set_page_config(
    page_title="팀 분석 결과",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui
from teambuilding.result_styles import inject_result_styles


# ── Helpers ──────────────────────────────────────────────────────────────

_TYPE_KEY_MAP: Dict[str, str] = {
    "노말": "normal", "불꽃": "fire", "물": "water", "전기": "electric",
    "풀": "grass", "얼음": "ice", "격투": "fighting", "독": "poison",
    "땅": "ground", "비행": "flying", "에스퍼": "psychic", "벌레": "bug",
    "바위": "rock", "고스트": "ghost", "드래곤": "dragon", "악": "dark",
    "강철": "steel", "페어리": "fairy",
}


def _type_badge(name: str) -> str:
    key = _TYPE_KEY_MAP.get(name, "normal")
    return f'<span class="tr-type-badge tb-{key}">{escape(name)}</span>'


def _clean_body(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return "".join(f"<p>{escape(p.strip())}</p>" for p in text.split("\n") if p.strip())


# ── Render sections ───────────────────────────────────────────────────────

def _render_selected_team(selected: List[Dict[str, Any]]) -> None:
    if not selected:
        return
    cards = []
    for p in selected:
        types = [t.get("type_name", "") for t in p.get("types", []) if t.get("type_name")]
        img = escape(
            p.get("image_url")
            or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{p.get('pokemon_id')}.png"
        )
        name = escape(p.get("name", ""))
        pid = p.get("pokemon_id", 0)
        types_html = "".join(_type_badge(t) for t in types)
        cards.append(f"""
            <div class="tr-team-card">
                <img class="tr-team-img" src="{img}" alt="{name}">
                <div class="tr-team-name">{name}</div>
                <div class="tr-team-id">#{pid:04d}</div>
                <div class="tr-team-types">{types_html}</div>
            </div>""")

    st.markdown(
        f'<div class="tr-section-title">선택한 팀</div>'
        f'<div class="tr-team-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def _render_insights(insights: Dict[str, Any]) -> None:
    if not insights:
        return

    summary = insights.get("summary", "")
    # 백엔드(team_insight_service)의 키값과 일치시킵니다.
    risk_data = insights.get("risk_summary") or insights.get("risk", "")
    if isinstance(risk_data, list) and risk_data:
        risk = risk_data[0].get("detail", "")
    else:
        risk = str(risk_data)

    strength_data = insights.get("strength_summary") or insights.get("strength", "")
    if isinstance(strength_data, list) and strength_data:
        strength = strength_data[0].get("detail", "")
    else:
        strength = str(strength_data)

    direction = str(insights.get("recommendation_direction") or insights.get("direction", ""))
    
    type_balance = insights.get("type_balance", [])

    # type_balance는 [{"type_name": "불꽃", "count": 2}, ...] 형태의 dict 리스트일 수 있으므로 처리합니다.
    type_badges = "".join(
        _type_badge(t.get("type_name", "") if isinstance(t, dict) else t)
        for t in type_balance
    )
    type_row = f'<div class="tr-summary-types">{type_badges}</div>' if type_badges else ""

    st.markdown(
        f"""<div class="tr-glass tr-summary">
            <div class="tr-summary-label">종합 분석</div>
            <div class="tr-summary-text">{escape(summary)}</div>
            {type_row}
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""<div class="tr-insight-grid">
            <div class="tr-insight-card ic-risk">
                <div class="tr-insight-label">위험 요소</div>
                <div class="tr-insight-text">{escape(risk)}</div>
            </div>
            <div class="tr-insight-card ic-strength">
                <div class="tr-insight-label">강점</div>
                <div class="tr-insight-text">{escape(strength)}</div>
            </div>
            <div class="tr-insight-card ic-direction">
                <div class="tr-insight-label">전략 방향</div>
                <div class="tr-insight-text">{escape(direction)}</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_rag_answer(result: Dict[str, Any], title: str = "AI 종합 의견") -> None:
    rag = result.get("rag_answer") or result.get("final_answer", "")
    if not rag:
        return

    with st.container(border=True):
        st.markdown(f"#### {title}")
        st.markdown(rag)


def _render_detail_cards(
    weaknesses: List[Dict[str, Any]],
    resistances: List[Dict[str, Any]],
    move_coverage: List[Dict[str, Any]],
) -> None:
    def matchup_rows(items: List[Dict[str, Any]], label: str) -> str:
        if not items:
            return "<div class='tr-empty-row'>아직 계산된 정보가 부족해요.</div>"
        rows = []
        for item in items[:6]:
            type_name = item.get("type_name", "")
            score = item.get("score", 0)
            avg = item.get("average_multiplier", 0)
            rows.append(
                f'<div class="tr-metric-row">'
                f'  <div>{_type_badge(type_name)}</div>'
                f'  <div class="tr-metric-right">'
                f'    <strong>{label} {score}점</strong>'
                f'    <span>평균 {float(avg):.2f}배</span>'
                f'  </div>'
                f'</div>'
            )
        return "".join(rows)

    def coverage_rows(items: List[Dict[str, Any]]) -> str:
        if not items:
            return "<div class='tr-empty-row'>기술 타입 정보가 부족해요.</div>"
        max_count = max((i.get("move_count", 0) for i in items[:6]), default=1)
        rows = []
        for item in items[:6]:
            type_name = item.get("type_name", "")
            cnt = item.get("move_count", 0)
            width = int((cnt / max_count) * 100) if max_count else 0
            rows.append(
                f'<div class="tr-cov-row">'
                f'  <div class="tr-cov-top">{_type_badge(type_name)}<strong>{cnt}개</strong></div>'
                f'  <div class="tr-cov-bar"><div class="tr-cov-fill" style="width:{width}%"></div></div>'
                f'</div>'
            )
        return "".join(rows)

    st.markdown(
        f"""<div class="tr-section-title">타입 분석</div>
        <div class="tr-detail-grid">
            <div class="tr-detail-card dc-danger">
                <div class="tr-detail-title">주의할 약점 타입</div>
                <div class="tr-detail-caption">상대가 이 타입 기술을 들고 오면 교체와 선봉 선택을 조심하세요.</div>
                {matchup_rows(weaknesses, "위험")}
            </div>
            <div class="tr-detail-card dc-safe">
                <div class="tr-detail-title">방어가 좋은 타입</div>
                <div class="tr-detail-caption">이 타입 공격은 비교적 안정적으로 받아낼 가능성이 높아요.</div>
                {matchup_rows(resistances, "안정")}
            </div>
            <div class="tr-detail-card dc-coverage">
                <div class="tr-detail-title">기술 타입 커버리지</div>
                <div class="tr-detail-caption">현재 팀이 확보한 공격 타입 분포를 보여줍니다.</div>
                {coverage_rows(move_coverage)}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_recommendation_cards(recommendations: List[Dict[str, Any]]) -> None:
    if not recommendations:
        st.info("추천 결과가 없어요.")
        return

    cards = []
    for idx, p in enumerate(recommendations[:3], start=1):
        rank = p.get("rank", idx)
        score = p.get("hybrid_score", p.get("score", 0))
        img = escape(
            p.get("image_url")
            or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{p.get('pokemon_id')}.png"
        )
        name = escape(p.get("name", ""))
        pid = p.get("pokemon_id", 0)

        raw_types = p.get("types", [])
        type_names = [
            t.get("type_name", t.get("name", "")) if isinstance(t, dict) else str(t)
            for t in raw_types
        ]
        types_html = "".join(_type_badge(t) for t in type_names if t)

        reasons = p.get("reasons") or []
        reasons_html = (
            "".join(f"<li>{escape(r)}</li>" for r in reasons[:4])
            or "<li>현재 팀의 약점을 보완할 수 있는 후보입니다.</li>"
        )

        cards.append(f"""
            <div class="tr-rec-card rank-{rank}">
                <div class="tr-rec-ribbon"></div>
                <div class="tr-rec-body">
                    <div class="tr-rec-rank">{rank}순위</div>
                    <div class="tr-rec-imgwrap">
                        <img class="tr-rec-img" src="{img}" alt="{name}">
                    </div>
                    <div class="tr-rec-name">#{pid:04d} {name}</div>
                    <div class="tr-rec-types">{types_html}</div>
                    <div class="tr-rec-score">추천 점수 <strong>{score}</strong></div>
                    <ul class="tr-rec-reasons">{reasons_html}</ul>
                </div>
            </div>""")

    st.markdown(
        f'<div class="tr-section-title">추천 포켓몬</div>'
        f'<div class="tr-rec-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    inject_common_ui(spacer=True)
    inject_result_styles()

    result_type: str | None = st.session_state.get("team_result_type")

    if not result_type:
        st.error("결과 데이터가 없습니다. 팀 빌더로 돌아가세요.")
        if st.button("← 팀 빌더로 돌아가기", key="back_btn_err"):
            st.switch_page("pages/teambuilding.py")
        return

    tag, title, sub = "팀 분석 & 추천 결과", "팀 전력 분석 & 추천 리포트", "선택한 팀의 강점·약점을 분석하고 최적의 추천 포켓몬을 제안합니다."

    # Hero
    st.markdown(
        f"""<div class="tr-hero">
            <div class="tr-hero-tag">{tag}</div>
            <h1 class="tr-hero-title">{title}</h1>
            <p class="tr-hero-sub">{sub}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Analysis section ──────────────────────────────────────────────────
    analysis_result: Dict[str, Any] = st.session_state.get("analysis_result") or {}
    if analysis_result:
        analysis = analysis_result.get("graph_result", analysis_result)

        _render_selected_team(analysis.get("selected_pokemon", []))
        _render_insights(analysis.get("insights", {}))
        _render_rag_answer(analysis_result)

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
        _render_detail_cards(weaknesses, resistances, move_coverage)

    # ── Recommendation section ────────────────────────────────────────────
    rec_result: Dict[str, Any] = st.session_state.get("recommendation_result") or {}
    if rec_result:
        st.markdown("<hr style='border-color:rgba(255,255,255,0.07);margin:8px 0 4px'>", unsafe_allow_html=True)
        _render_rag_answer(rec_result)
        reranked = rec_result.get("reranked_result", rec_result.get("graph_result", rec_result))
        _render_recommendation_cards(reranked.get("recommendations", []))


main()
