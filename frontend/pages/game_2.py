import streamlit as st
import requests
import os
import sys
import base64

# Ensure utils is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

# ── Backend Configuration ─────────────────────────────────────
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_V1_STR = "/api/v1/pokemon"
CHAT_STREAM_STR = "/api/v1/chat/rap-battle/stream"
ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 비공식 랩배틀",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_base64_img(file_name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

bg_img = get_base64_img("game_2.png")
inject_common_ui(spacer=False)

# ── Data Fetching ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_all_pokemon_names():
    try:
        # 타임아웃 3초 설정으로 무한 대기 방지
        resp = requests.get(f"{BACKEND_URL}{API_V1_STR}/?limit=151", timeout=3.0)
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            if items:
                return {item["name"]: item["id"] for item in items}
    except Exception as e:
        # 에러 발생 시 로그를 남기지 않고 즉시 폴백 데이터 반환
        pass
    
    # 백엔드 연결 실패 시 사용할 기본 데이터
    return {
        "리자몽": 6, "피카츄": 25, "이상해꽃": 3, "거북왕": 9, "뮤츠": 150, 
        "팬텀": 94, "망나뇽": 149, "잠만보": 143, "이브이": 133, "갸라도스": 130
    }

# ── Styles ────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Noto+Sans+KR:wght@400;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
    background: url('{bg_img}') center/cover no-repeat fixed !important;
    background-color: #000000 !important;
}}

[data-testid="stAppViewBlockContainer"], .main {{ background-color: transparent !important; }}
.battle-board-marker {{ position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }}

/* 힙합 네온 보드 (선택자 강화 및 가시성 확보) */
div[data-testid="column"]:has(.battle-board-marker) {{
    background: linear-gradient(135deg, rgba(80, 0, 200, 0.6) 0%, rgba(15, 15, 15, 0.95) 50%, rgba(200, 0, 80, 0.5) 100%) !important;
    backdrop-filter: blur(35px) !important;
    -webkit-backdrop-filter: blur(35px) !important;
    border: 3px solid rgba(180, 0, 255, 0.6) !important;
    border-radius: 45px !important;
    padding: 3rem !important;
    box-shadow: 0 0 80px rgba(180, 0, 255, 0.4) !important;
    margin-top: 100px !important;
    min-height: 700px !important; /* 보드 높이 강제 확보 */
    display: block !important;
}}

/* 포켓몬 카드 */
.battle-pk-card {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 25px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}}
.battle-pk-card img {{ width: 200px; height: 200px; object-fit: contain; }}
.battle-pk-card h3 {{ color: white; font-family: 'Outfit'; font-size: 1.5rem; margin-top: 10px; }}

/* 랩 대사창 */
.rap-verse {{
    background: rgba(0, 0, 0, 0.7);
    border-left: 5px solid #FF00FF;
    padding: 18px 25px;
    margin: 15px 0;
    border-radius: 0 15px 15px 0;
    font-family: 'Noto Sans KR', sans-serif;
    line-height: 1.6;
    color: #ffffff;
    font-size: 1.15rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}}

.vs-text {{
    font-family: 'Outfit', sans-serif;
    font-size: 4.5rem;
    font-weight: 900;
    background: linear-gradient(to bottom, #FF00FF, #00FFFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin: 40px 0;
}}

/* 셀렉트박스 라벨 색상 수정 */
[data-testid="stWidgetLabel"] p {{ color: #ccc !important; font-weight: 600 !important; }}

/* 배틀 버튼 */
div.stButton > button {{
    background: linear-gradient(90deg, #FF00FF, #00FFFF) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 15px 0 !important;
    font-weight: 900 !important;
    font-size: 1.6rem !important;
    box-shadow: 0 10px 30px rgba(255, 0, 255, 0.4) !important;
    transition: all 0.3s ease !important;
}}
div.stButton > button:hover {{
    transform: scale(1.05) !important;
    box-shadow: 0 15px 45px rgba(0, 255, 255, 0.6) !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Game View ─────────────────────────────────────────────────

def show_game():
    # 🌟 초기 데이터 로딩 시 스피너 추가
    if "pk_names" not in st.session_state:
        with st.spinner("🎤 배틀 참가 포켓몬 명단 확인 중..."):
            pk_map = get_all_pokemon_names()
            st.session_state.pk_map = pk_map
            st.session_state.pk_names = list(pk_map.keys())
    
    pk_map = st.session_state.pk_map
    pk_names = st.session_state.pk_names

    _, col_board, _ = st.columns([1, 4.5, 1])

    with col_board:
        # 스타일 적용을 위한 마커
        st.markdown('<div class="battle-board-marker"></div>', unsafe_allow_html=True)

        sel_col1, vs_col, sel_col2 = st.columns([2, 1, 2])

        with sel_col1:
            p1_name = st.selectbox("챌린저 1", pk_names, index=pk_names.index("리자몽") if "리자몽" in pk_names else 0, key="p1_sel")
            p1_id = pk_map[p1_name]
            st.markdown(f"""<div class="battle-pk-card"><img src="{ART_URL}/{p1_id}.png"><h3>{p1_name}</h3></div>""", unsafe_allow_html=True)

        with vs_col:
            st.markdown('<div class="vs-text">VS</div>', unsafe_allow_html=True)

        with sel_col2:
            p2_name = st.selectbox("챌린저 2", pk_names, index=pk_names.index("이상해꽃") if "이상해꽃" in pk_names else 0, key="p2_sel")
            p2_id = pk_map[p2_name]
            st.markdown(f"""<div class="battle-pk-card"><img src="{ART_URL}/{p2_id}.png"><h3>{p2_name}</h3></div>""", unsafe_allow_html=True)

        st.write("")
        battle_btn = st.button("🔥 배틀 시작! (Drop the Beat)", use_container_width=True)

        # ── 배틀 결과 표시 영역 ────────────────────────────────
        if battle_btn:
            # 새 배틀 시작 시 이전 결과 초기화
            st.session_state.pop("rap_script", None)
            st.session_state.pop("rap_p1", None)
            st.session_state.pop("rap_p2", None)

            st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            st.markdown(f"""<h2 style="color: #FF00FF; font-family: 'Outfit'; font-weight: 900; margin-bottom: 20px;">
                🎤 {p1_name} vs {p2_name} — BATTLE SCRIPT</h2>""", unsafe_allow_html=True)

            stream_box = st.empty()
            full_script = ""
            error_occurred = False

            try:
                with requests.post(
                    f"{BACKEND_URL}{CHAT_STREAM_STR}",
                    json={"pokemon1": p1_name, "pokemon2": p2_name},
                    stream=True,
                    timeout=(10, 75),  # (connect, read per chunk)
                ) as resp:
                    if resp.status_code != 200:
                        stream_box.error(f"서버 오류 ({resp.status_code}): AI 힙합 프로듀서가 자리를 비웠습니다.")
                        error_occurred = True
                    else:
                        for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                            if chunk:
                                full_script += chunk
                                stream_box.markdown(
                                    f'<div class="rap-verse" style="white-space: pre-wrap; font-size: 1rem;">'
                                    f'{full_script}▋</div>',
                                    unsafe_allow_html=True,
                                )
            except requests.exceptions.ConnectionError:
                stream_box.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
                error_occurred = True
            except Exception as e:
                stream_box.error(f"오류 발생: {str(e)}")
                error_occurred = True

            if not error_occurred and full_script:
                st.session_state.rap_script = full_script
                st.session_state.rap_p1 = p1_name
                st.session_state.rap_p2 = p2_name
                # 스트리밍 완료 → 포맷된 버전으로 교체
                stream_box.empty()
                st.rerun()

        if "rap_script" in st.session_state:
            p1 = st.session_state.get("rap_p1", "챌린저1")
            p2 = st.session_state.get("rap_p2", "챌린저2")
            st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            st.markdown(f"""<h2 style="color: #FF00FF; font-family: 'Outfit'; font-weight: 900; margin-bottom: 20px;">
                🎤 {p1} vs {p2} — BATTLE SCRIPT</h2>""", unsafe_allow_html=True)

            lines = st.session_state.rap_script.split("\n")
            winner_line = ""
            for line in lines:
                if not line.strip():
                    continue
                if "🏆" in line:
                    winner_line = line
                    continue
                # "이름: 가사" 패턴이면 강조
                if ":" in line:
                    pk, verse = line.split(":", 1)
                    # p1/p2 이름이 포함된 라인에 색상 구분
                    color = "#FF00FF" if p1 in pk else ("#00FFFF" if p2 in pk else "#FFFF00")
                    st.markdown(
                        f'<div class="rap-verse"><strong style="color:{color};">{pk.strip()}</strong>:{verse}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="color:#aaa; font-style:italic; margin:10px 0; font-family:\'Noto Sans KR\';">{line}</div>',
                        unsafe_allow_html=True,
                    )

            if winner_line:
                st.markdown(
                    f'<div style="background: linear-gradient(90deg,rgba(255,215,0,0.2),rgba(255,165,0,0.2)); '
                    f'border: 2px solid gold; border-radius: 15px; padding: 20px; text-align: center; '
                    f'margin-top: 20px; font-size: 1.5rem; font-weight: 900; color: gold; '
                    f'font-family: Outfit, sans-serif;">{winner_line}</div>',
                    unsafe_allow_html=True,
                )

            st.write("")
            if st.button("🔄 다시 배틀하기", use_container_width=True):
                st.session_state.pop("rap_script", None)
                st.session_state.pop("rap_p1", None)
                st.session_state.pop("rap_p2", None)
                st.rerun()

show_game()
