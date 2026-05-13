import streamlit as st

RESULT_CSS = """
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


def inject_result_styles() -> None:
    st.markdown(RESULT_CSS, unsafe_allow_html=True)
