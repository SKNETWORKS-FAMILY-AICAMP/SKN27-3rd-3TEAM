import streamlit as st
import requests
import random
import os
import sys
import base64
import time
import json

# Ensure utils is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

# ── Backend Configuration ─────────────────────────────────────
BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"
API_V1_STR = "/api/v1/pokemon"
LOG_API_STR = "/api/v1/users/game-log"
ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 비공식 실루엣",
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

def load_pokemon_data():
    """포켓몬 목록을 세션당 1회만 로드해서 캐시합니다 (라운드마다 API 호출 불필요)."""
    if "_pokemon_data" in st.session_state:
        return st.session_state["_pokemon_data"]
    try:
        resp = requests.get(
            f"{BACKEND_URL}{API_V1_STR}/",
            params={"limit": 2000, "max_id": 1025},
            timeout=15,
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            # alternate form(id 10001+) 제외, 이름 없는 항목 제외
            data = [
                {"id": item["id"], "name": item["name"], "types": item.get("types", [])}
                for item in items
                if 1 <= item["id"] <= 1025 and item.get("name")
            ]
            if data:
                st.session_state["_pokemon_data"] = data
                return data
    except Exception:
        pass
    # fallback: 1세대 하드코딩 없이 최소한 피카츄라도
    fallback = [{"id": 25, "name": "피카츄", "types": [{"slot": 1, "type_": {"id": 13, "name": "전기"}}]}]
    st.session_state["_pokemon_data"] = fallback
    return fallback

def save_game_log(game_type, pokemon_id, is_correct, hint_used=False, wrong_answer_name=None, log_data=None):
    user = st.session_state.get("user")
    user_id = user.get("db_id") if user else None

    extra = log_data or {}
    if wrong_answer_name:
        extra["wrong_name"] = wrong_answer_name

    payload = {
        "user_id": user_id,
        "game_type": game_type,
        "pokemon_id": pokemon_id,
        "is_correct": is_correct,
        "hint_used": hint_used,
        "log_data": json.dumps(extra) if extra else None,
    }

    try:
        requests.post(f"{BACKEND_URL}{LOG_API_STR}", json=payload, timeout=3)
    except Exception:
        pass

bg_img = get_base64_img("mini_game.png")
inject_common_ui(spacer=False)

# ── Session State Initialization ──────────────────────────────
if "sil_target" not in st.session_state:
    st.session_state.sil_target = None
if "sil_revealed" not in st.session_state:
    st.session_state.sil_revealed = False
if "sil_hint_count" not in st.session_state:
    st.session_state.sil_hint_count = 0
if "sil_clear_input" not in st.session_state:
    st.session_state.sil_clear_input = False

# ── Styles ────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@400;600;800&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
    background: url('{bg_img}') center/cover no-repeat fixed !important;
    background-color: #000000 !important;
}}

[data-testid="stAppViewBlockContainer"], .main {{ background-color: transparent !important; }}
.sil-main-card, .btn-marker {{ position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }}

[data-testid="stVerticalBlock"]:has(> .element-container .sil-main-card) {{
    background: linear-gradient(135deg, rgba(42, 117, 187, 0.2) 0%, rgba(20, 20, 20, 0.8) 50%, rgba(227, 53, 53, 0.1) 100%) !important;
    backdrop-filter: blur(25px) !important;
    -webkit-backdrop-filter: blur(25px) !important;
    border: 2px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 35px !important;
    padding: 1rem 3rem !important;
    box-shadow: 0 40px 100px rgba(0,0,0,0.7) !important;
    margin-top: 90px !important;
}}

[data-testid="stTextInput"] {{ 
    width: 55% !important; 
    margin: 30px auto 0 !important;
}}
[data-testid="stTextInput"] [data-baseweb="input"], 
[data-testid="stTextInput"] [data-baseweb="input"] > div,
[data-testid="stTextInput"] input {{
    background-color: #000000 !important;
    border-color: #E33535 !important;
    border-radius: 15px !important;
}}
[data-testid="stTextInput"] [data-baseweb="input"] {{ 
    border: 3px solid #E33535 !important;
    min-height: 55px !important; 
}}
[data-testid="stTextInput"] input {{ color: #ffffff !important; font-family: 'Outfit'; font-weight: 700; font-size: 1.2rem !important; text-align: center !important; }}

div[data-testid="stColumn"]:has(.btn-marker) button {{
    border-radius: 12px !important; height: 45px !important; width: 100% !important;
    border: 2px solid #E33535 !important;
}}
div[data-testid="stColumn"]:has(.btn-marker) button p {{ font-family: 'Outfit'; font-weight: 800; font-size: 1rem !important; }}

div[data-testid="stColumn"]:has(.btn-hint) button {{ background-color: #ffffff !important; }}
div[data-testid="stColumn"]:has(.btn-hint) button p {{ color: #000000 !important; }}
div[data-testid="stColumn"]:has(.btn-giveup) button {{ background-color: #000000 !important; }}
div[data-testid="stColumn"]:has(.btn-giveup) button p {{ color: #ffffff !important; }}
div[data-testid="stColumn"]:has(.btn-next) button {{ background-color: #ffffff !important; }}
div[data-testid="stColumn"]:has(.btn-next) button p {{ color: #000000 !important; }}

.sil-hint-box {{
    background: rgba(10, 10, 10, 0.8) !important;
    border: 1px solid #E33535 !important;
    border-left: 5px solid #E33535 !important;
    border-radius: 12px !important;
    padding: 12px 18px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 5px 15px rgba(0,0,0,0.4) !important;
}}

.sil-hint-box p {{
    color: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
}}

.image-glow-ring {{
    background: rgba(227, 53, 53, 0.05); border-radius: 50%; padding: 25px;
    backdrop-filter: blur(15px); border: 1px solid rgba(227, 53, 53, 0.2);
    box-shadow: inset 0 0 50px rgba(0,0,0,0.6), 0 0 50px rgba(227, 53, 53, 0.4);
    display: inline-block;
}}

.silhouette-img {{ filter: brightness(0); transform: scale(1.0); }}
.silhouette-img.revealed {{
    filter: brightness(1) drop-shadow(0 0 20px rgba(255,255,255,0.4));
    transform: scale(1.1); transition: filter 1s ease-in-out, transform 0.6s ease;
}}
</style>
""", unsafe_allow_html=True)

# ── Game Logic ────────────────────────────────────────────────

def reset_silhouette():
    st.session_state.sil_revealed = False
    st.session_state.sil_hint_count = 0
    st.session_state.sil_clear_input = True

    pokemon_list = load_pokemon_data()
    st.session_state.sil_target = random.choice(pokemon_list)

def show_game():
    if st.session_state.get("sil_clear_input", False):
        if "guess_input" in st.session_state:
            st.session_state.guess_input = ""
        st.session_state.sil_clear_input = False

    target = st.session_state.sil_target
    if not target:
        reset_silhouette()
        st.rerun()

    _, col_main, _ = st.columns([1, 2.2, 1])

    with col_main:
        with st.container():
            st.markdown('<div class="sil-main-card"></div>', unsafe_allow_html=True)
            st.markdown("""<div style="text-align: center; margin-bottom: 5px;"><h1 style="font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 2.8rem; color: white; margin: 0; text-shadow: 0 4px 15px rgba(227, 53, 53, 0.7);">Who's That Pokémon?</h1></div>""", unsafe_allow_html=True)

            img_class = "silhouette-img" + (" revealed" if st.session_state.sil_revealed else "")
            img_url = f"{ART_URL}/{target['id']}.png"
            st.markdown(f"""<div style="text-align: center; margin: 10px 0;"><div class="image-glow-ring"><img src="{img_url}" class="{img_class}" style="width: 350px; height: 350px; object-fit: contain;"></div></div>""", unsafe_allow_html=True)

            if st.session_state.sil_revealed:
                st.markdown(f"""<div style="text-align: center; margin-bottom: 10px;"><div style="background: rgba(227, 53, 53, 0.1); border: 3px solid #E33535; border-radius: 15px; padding: 10px;"><h2 style="color: #ffffff; margin: 0; font-family: 'Outfit'; font-size: 1.8rem;">정답! {target['name'].upper()}</h2></div></div>""", unsafe_allow_html=True)
                time.sleep(2.0)
                reset_silhouette()
                st.rerun()
            else:
                guess = st.text_input("포켓몬 이름 입력", placeholder="이름 입력 후 엔터...", key="guess_input", label_visibility="collapsed")

                if guess:
                    hint_used = st.session_state.sil_hint_count > 0
                    if guess.strip() == target["name"]:
                        # 정답 로그 저장
                        save_game_log("silhouette", target["id"], is_correct=True, hint_used=hint_used)
                        st.balloons()
                        st.session_state.sil_revealed = True
                        st.session_state.sil_clear_input = True
                        st.rerun()
                    else:
                        # 오답 로그 저장 (헷갈린 이름 포함)
                        save_game_log("silhouette", target["id"], is_correct=False, hint_used=hint_used, wrong_answer_name=guess.strip())
                        st.error("❌ 틀렸습니다!")
                        time.sleep(1.5)
                        st.session_state.sil_clear_input = True
                        st.rerun()

            st.write("")
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                st.markdown('<div class="btn-marker btn-hint"></div>', unsafe_allow_html=True)
                if st.button("힌트 보기", key="h_btn", use_container_width=True):
                    st.session_state.sil_hint_count += 1
                    # 힌트 사용 자체도 로그로 남길 수 있지만, 정답 시점에 몰아서 hint_used로 처리합니다.
                    st.rerun()
            with h_col2:
                st.markdown('<div class="btn-marker btn-giveup"></div>', unsafe_allow_html=True)
                if st.button("정답 보기", key="g_btn", use_container_width=True):
                    # 정답 보기(포기) 로그 저장
                    save_game_log("silhouette", target["id"], is_correct=False, hint_used=(st.session_state.sil_hint_count > 0), log_data={"action": "give_up"})
                    st.session_state.sil_revealed = True
                    st.rerun()
            with h_col3:
                st.markdown('<div class="btn-marker btn-next"></div>', unsafe_allow_html=True)
                if st.button("스킵 하기", key="s_btn", use_container_width=True):
                    # 스킵 로그 저장
                    save_game_log("silhouette", target["id"], is_correct=False, hint_used=(st.session_state.sil_hint_count > 0), log_data={"action": "skip"})
                    reset_silhouette()
                    st.rerun()

            if st.session_state.sil_hint_count > 0:
                st.write("")
                if st.session_state.sil_hint_count >= 1:
                    types = ", ".join([t["type_"]["name"] for t in target.get("types", [])])
                    st.markdown(f'<div class="sil-hint-box"><p>🧬 <b>타입:</b> {types}</p></div>', unsafe_allow_html=True)
                if st.session_state.sil_hint_count >= 2:
                    st.markdown(f'<div class="sil-hint-box"><p>🔢 <b>번호:</b> No.{target["id"]}</p></div>', unsafe_allow_html=True)
                if st.session_state.sil_hint_count >= 3:
                    st.markdown(f'<div class="sil-hint-box"><p>🔤 <b>첫 글자:</b> \'{target["name"][0]}\'</p></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_game()
