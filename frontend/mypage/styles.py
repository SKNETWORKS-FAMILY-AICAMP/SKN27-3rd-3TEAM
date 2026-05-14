import streamlit as st

MYPAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #000000 !important; /* 기본 배경을 검정으로 설정하여 이미지와 조화 */
}
[data-testid="stAppViewContainer"] {
    background-image: var(--bg-img) !important;
    background-size: cover !important;
    background-attachment: fixed !important;
    background-position: center top !important;
}
[data-testid="stHeader"], footer, [data-testid="stToolbar"] { display: none !important; }
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}

.mp-wrap {
    padding: 20px 0 10px;
    font-family: 'Inter', sans-serif;
    color: #2d3436;
    min-height: 30vh;
}
.mp-container {
    margin: 0 auto;
    width: 75%;
    max-width: 1000px;
}

/* ── Premium Glass Card ── */
.mp-card {
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(25px) saturate(180%);
    -webkit-backdrop-filter: blur(25px) saturate(180%);
    border-radius: 28px;
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.12);
    margin: 0 auto 40px;
    width: 75%;
    max-width: 1000px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    transition: all 0.3s ease;
    overflow: hidden;
    position: relative;
    padding: 45px; /* 패딩 증가 */
}
.mp-card:hover { transform: translateY(-4px); background: rgba(255, 255, 255, 0.55); box-shadow: 0 20px 55px rgba(0,0,0,0.2); }

/* 섹션별 보더 컬러 포인트 */
.card-profile { border-top: 6px solid #FFCB05; padding: 50px; }
.card-actions { border-top: 6px solid #0984e3; }
.card-dev     { border-top: 6px solid #6c5ce7; }
.card-game    { border-top: 6px solid #ff4757; }
.card-dex     { border-top: 6px solid #27ae60; }
.card-badge   { border-top: 6px solid #fd9644; }
.card-activity { border-top: 6px solid #b2bec3; padding: 20px 40px; }

/* ── Labels / Badges ── */
.mp-pill {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 50px;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    background: rgba(241, 242, 246, 0.8);
    color: #2d3436;
    margin-bottom: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.mp-pill-yellow { background: #FFCB05; color: #000; box-shadow: 0 0 15px rgba(255, 203, 5, 0.4); }

/* ── Section Title (Minigame Style) ── */
.mp-section-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 1.6rem;
    color: #ffffff;
    letter-spacing: -0.5px;
    margin: 0 auto 25px;
    width: 75%;
    max-width: 1000px;
    display: flex;
    align-items: center;
    gap: 10px;
    text-shadow: 0 2px 15px rgba(0,0,0,0.5), 0 0 10px rgba(255, 203, 5, 0.3);
}
.mp-section-title::before {
    content: ''; width: 8px; height: 24px; background: #FFCB05; border-radius: 4px;
    box-shadow: 0 0 10px #FFCB05;
}

/* ── Profile Hero ── */
.mp-hero {
    padding: 40px 50px;
    display: flex;
    align-items: center;
    gap: 40px;
}
.mp-avatar {
    width: 130px; height: 130px;
    border-radius: 50%;
    border: 4px solid #FFCB05;
    object-fit: cover;
    animation: mpfloat 6s ease-in-out infinite;
    flex-shrink: 0;
    box-shadow: 0 10px 30px rgba(255, 203, 5, 0.3);
}
@keyframes mpfloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.mp-name {
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 3rem;
    color: #2d3436;
    letter-spacing: -1px;
    margin: 0;
    text-shadow: 0 0 20px rgba(255,255,255,0.8);
}
.mp-handle { font-size: 1rem; color: #2d3436; margin-bottom: 15px; font-weight: 600; }

/* ── Hero Creature & Friends Animation ── */
.mp-hero-creature-wrap {
    display: flex;
    align-items: flex-end;
    gap: 15px;
    flex-shrink: 0;
    margin-right: 20px;
}
.mp-hero-friends {
    position: relative;
    width: 100px;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.mp-hero-friends img {
    height: 80px;
    object-fit: contain;
    animation: mpfloat 5s ease-in-out infinite;
    animation-delay: -1.5s;
    opacity: 0.85;
}
.mp-hero-creature {
    position: relative;
    width: 200px;
    height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.mp-hero-creature img {
    height: 160px;
    object-fit: contain;
    z-index: 2;
    animation: mpfloat 4s ease-in-out infinite;
    filter: drop-shadow(0 10px 25px rgba(0,0,0,0.15));
}
.mp-creature-glow {
    position: absolute;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(255, 203, 5, 0.3) 0%, rgba(255, 203, 5, 0) 70%);
    z-index: 1;
    border-radius: 50%;
    animation: mpglow 4s ease-in-out infinite;
}
@keyframes mpglow {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.2); opacity: 0.8; }
}
@media (max-width: 1100px) {
    .mp-hero-friends { display: none; }
}
@media (max-width: 900px) {
    .mp-hero-creature-wrap { display: none; }
}

/* ── Stats Box (Minigame Style) ── */
.mp-stat-value {
    font-family: 'Outfit', sans-serif;
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
    color: #2d3436;
    text-shadow: 0 0 15px rgba(255,255,255,0.8), 0 2px 5px rgba(0,0,0,0.1);
}
.mp-stat-label {
    font-size: 0.75rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #2d3436;
    margin-bottom: 8px;
    opacity: 0.8;
}

/* ── Activity Log (Premium Light) ── */
.mp-log-item {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 22px;
    border-bottom: 1px solid rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.mp-log-item:hover { background: rgba(255,255,255,0.3); }
.mp-log-icon {
    width: 50px; height: 50px;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 15px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; color: #2d3436; font-size: 0.85rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
.mp-log-main {
    font-weight: 800; font-size: 1.05rem; color: #2d3436;
    text-shadow: 0 0 10px rgba(255,255,255,0.5);
}
.mp-log-sub { font-size: 0.9rem; color: #636e72; font-weight: 500; }
.mp-tag {
    padding: 4px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: 900; text-transform: uppercase;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.mp-tag-ok { background: #e6fffa; color: #27ae60; border: 1px solid rgba(39, 174, 96, 0.2); }
.mp-tag-fail { background: #fff5f5; color: #e53e3e; border: 1px solid rgba(229, 62, 62, 0.2); }

/* ── Progress Bar ── */
.mp-xp-track { background: #f1f2f6; border-radius: 99px; height: 8px; overflow: hidden; }
.mp-xp-fill { height: 100%; background: linear-gradient(90deg, #FFCB05, #fd9644); border-radius: 99px; }

.mp-logout {
    padding: 10px 24px; border-radius: 100px; font-size: 0.85rem; font-weight: 800;
    color: #2d3436 !important; text-decoration: none !important;
    background: rgba(255, 255, 255, 0.7);
    border: 2px solid #FFCB05; /* 포켓몬 골드 테두리 */
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    text-shadow: 0 1px 2px rgba(255,255,255,0.8);
}
.mp-logout:hover { background: #FFCB05; color: #fff !important; transform: translateY(-2px); box-shadow: 0 6px 15px rgba(255,203,5,0.4); }

.badge-case-footer {
    margin-top: 25px; padding: 12px;
    background: #2d3436; /* 어두운 배경으로 변경 */
    border: 2px solid #FFCB05;
    border-radius: 12px;
    font-weight: 900; color: #ffffff !important; font-size: 1.1rem;
    text-align: center;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

@media (max-width: 768px) {
    .mp-hero { flex-direction: column; text-align: center; padding: 30px; }
}

/* ── Kanto Badge Case ── */
.badge-case {
    background: linear-gradient(160deg, #1a1a2e 0%, #16213e 55%, #0f3460 100%);
    border-radius: 24px;
    padding: 32px;
    border: 3px solid #e94560;
    box-shadow:
        0 0 40px rgba(233,69,96,0.12),
        0 20px 60px rgba(0,0,0,0.55),
        inset 0 1px 0 rgba(255,255,255,0.07);
    width: 100%;
    margin: 0;
}
.badge-case-title {
    text-align: center;
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 0.85rem;
    color: #e94560;
    letter-spacing: 6px;
    text-transform: uppercase;
    margin-bottom: 22px;
    text-shadow: 0 0 20px rgba(233,69,96,0.5);
}
.badge-case-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
}
.badge-slot {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
}
.badge-circle {
    width: 120px; height: 120px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    position: relative;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    cursor: pointer;
}
.badge-circle.locked {
    background: radial-gradient(circle, #1e2740, #111827);
    border: 2px solid #2d3748;
    box-shadow: inset 0 4px 14px rgba(0,0,0,0.7);
}
.badge-circle.unlocked {
    background: radial-gradient(circle at 35% 35%, #2d3f5a, #1a2535);
    border: 2px solid rgba(255,255,255,0.25);
}
.badge-circle.unlocked:hover { transform: scale(1.12); }
.badge-circle img.badge-img-lock {
    width: 90px; height: 90px;
    object-fit: contain;
    filter: grayscale(1) brightness(0.22);
}
.badge-circle img.badge-img-unlock {
    width: 100px; height: 100px;
    object-fit: contain;
    filter: drop-shadow(0 3px 10px rgba(0,0,0,0.6));
    transition: transform 0.25s ease;
}
.badge-slot-name {
    font-size: 0.95rem;
    font-weight: 900;
    color: #718096;
    text-align: center;
    max-width: 110px;
    line-height: 1.3;
}
.badge-slot-name.done { color: #e2e8f0; }
.badge-slot-mission {
    font-size: 0.8rem;
    color: #4a5568;
    text-align: center;
    max-width: 110px;
    line-height: 1.3;
}
.badge-slot-mission.done { color: #68d391; }
.badge-case-footer {
    margin-top: 20px;
    text-align: center;
    font-size: 0.75rem;
    color: #4a5568;
    font-weight: 600;
    letter-spacing: 1px;
}
@keyframes badgePulse {
    0%, 100% { opacity: 0.85; }
    50%       { opacity: 1; }
}

/* ── Team Builder History (Streamlit Container Hack) ── */
[data-testid="stVerticalBlock"]:has(> .element-container .history-marker) {
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(25px) saturate(180%) !important;
    border-radius: 28px !important;
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.08) !important;
    margin: 0 auto 40px !important;
    width: 75% !important;
    max-width: 1000px !important;
    border: 1px solid rgba(255, 255, 255, 0.6) !important;
    border-top: 6px solid #a29bfe !important;
    padding: 30px !important;
}

.history-marker {
    position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none;
}

.mp-hist-card-h {
    display: flex;
    align-items: center;
    background: transparent;
    padding: 10px 5px;
    min-height: 90px;
}
.mp-hist-team-block {
    flex: 0 0 200px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.mp-hist-rec-block {
    flex: 0 0 150px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.mp-hist-text-block {
    flex: 1;
    min-width: 0;
    padding: 0 10px;
}
.mp-hist-sep {
    width: 1px;
    align-self: stretch;
    background: rgba(0, 0, 0, 0.08);
    margin: 0 20px;
    flex-shrink: 0;
}
.mp-hist-date {
    font-size: 0.65rem;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.mp-hist-label {
    font-size: 0.65rem;
    font-weight: 900;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 5px;
}
.mp-hist-row {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
}
.mp-hist-pkmn-img {
    width: 42px; height: 42px;
    object-fit: contain;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 8px;
    padding: 2px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
}
.mp-hist-pkmn-rec {
    width: 38px; height: 38px;
}
.mp-hist-conclusion-h {
    font-size: 0.85rem;
    color: #334155;
    line-height: 1.6;
    font-weight: 650;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    word-break: keep-all;
}
.hist-row-divider {
    height: 1px;
    background: rgba(0,0,0,0.06);
    margin: 5px 0;
}
div[data-testid="stColumn"]:has(.hist-btn-marker) button {
    background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 800 !important;
    font-size: 0.9rem !important;
    margin-top: 28px !important;
    box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3) !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stColumn"]:has(.hist-btn-marker) button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(108, 92, 231, 0.45) !important;
}
div[data-testid="stColumn"]:has(.hist-btn-marker) button:disabled {
    background: #e2e8f0 !important;
    color: #94a3b8 !important;
    box-shadow: none !important;
    transform: none !important;
}
</style>
"""


def inject_mypage_styles(bg_b64: str) -> None:
    st.markdown(f"""
    <style>
    :root {{
        --bg-img: url('{bg_b64}');
    }}
    [data-testid="stAppViewBlockContainer"] {{ padding-top: 0 !important; }}
    [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(MYPAGE_CSS, unsafe_allow_html=True)
