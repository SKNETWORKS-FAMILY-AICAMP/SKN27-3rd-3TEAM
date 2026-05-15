import streamlit as st

RESULT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Background & container ─────────────────────────────────────── */
.stApp {
    background: linear-gradient(140deg, #f0f4ff 0%, #fafbff 45%, #f5f0ff 100%) !important;
    min-height: 100vh;
    font-family: 'Inter', sans-serif;
}
[data-testid="stAppViewContainer"] .block-container,
[data-testid="stMain"] .block-container,
.stApp .main .block-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 1.5rem 5rem 5rem !important;
}

/* ── Hero ────────────────────────────────────────────────────────── */
.tr-hero {
    margin-left: -5rem;
    margin-right: -5rem;
    width: calc(100% + 10rem);
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    text-align: center;
    padding: 60px 20px 40px;
    margin-top: -1.5rem;
    margin-bottom: 40px;
}
.tr-hero-tag {
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 0.78rem;
    font-weight: 900;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #E33535;
    background: rgba(227,53,53,0.08);
    border: 1px solid rgba(227,53,53,0.2);
    border-radius: 999px;
    padding: 5px 20px;
    margin-bottom: 18px;
}
.tr-hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.9rem;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin: 0 0 14px;
}
.tr-hero-sub {
    color: #94a3b8;
    font-size: 1rem;
    font-weight: 400;
    margin: 0;
}

/* ── Glass card base ─────────────────────────────────────────────── */
.tr-glass {
    background: rgba(255,255,255,0.78);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border: 1px solid rgba(255,255,255,0.95);
    border-radius: 22px;
    box-shadow: 0 4px 28px rgba(15,23,42,0.07), 0 1px 4px rgba(15,23,42,0.04);
}

/* ── Section title ───────────────────────────────────────────────── */
.tr-section-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 900;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    margin: 36px 0 18px;
}
.tr-section-title::before {
    content: '';
    width: 5px;
    height: 20px;
    background: linear-gradient(180deg, #E33535, #ff6b6b);
    border-radius: 3px;
    flex-shrink: 0;
}

/* ── Selected team cards ─────────────────────────────────────────── */
.tr-team-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 28px;
}
.tr-team-card {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(226,232,240,0.9);
    border-radius: 18px;
    padding: 18px 10px 14px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    box-shadow: 0 2px 12px rgba(15,23,42,0.05);
}
.tr-team-img {
    width: 82px;
    height: 76px;
    object-fit: contain;
    filter: drop-shadow(0 6px 14px rgba(15,23,42,0.12));
}
.tr-team-name {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 800;
    color: #1e293b;
    text-align: center;
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.tr-team-id {
    font-size: 0.65rem;
    color: #94a3b8;
    font-weight: 600;
}
.tr-team-types {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    justify-content: center;
}

/* ── Type badges ─────────────────────────────────────────────────── */
.tr-type-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 800;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.25);
}
.tb-normal   { background:#A8A77A; }
.tb-fire     { background:#EE8130; }
.tb-water    { background:#6390F0; }
.tb-electric { background:#F7D02C; color:#1a1a1a; text-shadow:none; }
.tb-grass    { background:#7AC74C; }
.tb-ice      { background:#96D9D9; color:#1a1a1a; text-shadow:none; }
.tb-fighting { background:#C22E28; }
.tb-poison   { background:#A33EA1; }
.tb-ground   { background:#E2BF65; color:#1a1a1a; text-shadow:none; }
.tb-flying   { background:#A98FF3; }
.tb-psychic  { background:#F95587; }
.tb-bug      { background:#A6B91A; }
.tb-rock     { background:#B6A136; }
.tb-ghost    { background:#735797; }
.tb-dragon   { background:#6F35FC; }
.tb-dark     { background:#705746; }
.tb-steel    { background:#B7B7CE; color:#1a1a1a; text-shadow:none; }
.tb-fairy    { background:#D685AD; }

/* ── Summary glass card ──────────────────────────────────────────── */
.tr-summary {
    padding: 28px 32px;
    margin-bottom: 20px;
    border-radius: 22px;
    border-left: 5px solid #E33535;
}
.tr-summary-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    font-weight: 900;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #E33535;
    margin-bottom: 10px;
}
.tr-summary-text {
    font-size: 1.05rem;
    line-height: 1.9;
    color: #1e293b;
    font-weight: 400;
}
.tr-summary-types {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 14px;
}

/* ── Insight 3-col ───────────────────────────────────────────────── */
.tr-insight-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}
.tr-insight-card {
    padding: 22px;
    border-radius: 18px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}
.tr-insight-card.ic-risk {
    background: rgba(255,241,242,0.9);
    border: 1px solid rgba(254,202,202,0.8);
    box-shadow: 0 2px 16px rgba(239,68,68,0.06);
}
.tr-insight-card.ic-strength {
    background: rgba(240,253,244,0.9);
    border: 1px solid rgba(187,247,208,0.8);
    box-shadow: 0 2px 16px rgba(52,211,153,0.06);
}
.tr-insight-card.ic-direction {
    background: rgba(239,246,255,0.9);
    border: 1px solid rgba(191,219,254,0.8);
    box-shadow: 0 2px 16px rgba(59,130,246,0.06);
}
.tr-insight-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.7rem;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.ic-risk .tr-insight-label      { color: #dc2626; }
.ic-strength .tr-insight-label  { color: #16a34a; }
.ic-direction .tr-insight-label { color: #2563eb; }
.tr-insight-text {
    font-size: 0.95rem;
    line-height: 1.8;
    color: #374151;
    font-weight: 400;
}

/* ── RAG answer glass card ───────────────────────────────────────── */
.tr-rag-card {
    padding: 28px 32px;
    margin-bottom: 28px;
    border-radius: 22px;
    border-left: 5px solid #2563eb;
}
.tr-rag-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    font-weight: 900;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #2563eb;
    margin-bottom: 14px;
}
.tr-rag-conclusion {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.8;
    margin-bottom: 18px;
    padding: 18px 22px;
    background: rgba(239,246,255,0.8);
    border-radius: 14px;
    border: 1px solid rgba(191,219,254,0.6);
}
.tr-rag-body {
    font-size: 0.97rem;
    line-height: 1.95;
    color: #475569;
    font-weight: 400;
}
.tr-rag-body p { margin: 0 0 12px 0; }

/* ── Type analysis 3-col ─────────────────────────────────────────── */
.tr-detail-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 32px;
}
.tr-detail-card {
    padding: 24px;
    border-radius: 20px;
    min-height: 300px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 2px 20px rgba(15,23,42,0.05);
}
.tr-detail-card.dc-danger {
    background: rgba(255,241,242,0.88);
    border: 1px solid rgba(254,202,202,0.7);
}
.tr-detail-card.dc-safe {
    background: rgba(240,253,244,0.88);
    border: 1px solid rgba(187,247,208,0.7);
}
.tr-detail-card.dc-coverage {
    background: rgba(239,246,255,0.88);
    border: 1px solid rgba(191,219,254,0.7);
}
.tr-detail-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1rem;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 6px;
}
.tr-detail-caption {
    font-size: 0.8rem;
    color: #64748b;
    line-height: 1.55;
    margin-bottom: 16px;
}
.tr-metric-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-top: 1px solid rgba(148,163,184,0.2);
    gap: 8px;
}
.tr-metric-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    font-size: 0.86rem;
    font-weight: 700;
    color: #1e293b;
}
.tr-metric-right span {
    font-size: 0.73rem;
    color: #94a3b8;
    font-weight: 500;
}
.tr-empty-row {
    padding: 14px;
    color: #94a3b8;
    font-size: 0.84rem;
    background: rgba(248,250,252,0.8);
    border-radius: 10px;
    border: 1px solid rgba(226,232,240,0.6);
}
.tr-cov-row {
    padding: 10px 0;
    border-top: 1px solid rgba(148,163,184,0.2);
}
.tr-cov-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 7px;
    font-size: 0.86rem;
    font-weight: 800;
    color: #1e293b;
}
.tr-cov-bar {
    height: 6px;
    border-radius: 999px;
    background: rgba(203,213,225,0.5);
    overflow: hidden;
}
.tr-cov-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #3b82f6, #2563eb);
}

/* ── Recommendation cards ────────────────────────────────────────── */
.tr-rec-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 40px;
}
.tr-rec-card {
    position: relative;
    border-radius: 24px;
    overflow: hidden;
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border: 1px solid rgba(226,232,240,0.9);
    box-shadow: 0 8px 40px rgba(15,23,42,0.09), 0 1px 4px rgba(15,23,42,0.04);
}
.tr-rec-ribbon { height: 5px; }
.tr-rec-card.rank-1 .tr-rec-ribbon { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.tr-rec-card.rank-2 .tr-rec-ribbon { background: linear-gradient(90deg, #64748b, #94a3b8); }
.tr-rec-card.rank-3 .tr-rec-ribbon { background: linear-gradient(90deg, #b45309, #d97706); }
.tr-rec-body { padding: 22px 22px 24px; }
.tr-rec-rank {
    font-family: 'Outfit', sans-serif;
    font-size: 1.35rem;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 14px;
}
.tr-rec-card.rank-1 .tr-rec-rank { color: #d97706; }
.tr-rec-imgwrap {
    height: 160px;
    border-radius: 18px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid rgba(226,232,240,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}
.tr-rec-img {
    width: 138px;
    height: 128px;
    object-fit: contain;
    filter: drop-shadow(0 8px 18px rgba(15,23,42,0.14));
}
.tr-rec-name {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 8px;
}
.tr-rec-types {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 14px;
    min-height: 24px;
}
.tr-rec-score {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-radius: 12px;
    background: #f8fafc;
    border: 1px solid rgba(226,232,240,0.8);
    color: #64748b;
    font-size: 0.87rem;
    font-weight: 700;
    margin-bottom: 14px;
}
.tr-rec-score strong {
    color: #2563eb;
    font-size: 1.15rem;
    font-weight: 900;
}
.tr-rec-reasons {
    margin: 0;
    padding-left: 16px;
    color: #475569;
    font-size: 0.87rem;
    line-height: 1.9;
    font-weight: 400;
}
.tr-rec-reasons li { margin-bottom: 5px; }

/* ── Responsive ──────────────────────────────────────────────────── */
@media (max-width: 1100px) {
    .stApp > .main > .block-container { padding: 1.5rem 2.5rem 4rem !important; }
    .tr-hero { margin-left: -2.5rem; margin-right: -2.5rem; width: calc(100% + 5rem); }
    .tr-team-grid    { grid-template-columns: repeat(3, 1fr); }
    .tr-insight-grid { grid-template-columns: 1fr; }
    .tr-detail-grid  { grid-template-columns: 1fr; }
    .tr-rec-grid     { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 720px) {
    .stApp > .main > .block-container { padding: 1rem 1.2rem 3rem !important; }
    .tr-hero { margin-left: -1.2rem; margin-right: -1.2rem; width: calc(100% + 2.4rem); }
    .tr-rec-grid { grid-template-columns: 1fr; }
}
</style>
"""


def inject_result_styles() -> None:
    st.markdown(RESULT_CSS, unsafe_allow_html=True)
