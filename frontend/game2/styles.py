import streamlit as st


def inject_game2_styles(bg_img: str = "") -> None:
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Noto+Sans+KR:wght@400;700;900&display=swap');

html,body,[data-testid="stAppViewContainer"],[data-testid="stHeader"],.stApp{{
    background:url('{bg_img}') center/cover no-repeat fixed !important;
    background-color:#000 !important;
    overflow:hidden !important;
}}

/* TTS 데이터 브릿지 (숨김) */
.tts-bridge {{ display: none; }}

.bbm{{position:absolute;width:0;height:0;opacity:0;pointer-events:none;}}
div[data-testid="column"]:has(.bbm){{
    background:rgba(8,4,22,.84) !important;
    backdrop-filter:blur(30px) saturate(180%) !important;
    -webkit-backdrop-filter:blur(30px) saturate(180%) !important;
    border:1px solid rgba(200,0,255,.32) !important;
    border-radius:38px !important;
    padding:1.4rem 2.2rem 1.8rem !important;
    box-shadow:0 20px 80px rgba(0,0,0,.92),0 0 60px rgba(100,0,255,.1) !important;
    margin-top:12px !important;
}}


/* ── VS text — flex center ── */
.vs-wrap{{
    display:flex;align-items:center;justify-content:center;
    height:100%;min-height:260px;
}}
.vs-text{{
    font-family:'Outfit',sans-serif;font-size:2.6rem;font-weight:900;
    background:linear-gradient(to bottom,#FF00FF,#00FFFF);
    -webkit-background-clip:text;background-clip:text;
    -webkit-text-fill-color:transparent;
    line-height:1;
}}

.chall-card{{display:block;width:0;height:0;overflow:hidden;}}

/* ── Selectbox ── */
[data-testid="stWidgetLabel"] p{{color:#CC88FF !important;font-weight:700 !important;font-size:.85rem !important;}}

/* ── Battle Start Card ── */
.battle-start-card{{
    background:rgba(8,4,22,0.90);
    border:2px solid rgba(200,0,255,0.55);
    border-bottom:none;
    border-radius:18px 18px 0 0;
    padding:16px 24px 14px;
    text-align:center;
    backdrop-filter:blur(20px);
    box-shadow:0 -4px 24px rgba(180,0,255,0.18);
}}
.bsc-title{{
    color:#FF88FF;font-family:'Outfit',sans-serif;font-weight:900;
    font-size:1rem;letter-spacing:3px;margin:0 0 5px 0;
}}
.bsc-sub{{
    color:#999;font-family:'Noto Sans KR',sans-serif;
    font-size:0.78rem;margin:0;
}}
/* 배틀 카드 컬럼 안의 버튼만 카드 하단처럼 연결 */
div[data-testid="stVerticalBlock"]:has(.battle-start-card) div.stButton>button,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.battle-start-card) div.stButton>button{{
    border-radius:0 0 18px 18px !important;
    margin-top:0 !important;
    border:2px solid rgba(200,0,255,0.55) !important;
    border-top:none !important;
    box-shadow:0 8px 26px rgba(255,0,255,.45) !important;
}}

/* ── Battle button ── */
div.stButton>button{{
    background:linear-gradient(90deg,#FF00FF,#7700EE,#00FFFF) !important;
    color:#fff !important;border:none !important;border-radius:50px !important;
    padding:13px 0 !important;font-weight:900 !important;font-size:1.3rem !important;
    box-shadow:0 8px 26px rgba(255,0,255,.45) !important;
    transition:all .28s !important;letter-spacing:.5px !important;
    margin-top:12px !important;
}}
div.stButton>button:hover{{
    transform:scale(1.04) !important;
    box-shadow:0 14px 42px rgba(0,255,255,.55) !important;
}}
</style>
""", unsafe_allow_html=True)
