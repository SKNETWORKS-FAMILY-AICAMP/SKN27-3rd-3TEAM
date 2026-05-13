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
    page_icon="⚔️",
    layout="wide",
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

# ── CSS ─────────────────────────────────────────────────────────────────

_RESULT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600;700&display=swap');

/* inject_common_ui 이후 다크 테마 덮어쓰기 */
.stApp {
    background: radial-gradient(ellipse at top, #0d1117 0%, #060a10 100%) !important;
    font-family: 'Inter', sans-serif;
}
/* inject_common_ui가 padding:0으로 만든 block-container 복원 */
.stApp > .main > .block-container {
    max-width: 1180px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 2rem 3rem 4rem !important;
}

/* Back button */
.element-container:has(.tr-back-btn) + .element-container button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #aaa !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    height: 42px !important;
    transition: all 0.2s !important;
    margin-bottom: 24px !important;
}
.element-container:has(.tr-back-btn) + .element-container button:hover {
    background: rgba(255,255,255,0.12) !important;
    color: #fff !important;
}

/* Hero */
.tr-hero {
    text-align: center;
    padding: 36px 0 28px;
}
.tr-hero-tag {
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 900;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #FFCB05;
    background: rgba(255,203,5,0.08);
    border: 1px solid rgba(255,203,5,0.22);
    border-radius: 999px;
    padding: 5px 20px;
    margin-bottom: 16px;
}
.tr-hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.8rem;
    font-weight: 900;
    color: #fff;
    line-height: 1.1;
    text-shadow: 0 4px 20px rgba(0,0,0,0.5);
    margin: 0 0 12px;
}
.tr-hero-sub {
    color: rgba(255,255,255,0.35);
    font-size: 0.98rem;
    font-weight: 400;
    margin: 0;
}

/* Glass card base */
.tr-glass {
    background: rgba(15,15,25,0.75);
    backdrop-filter: blur(12px) saturate(160%);
    -webkit-backdrop-filter: blur(12px) saturate(160%);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 22px;
    box-shadow: 0 20px 55px rgba(0,0,0,0.35);
}

/* Section title */
.tr-section-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 900;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 32px 0 18px;
}
.tr-section-title::before {
    content: '';
    width: 5px;
    height: 20px;
    background: #FFCB05;
    border-radius: 3px;
    box-shadow: 0 0 12px rgba(255,203,5,0.55);
    flex-shrink: 0;
}

/* ── Selected team ── */
.tr-team-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 28px;
}
.tr-team-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 16px 10px 14px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    transition: all 0.25s ease;
}
.tr-team-card:hover {
    background: rgba(255,203,5,0.05);
    border-color: rgba(255,203,5,0.22);
    transform: translateY(-5px);
}
.tr-team-img {
    width: 86px;
    height: 80px;
    object-fit: contain;
    filter: drop-shadow(0 8px 16px rgba(0,0,0,0.45));
}
.tr-team-name {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 800;
    color: #e0e0e0;
    text-align: center;
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.tr-team-id {
    font-size: 0.65rem;
    color: #555;
    font-weight: 600;
}
.tr-team-types {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    justify-content: center;
}

/* Type badge */
.tr-type-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 800;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.4);
}
.tb-normal   { background:#A8A77A; }
.tb-fire     { background:#EE8130; }
.tb-water    { background:#6390F0; }
.tb-electric { background:#F7D02C; color:#111; text-shadow:none; }
.tb-grass    { background:#7AC74C; }
.tb-ice      { background:#96D9D9; color:#111; text-shadow:none; }
.tb-fighting { background:#C22E28; }
.tb-poison   { background:#A33EA1; }
.tb-ground   { background:#E2BF65; color:#111; text-shadow:none; }
.tb-flying   { background:#A98FF3; }
.tb-psychic  { background:#F95587; }
.tb-bug      { background:#A6B91A; }
.tb-rock     { background:#B6A136; }
.tb-ghost    { background:#735797; }
.tb-dragon   { background:#6F35FC; }
.tb-dark     { background:#705746; }
.tb-steel    { background:#B7B7CE; color:#111; text-shadow:none; }
.tb-fairy    { background:#D685AD; }

/* ── Summary card ── */
.tr-summary {
    padding: 26px 30px;
    margin-bottom: 20px;
    border-radius: 0 20px 20px 0;
    border-left: 4px solid #FFCB05;
}
.tr-summary-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.75rem;
    font-weight: 900;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #FFCB05;
    margin-bottom: 10px;
}
.tr-summary-text {
    font-size: 1.08rem;
    line-height: 1.85;
    color: rgba(255,255,255,0.82);
    font-weight: 400;
}
.tr-summary-types {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 14px;
}

/* ── Insight 3-col ── */
.tr-insight-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}
.tr-insight-card {
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.02);
}
.tr-insight-card.ic-risk {
    border-color: rgba(239,68,68,0.22);
    background: rgba(239,68,68,0.04);
}
.tr-insight-card.ic-strength {
    border-color: rgba(52,211,153,0.22);
    background: rgba(52,211,153,0.04);
}
.tr-insight-card.ic-direction {
    border-color: rgba(56,189,248,0.22);
    background: rgba(56,189,248,0.04);
}
.tr-insight-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.7rem;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.ic-risk .tr-insight-label      { color: #f87171; }
.ic-strength .tr-insight-label  { color: #34d399; }
.ic-direction .tr-insight-label { color: #38bdf8; }
.tr-insight-text {
    font-size: 0.96rem;
    line-height: 1.75;
    color: rgba(255,255,255,0.72);
    font-weight: 400;
}

/* ── RAG answer card ── */
.tr-rag-card {
    padding: 26px 30px;
    margin-bottom: 28px;
    border-radius: 0 20px 20px 0;
    border-left: 4px solid #2A75BB;
}
.tr-rag-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.75rem;
    font-weight: 900;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #60a5fa;
    margin-bottom: 14px;
}
.tr-rag-conclusion {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    line-height: 1.8;
    margin-bottom: 16px;
    padding: 16px 20px;
    background: rgba(255,255,255,0.035);
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.06);
}
.tr-rag-body {
    font-size: 0.98rem;
    line-height: 1.95;
    color: rgba(255,255,255,0.65);
    font-weight: 400;
}
.tr-rag-body p { margin: 0 0 12px 0; }

/* ── Detail 3-col cards ── */
.tr-detail-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 32px;
}
.tr-detail-card {
    padding: 22px;
    border-radius: 20px;
    min-height: 300px;
}
.tr-detail-card.dc-danger   { background: rgba(239,68,68,0.05);  border: 1px solid rgba(239,68,68,0.18); }
.tr-detail-card.dc-safe     { background: rgba(52,211,153,0.05); border: 1px solid rgba(52,211,153,0.18); }
.tr-detail-card.dc-coverage { background: rgba(56,189,248,0.05); border: 1px solid rgba(56,189,248,0.18); }
.tr-detail-title {
    font-family: 'Outfit', sans-serif;
    font-size: 0.98rem;
    font-weight: 900;
    color: #fff;
    margin-bottom: 6px;
}
.tr-detail-caption {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.38);
    line-height: 1.55;
    margin-bottom: 16px;
}
.tr-metric-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 0;
    border-top: 1px solid rgba(255,255,255,0.06);
    gap: 8px;
}
.tr-metric-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    font-size: 0.85rem;
    font-weight: 700;
    color: rgba(255,255,255,0.78);
}
.tr-metric-right span {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.38);
}
.tr-empty-row {
    padding: 12px;
    color: rgba(255,255,255,0.28);
    font-size: 0.82rem;
    background: rgba(255,255,255,0.015);
    border-radius: 10px;
}
.tr-cov-row {
    padding: 9px 0;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.tr-cov-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 6px;
    font-size: 0.85rem;
    font-weight: 800;
    color: rgba(255,255,255,0.75);
}
.tr-cov-bar {
    height: 6px;
    border-radius: 999px;
    background: rgba(255,255,255,0.07);
    overflow: hidden;
}
.tr-cov-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #2A75BB 0%, #38bdf8 100%);
}

/* ── Recommendation cards ── */
.tr-rec-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 36px;
}
.tr-rec-card {
    position: relative;
    border-radius: 24px;
    overflow: hidden;
    background: rgba(15,15,25,0.85);
    border: 1px solid rgba(255,255,255,0.07);
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.tr-rec-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 32px 70px rgba(0,0,0,0.55);
}
.tr-rec-ribbon { height: 6px; }
.tr-rec-card.rank-1 .tr-rec-ribbon { background: linear-gradient(90deg, #FFCB05, #f59e0b); }
.tr-rec-card.rank-2 .tr-rec-ribbon { background: linear-gradient(90deg, #94a3b8, #cbd5e1); }
.tr-rec-card.rank-3 .tr-rec-ribbon { background: linear-gradient(90deg, #cd7c2f, #b45309); }
.tr-rec-body { padding: 20px 20px 22px; }
.tr-rec-rank {
    font-family: 'Outfit', sans-serif;
    font-size: 1.4rem;
    font-weight: 900;
    color: #fff;
    margin-bottom: 14px;
}
.tr-rec-card.rank-1 .tr-rec-rank { color: #FFCB05; }
.tr-rec-imgwrap {
    height: 160px;
    border-radius: 18px;
    background: rgba(255,255,255,0.025);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}
.tr-rec-img {
    width: 140px;
    height: 130px;
    object-fit: contain;
    filter: drop-shadow(0 12px 24px rgba(0,0,0,0.5));
}
.tr-rec-name {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 900;
    color: #fff;
    margin-bottom: 8px;
}
.tr-rec-types {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 12px;
    min-height: 24px;
}
.tr-rec-score {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-radius: 12px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.55);
    font-size: 0.86rem;
    font-weight: 700;
    margin-bottom: 14px;
}
.tr-rec-score strong {
    color: #FFCB05;
    font-size: 1.15rem;
    font-weight: 900;
}
.tr-rec-reasons {
    margin: 0;
    padding-left: 16px;
    color: rgba(255,255,255,0.5);
    font-size: 0.85rem;
    line-height: 1.85;
}
.tr-rec-reasons li { margin-bottom: 5px; }

@media (max-width: 900px) {
    .tr-team-grid    { grid-template-columns: repeat(3, 1fr); }
    .tr-insight-grid { grid-template-columns: 1fr; }
    .tr-detail-grid  { grid-template-columns: 1fr; }
    .tr-rec-grid     { grid-template-columns: 1fr; }
}
</style>
"""

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


def _render_rag_answer(result: Dict[str, Any]) -> None:
    rag = result.get("rag_answer") or result.get("final_answer", "")
    if not rag:
        return

    parts = str(rag).split("\n\n", 1)
    conclusion = escape(parts[0].strip())
    body = _clean_body(parts[1]) if len(parts) > 1 else f"<p>{conclusion}</p>"

    st.markdown(
        f"""<div class="tr-glass tr-rag-card">
            <div class="tr-rag-label">AI 종합 의견</div>
            <div class="tr-rag-conclusion">{conclusion}</div>
            <div class="tr-rag-body">{body}</div>
        </div>""",
        unsafe_allow_html=True,
    )


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
    st.markdown(_RESULT_CSS, unsafe_allow_html=True)

    result_type: str | None = st.session_state.get("team_result_type")

    if not result_type:
        st.error("결과 데이터가 없습니다. 팀 빌더로 돌아가세요.")
        st.markdown('<div class="tr-back-btn"></div>', unsafe_allow_html=True)
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

    # Back button
    st.markdown('<div class="tr-back-btn"></div>', unsafe_allow_html=True)
    if st.button("← 팀 빌더로 돌아가기", key="back_btn"):
        st.switch_page("pages/teambuilding.py")

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
