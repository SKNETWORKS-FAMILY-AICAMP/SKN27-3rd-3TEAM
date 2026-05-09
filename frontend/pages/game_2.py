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
    style = (f"position:relative;background:rgba(8,4,22,0.95);border:3px solid {color};"
             f"border-radius:24px;padding:30px 40px;min-height:220px;color:#fff;"
             f"font-family:Noto Sans KR,sans-serif;font-size:1.2rem;line-height:1.8;"
             f"box-shadow:0 0 35px {color}66;word-break:keep-all;white-space:pre-wrap;"
             f"display:flex;align-items:center;justify-content:center;text-align:center;")
    return (f'<div style="{style}">'
            f'<div style="position:absolute;{arrow}width:0;height:0;"></div>'
            f'{content}</div>')

def pk_card(img_id: int, name: str, size: int = 700) -> str:
    # 카드 상자를 제거하고 이미지만 웅장하게 노출
    return (f'<div style="text-align:center; transition: transform 0.3s ease;">'
            f'<img src="{ART_URL}/{img_id}.png" '
            f'style="width:{size}px; height:auto; max-width:110%; object-fit:contain;'
            f'filter:drop-shadow(0 15px 45px rgba(0,0,0,0.9));">'
            f'<div style="display:inline-block;margin-top:10px;padding:8px 28px;'
            f'background:rgba(8,4,22,0.85);border:2px solid rgba(200,0,255,0.55);'
            f'border-radius:50px;backdrop-filter:blur(12px);'
            f'box-shadow:0 0 20px rgba(200,0,255,0.3);">'
            f'<span style="color:#fff;font-family:Outfit,sans-serif;font-weight:900;'
            f'font-size:1.4rem;letter-spacing:3px;text-transform:uppercase;'
            f'text-shadow:0 0 12px rgba(255,0,255,0.8);">'
            f'{htmllib.escape(name)}</span></div></div>')

def tts_speak(text: str, voice: str):
    # pitch, rate, voice_pref(male/female/any)
    presets = {
        "기본":       (1.0,  1.0,  "any"),
        "남성":       (0.8,  1.0,  "male"),
        "여성":       (1.4,  1.1,  "female"),
        "로봇":       (0.1,  0.8,  "any"),
        "래퍼(빠름)": (0.7,  1.35, "male"),
        "래퍼(딥)":   (0.45, 1.0,  "male"),
    }
    pitch, rate, voice_pref = presets.get(voice, presets["기본"])
    components.html(f"""<script>
(function(){{
    var synth = (window.parent !== window) ? window.parent.speechSynthesis : window.speechSynthesis;
    if (!synth) return;
    synth.cancel();
    function speak(voices) {{
        var uttr = new SpeechSynthesisUtterance({json.dumps(text)});
        uttr.lang = 'ko-KR';
        uttr.pitch = {pitch};
        uttr.rate  = {rate};
        var pref = {json.dumps(voice_pref)};
        var ko = voices.filter(function(v){{ return v.lang.indexOf('ko') === 0; }});
        var chosen = null;
        if (pref === 'male') {{
            chosen = ko.find(function(v){{
                var n = v.name.toLowerCase();
                return n.indexOf('male') >= 0 || n.indexOf('인준') >= 0 ||
                       n.indexOf('hyunsu') >= 0 || n.indexOf('sunhi') < 0;
            }});
        }} else if (pref === 'female') {{
            chosen = ko.find(function(v){{
                var n = v.name.toLowerCase();
                return n.indexOf('heami') >= 0 || n.indexOf('female') >= 0 || n.indexOf('여') >= 0;
            }});
        }}
        // Neural/Natural 목소리 우선 선택 (고품질)
        if (!chosen) {{
            chosen = ko.find(function(v){{
                var n = v.name.toLowerCase();
                return n.indexOf('natural') >= 0 || n.indexOf('neural') >= 0 || n.indexOf('online') >= 0;
            }});
        }}
        if (!chosen && ko.length) chosen = ko[0];
        if (chosen) uttr.voice = chosen;
        synth.speak(uttr);
    }}
    // Chrome: getVoices()가 비동기로 로드되므로 voiceschanged 대기 처리
    setTimeout(function() {{
        var vs = synth.getVoices();
        if (vs && vs.length > 0) {{
            speak(vs);
        }} else {{
            synth.addEventListener('voiceschanged', function(){{ speak(synth.getVoices()); }}, {{once: true}});
            speak([]);
        }}
    }}, 150);
}})();
</script>""", height=0)
    estimated = len(text.strip()) / (5.0 * rate)
    time.sleep(max(2.0, estimated) + 0.5)

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

# ── Global Styles & TTS Engine ────────────────────────────────
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

# ── Challenger card style — parent.head CSS + JS 이중 적용 ──
components.html("""<script>
(function(){
    var pd = (window.parent !== window) ? window.parent.document : document;

    // 1) parent.head 에 <style> 태그 직접 주입
    //    data-testid 가 'column' 또는 'stColumn' 중 어느 쪽이든 커버
    var sid = 'rfb-chall-style';
    var sEl = pd.getElementById(sid);
    if (!sEl) { sEl = pd.createElement('style'); sEl.id = sid; pd.head.appendChild(sEl); }
    sEl.textContent =
        'div[data-testid="column"]:has(.chall-card):not(:has(.bbm)),' +
        'div[data-testid="stColumn"]:has(.chall-card):not(:has(.bbm)){' +
            'background:rgba(8,4,22,0.92)!important;' +
            'border:2px solid rgba(200,0,255,0.6)!important;' +
            'border-radius:22px!important;' +
            'padding:1rem 1.4rem 1.4rem!important;' +
            'backdrop-filter:blur(28px) saturate(160%)!important;' +
            '-webkit-backdrop-filter:blur(28px) saturate(160%)!important;' +
            'box-shadow:0 8px 36px rgba(0,0,0,0.8),0 0 30px rgba(180,0,255,0.3)!important;' +
            'margin-top:6px!important;' +
        '}';

    // 2) JS inline setProperty — CSS 가 못 뚫을 때 최후 보루
    var P = [
        ['background','rgba(8,4,22,0.92)'],
        ['border','2px solid rgba(200,0,255,0.6)'],
        ['border-radius','22px'],
        ['padding','1rem 1.4rem 1.4rem'],
        ['backdrop-filter','blur(28px) saturate(160%)'],
        ['-webkit-backdrop-filter','blur(28px) saturate(160%)'],
        ['box-shadow','0 8px 36px rgba(0,0,0,0.8),0 0 30px rgba(180,0,255,0.3)'],
        ['margin-top','6px']
    ];
    function apply(){
        pd.querySelectorAll('.chall-card').forEach(function(m){
            var el = m;
            // data-testid 가 column 이든 stColumn 이든 둘 다 탐색
            while(el && el !== pd.body){
                var td = el.getAttribute && el.getAttribute('data-testid');
                if(td === 'column' || td === 'stColumn') break;
                el = el.parentElement;
            }
            if(!el || el === pd.body) return;
            if(el.querySelector('.bbm')) return;   // col_board 제외
            P.forEach(function(p){ el.style.setProperty(p[0],p[1],'important'); });
        });
    }
    [200,500,1000,2000].forEach(function(t){ setTimeout(apply,t); });
    var tmr;
    new MutationObserver(function(){ clearTimeout(tmr); tmr=setTimeout(apply,150); })
        .observe(pd.body,{childList:true,subtree:true});
})();
</script>""", height=0)

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

        st.markdown("<br><br>", unsafe_allow_html=True)


        # ── 설정 카드 행 ──────────────────────────────────────────
        s1_col, _, s2_col = st.columns([1.1, 1.3, 1.1])

        with s1_col:
            st.markdown('<div class="chall-card"></div>', unsafe_allow_html=True)
            p1_name = st.selectbox(
                "🔴 챌린저 1", pk_names,
                index=pk_names.index("리자몽") if "리자몽" in pk_names else 0,
                key="p1_sel",
            )
            p1_voice = st.selectbox("🎙 목소리 톤", ["기본", "남성", "여성", "로봇", "래퍼(빠름)", "래퍼(딥)"], key="v1_sel")

        with s2_col:
            st.markdown('<div class="chall-card"></div>', unsafe_allow_html=True)
            p2_name = st.selectbox(
                "🔵 챌린저 2", pk_names,
                index=pk_names.index("이상해꽃") if "이상해꽃" in pk_names else 0,
                key="p2_sel",
            )
            p2_voice = st.selectbox("🎙 목소리 톤", ["기본", "남성", "여성", "로봇", "래퍼(빠름)", "래퍼(딥)"], key="v2_sel")

        p1_id = pk_map[p1_name]
        p2_id = pk_map[p2_name]

        # ── 배틀 시작 카드 (독립 행) ────────────────────────────
        _, start_col, _ = st.columns([1.5, 2, 1.5])
        with start_col:
            st.markdown(
                '<div class="battle-start-card">'
                '<p class="bsc-title">🎤 RAP BATTLE</p>'
                '<p class="bsc-sub">챌린저를 선택하고 배틀을 시작하세요</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            battle_btn = st.button("🔥 배틀 시작! (Drop the Beat)", use_container_width=True)

        # ── 배틀 영역 — [포켓몬1 | 중앙 말풍선 | 포켓몬2] ────────
        p1_img_col, mid_bubble_col, p2_img_col = st.columns([1.1, 1.3, 1.1])

        with p1_img_col:
            st.markdown(pk_card(p1_id, p1_name, 500), unsafe_allow_html=True)

        # ── 중앙 말풍선 영역 ──
        with mid_bubble_col:
            bubble1 = st.empty()
            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            bubble2 = st.empty()

        with p2_img_col:
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

        # ── 스트리밍 배틀 ──────────────────────────────────────
        if battle_btn:
            for k in ("rap_script", "rap_p1_verse", "rap_p2_verse"):
                st.session_state.pop(k, None)
            bubble1.markdown(speech_bubble("", ph="🎤 챌린저 1 준비 중..."), unsafe_allow_html=True)
            bubble2.markdown(speech_bubble("", "right", "#00FFFF", "🎤 챌린저 2 준비 중..."), unsafe_allow_html=True)

            full_script = buf = cur1 = cur2 = ""
            current_speaker = None
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
                            if not chunk: continue
                            full_script += chunk
                            buf += chunk
                            if "\n" not in buf: continue
                            lines = buf.split("\n")
                            buf = lines[-1]
                            for line in lines[:-1]:
                                stripped = line.strip()
                                if not stripped:
                                    current_speaker = None
                                    continue
                                clean = re.sub(r'\*+', '', stripped)
                                if ":" in clean:
                                    sp_raw, vr_raw = clean.split(":", 1)
                                    sp = sp_raw.strip(); vr = vr_raw.strip()
                                    if (p1_name in sp):
                                        current_speaker = "p1"
                                        if vr:
                                            cur1 = vr
                                            bubble1.markdown(speech_bubble(cur1, "left"), unsafe_allow_html=True)
                                            tts_speak(cur1, p1_voice)
                                    elif (p2_name in sp):
                                        current_speaker = "p2"
                                        if vr:
                                            cur2 = vr
                                            bubble2.markdown(speech_bubble(cur2, "right", "#00FFFF"), unsafe_allow_html=True)
                                            tts_speak(cur2, p2_voice)
                                    else:
                                        current_speaker = None
                                elif current_speaker == "p1" and clean.strip():
                                    cur1 = clean.strip()
                                    bubble1.markdown(speech_bubble(cur1, "left"), unsafe_allow_html=True)
                                    tts_speak(cur1, p1_voice)
                                elif current_speaker == "p2" and clean.strip():
                                    cur2 = clean.strip()
                                    bubble2.markdown(speech_bubble(cur2, "right", "#00FFFF"), unsafe_allow_html=True)
                                    tts_speak(cur2, p2_voice)
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
