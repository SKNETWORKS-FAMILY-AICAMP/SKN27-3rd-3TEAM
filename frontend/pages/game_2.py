import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import os
import sys
import base64
import html as htmllib
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_V1_STR  = "/api/v1/pokemon"
CHAT_STREAM  = "/api/v1/chat/rap-battle/stream"
ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

st.set_page_config(
    page_title="포켓몬 비공식 랩배틀",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Assets ────────────────────────────────────────────────────
def get_base64_img(name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

bg_img = get_base64_img("game_2.png")
inject_common_ui(spacer=False)

# ── Data ──────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_all_pokemon_names():
    try:
        r = requests.get(f"{BACKEND_URL}{API_V1_STR}/?limit=151", timeout=3.0)
        if r.status_code == 200:
            items = r.json().get("items", [])
            if items:
                return {it["name"]: it["id"] for it in items}
    except Exception:
        pass
    return {
        "리자몽": 6, "피카츄": 25, "이상해꽃": 3, "거북왕": 9, "뮤츠": 150,
        "팬텀": 94, "망나뇽": 149, "잠만보": 143, "이브이": 133, "갸라도스": 130,
    }

# ── HTML Helpers ──────────────────────────────────────────────
def speech_bubble(text: str, tail: str = "left",
                  color: str = "#FF00FF", ph: str = "🎤 준비 중...") -> str:
    # ★ HTML 안에 \n 절대 금지 — Streamlit Markdown 파서가 HTML 블록을 끊어버림
    content = (
        htmllib.escape(text).replace("\n", "<br>")
        if text.strip()
        else f'<span style="opacity:.4;font-style:italic;">{ph}</span>'
    )
    if tail == "left":
        arrow = f"left:-13px;top:38%;transform:translateY(-50%);border-right:13px solid {color};border-top:8px solid transparent;border-bottom:8px solid transparent;"
    else:
        arrow = f"right:-13px;top:38%;transform:translateY(-50%);border-left:13px solid {color};border-top:8px solid transparent;border-bottom:8px solid transparent;"
    style = (f"position:relative;background:rgba(8,4,22,0.9);border:2px solid {color};"
             f"border-radius:16px;padding:14px 18px;min-height:80px;color:#fff;"
             f"font-family:Noto Sans KR,sans-serif;font-size:.88rem;line-height:1.7;"
             f"box-shadow:0 0 22px {color}44;word-break:keep-all;white-space:pre-wrap;")
    return (f'<div style="{style}">'
            f'<div style="position:absolute;{arrow}width:0;height:0;"></div>'
            f'{content}</div>')

def pk_card(img_id: int, name: str, size: int = 700) -> str:
    # 카드 상자를 제거하고 이미지만 웅장하게 노출
    return (f'<div style="text-align:center; transition: transform 0.3s ease;">'
            f'<img src="{ART_URL}/{img_id}.png" '
            f'style="width:{size}px; height:auto; max-width:110%; object-fit:contain;'
            f'filter:drop-shadow(0 15px 45px rgba(0,0,0,0.9));">'
            f'<div style="color:#fff; font-family:Outfit,sans-serif; font-weight:900;'
            f'font-size:1.6rem; margin-top:5px; letter-spacing:2px; text-transform:uppercase;'
            f'text-shadow: 0 0 15px rgba(255,0,255,0.6);">'
            f'{htmllib.escape(name)}</div></div>')

def inject_floating_panel(script: str, p1: str, p2: str):
    """window.parent.document에 플로팅 버튼+패널을 직접 주입."""
    # 패널 내부 HTML 구성
    inner = (
        '<div style="display:flex;justify-content:space-between;align-items:center;'
        'margin-bottom:12px;border-bottom:1px solid rgba(255,0,255,.3);padding-bottom:10px;">'
        '<span style="color:#FF00FF;font-family:Outfit,sans-serif;font-weight:900;font-size:.9rem;">📜 BATTLE SCRIPT</span>'
        '<button onclick="this.closest(\'[id=rfb-panel]\').style.display=\'none\'"'
        ' style="background:none;border:none;color:#888;font-size:15px;cursor:pointer;padding:0;">✕</button>'
        '</div>'
    )
    for line in script.split("\n"):
        if not line.strip():
            inner += "<br>"
            continue
        if "🏆" in line:
            inner += (
                f'<div style="background:rgba(255,215,0,.15);border:1px solid gold;'
                f'border-radius:10px;padding:10px 14px;color:gold;font-weight:900;'
                f'margin:12px 0;text-align:center;font-family:Outfit,sans-serif;">'
                f'{htmllib.escape(line)}</div>'
            )
        elif ":" in line:
            sp, vr = line.split(":", 1)
            col = "#FF88FF" if p1 in sp else ("#88FFFF" if p2 in sp else "#FFFF99")
            inner += (
                f'<div style="margin:8px 0;font-size:.85rem;line-height:1.55;">'
                f'<span style="color:{col};font-weight:700;">{htmllib.escape(sp.strip())}:</span>'
                f' {htmllib.escape(vr.strip())}</div>'
            )
        else:
            inner += (
                f'<div style="color:#00FFFF;font-style:italic;margin:5px 0;'
                f'font-size:.82rem;">{htmllib.escape(line)}</div>'
            )

    pi_json = json.dumps(inner)
    # st.components.v1.html → 자체 iframe에서 실행 → window.parent로 외부 DOM 접근
    components.html(f"""<script>
(function(){{
  var pd = (window.parent !== window) ? window.parent.document : document;

  // 이전 요소 정리
  ['rfb-panel','rfb-btn'].forEach(function(id){{
    var e = pd.getElementById(id); if(e) e.remove();
  }});

  // ── 패널 생성 ──────────────────────────────────────────────
  var panel = pd.createElement('div');
  panel.id = 'rfb-panel';
  panel.style.cssText = [
    'display:none','position:fixed','bottom:100px','right:22px',
    'width:360px','max-height:66vh',
    'background:rgba(5,2,16,.97)',
    'border:2px solid rgba(150,0,255,.8)',
    'border-radius:22px','padding:18px 20px','overflow-y:auto',
    'z-index:2147483646',
    'backdrop-filter:blur(30px)','-webkit-backdrop-filter:blur(30px)',
    'box-shadow:0 0 80px rgba(140,0,255,.45)',
    'font-family:Noto Sans KR,sans-serif','color:white'
  ].join(';');
  panel.innerHTML = {pi_json};
  pd.body.appendChild(panel);

  // ── 버튼 생성 ──────────────────────────────────────────────
  var btn = pd.createElement('button');
  btn.id  = 'rfb-btn';
  btn.title = '배틀 스크립트 전체보기';
  btn.innerHTML = '📜';
  btn.style.cssText = [
    'position:fixed','bottom:28px','right:28px',
    'width:56px','height:56px','border-radius:50%',
    'background:linear-gradient(135deg,#FF00FF,#5500DD)',
    'border:2px solid rgba(255,255,255,.28)',
    'font-size:22px','cursor:pointer',
    'z-index:2147483647',
    'box-shadow:0 6px 30px rgba(255,0,255,.7)',
    'display:flex','align-items:center','justify-content:center',
    'color:white','transition:transform .18s,box-shadow .18s'
  ].join(';');
  btn.onmouseover = function(){{
    this.style.transform='scale(1.14)';
    this.style.boxShadow='0 8px 36px rgba(0,255,255,.65)';
  }};
  btn.onmouseout = function(){{
    this.style.transform='scale(1)';
    this.style.boxShadow='0 6px 30px rgba(255,0,255,.7)';
  }};
  btn.onclick = function(){{
    var p = pd.getElementById('rfb-panel');
    if(!p) return;
    p.style.display = (p.style.display === 'block') ? 'none' : 'block';
  }};
  pd.body.appendChild(btn);
}})();
</script>""", height=0)

# ── Global Styles ─────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Noto+Sans+KR:wght@400;700;900&display=swap');

html,body,[data-testid="stAppViewContainer"],[data-testid="stHeader"],.stApp{{
    background:url('{bg_img}') center/cover no-repeat fixed !important;
    background-color:#000 !important;
    overflow:hidden !important;
}}
[data-testid="stAppViewBlockContainer"],.main{{
    background-color:transparent !important;
    overflow:hidden !important;
}}

/* ── Glass board (app.py section-inner 패턴) ── */
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

/* ── Title glass card ── */
.title-card{{
    background:rgba(20,5,44,.65);
    border:1px solid rgba(200,0,255,.45);
    border-radius:18px;
    padding:12px 28px;
    text-align:center;
    margin-bottom:16px;
    box-shadow:0 4px 24px rgba(160,0,255,.25);
    backdrop-filter:blur(12px);
}}
.battle-title{{
    font-family:'Outfit',sans-serif;font-size:1.75rem;font-weight:900;
    letter-spacing:2px;margin:0;
    background:linear-gradient(90deg,#FF00FF,#00FFFF,#FF00FF);
    -webkit-background-clip:text;background-clip:text;
    -webkit-text-fill-color:transparent;
    background-size:300%;animation:shimmer 4s linear infinite;
}}
@keyframes shimmer{{from{{background-position:0%}}to{{background-position:300%}}}}

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

/* ── Selectbox ── */
[data-testid="stWidgetLabel"] p{{color:#bbb !important;font-weight:600 !important;font-size:.82rem !important;}}

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
</style>""", unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────
def show_game():
    if "pk_names" not in st.session_state:
        with st.spinner("🎤 배틀 참가 포켓몬 명단 확인 중..."):
            pk_map = get_all_pokemon_names()
            st.session_state.pk_map   = pk_map
            st.session_state.pk_names = list(pk_map.keys())

    pk_map   = st.session_state.pk_map
    pk_names = st.session_state.pk_names

    _, col_board, _ = st.columns([0.2, 5, 0.2])
    with col_board:
        st.markdown('<div class="bbm"></div>', unsafe_allow_html=True)

        # 타이틀 카드
        st.markdown(
            '<div class="title-card">'
            '<h1 class="battle-title">🎤 POKÉMON SOUL RAP BATTLE</h1>'
            '</div>',
            unsafe_allow_html=True,
        )

        # 배틀 영역 — [포켓몬1+말풍선 | VS | 말풍선+포켓몬2]
        p1_col, vs_col, p2_col = st.columns([5, 1.4, 5])

        # ── 챌린저 1 ──
        with p1_col:
            p1_name = st.selectbox(
                "챌린저 1", pk_names,
                index=pk_names.index("리자몽") if "리자몽" in pk_names else 0,
                key="p1_sel",
            )
            p1_id = pk_map[p1_name]
            card1_col, bub1_col = st.columns([4, 1.5])
            with card1_col:
                st.markdown(pk_card(p1_id, p1_name, 500), unsafe_allow_html=True)
            with bub1_col:
                bubble1 = st.empty()

        # ── VS ──
        with vs_col:
            st.markdown(
                '<div class="vs-wrap"><div class="vs-text">VS</div></div>',
                unsafe_allow_html=True,
            )

        # ── 챌린저 2 ──
        with p2_col:
            p2_name = st.selectbox(
                "챌린저 2", pk_names,
                index=pk_names.index("이상해꽃") if "이상해꽃" in pk_names else 0,
                key="p2_sel",
            )
            p2_id = pk_map[p2_name]
            bub2_col, card2_col = st.columns([1.5, 4])
            with bub2_col:
                bubble2 = st.empty()
            with card2_col:
                st.markdown(pk_card(p2_id, p2_name, 500), unsafe_allow_html=True)

        # 이전 배틀 말풍선 복원
        bubble1.markdown(
            speech_bubble(st.session_state.get("rap_p1_verse", ""), "left"),
            unsafe_allow_html=True,
        )
        bubble2.markdown(
            speech_bubble(st.session_state.get("rap_p2_verse", ""), "right", "#00FFFF"),
            unsafe_allow_html=True,
        )

        # 배틀 버튼
        battle_btn = st.button("🔥 배틀 시작! (Drop the Beat)", use_container_width=True)

        # ── 스트리밍 배틀 ──────────────────────────────────────
        if battle_btn:
            for k in ("rap_script", "rap_p1_verse", "rap_p2_verse"):
                st.session_state.pop(k, None)
            bubble1.markdown(speech_bubble("", ph="🎤 비트 타는 중..."), unsafe_allow_html=True)
            bubble2.markdown(speech_bubble("", "right", "#00FFFF", "🎤 비트 타는 중..."), unsafe_allow_html=True)

            full_script = buf = cur1 = cur2 = ""
            current_speaker = None  # persists across chunk boundaries
            error_occurred = False
            try:
                with requests.post(
                    f"{BACKEND_URL}{CHAT_STREAM}",
                    json={"pokemon1": p1_name, "pokemon2": p2_name},
                    stream=True,
                    timeout=(10, 75),
                ) as resp:
                    if resp.status_code != 200:
                        st.error(f"서버 오류 ({resp.status_code}): AI 힙합 프로듀서가 자리를 비웠습니다.")
                        error_occurred = True
                    else:
                        for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                            if not chunk:
                                continue
                            full_script += chunk
                            buf += chunk
                            if "\n" not in buf:
                                continue
                            lines = buf.split("\n")
                            buf = lines[-1]
                            for line in lines[:-1]:
                                stripped = line.strip()
                                if not stripped:
                                    current_speaker = None
                                    continue
                                # strip markdown bold/italic markers before parsing
                                clean = re.sub(r'\*+', '', stripped)
                                if ":" in clean:
                                    sp_raw, vr_raw = clean.split(":", 1)
                                    sp = sp_raw.strip(); vr = vr_raw.strip()
                                    if p1_name in sp:
                                        current_speaker = "p1"
                                        if vr:
                                            cur1 = vr
                                            bubble1.markdown(speech_bubble(cur1, "left"), unsafe_allow_html=True)
                                            time.sleep(1.2) # 대사 간 딜레이 추가
                                    elif p2_name in sp:
                                        current_speaker = "p2"
                                        if vr:
                                            cur2 = vr
                                            bubble2.markdown(speech_bubble(cur2, "right", "#00FFFF"), unsafe_allow_html=True)
                                            time.sleep(1.2) # 대사 간 딜레이 추가
                                    else:
                                        current_speaker = None
                                elif current_speaker == "p1" and clean.strip():
                                    cur1 = clean.strip()
                                    bubble1.markdown(speech_bubble(cur1, "left"), unsafe_allow_html=True)
                                    time.sleep(1.2)
                                elif current_speaker == "p2" and clean.strip():
                                    cur2 = clean.strip()
                                    bubble2.markdown(speech_bubble(cur2, "right", "#00FFFF"), unsafe_allow_html=True)
                                    time.sleep(1.2)
            except requests.exceptions.ConnectionError:
                st.error("백엔드 서버에 연결할 수 없습니다.")
                error_occurred = True
            except Exception as e:
                st.error(f"오류: {str(e)}")
                error_occurred = True

            if not error_occurred and full_script:
                st.session_state.rap_script   = full_script
                st.session_state.rap_p1       = p1_name
                st.session_state.rap_p2       = p2_name
                st.session_state.rap_p1_verse = cur1
                st.session_state.rap_p2_verse = cur2
                st.rerun()

    # ── 플로팅 패널 (parent document 주입) ─────────────────────
    if "rap_script" in st.session_state:
        inject_floating_panel(
            st.session_state.rap_script,
            st.session_state.get("rap_p1", ""),
            st.session_state.get("rap_p2", ""),
        )


show_game()
