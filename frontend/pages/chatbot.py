import os
import sys
import copy
import uuid
import html as _html
import requests
import base64
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080")

# ── API helpers ───────────────────────────────────────────────────────────

def _get(path, params=None):
    return requests.get(f"{BACKEND_URL}{path}", params=params, timeout=10)

def _post(path, **kwargs):
    return requests.post(f"{BACKEND_URL}{path}", timeout=180, **kwargs)

def _delete(path):
    return requests.delete(f"{BACKEND_URL}{path}", timeout=10)

@st.cache_data(ttl=60)
def fetch_models():
    try:
        data = _get("/api/v1/chatbot/models").json()
        return data["models"], data["default"]
    except Exception:
        return ["gpt-4o-mini"], "gpt-4o-mini"

def api_chat(query, history, model, session_id=None, user_id=None):
    r = _post("/api/v1/chatbot/chat", json={
        "query": query, "history": history,
        "model": model, "session_id": session_id,
        "user_id": user_id,
    })
    r.raise_for_status()
    return r.json()

def api_sessions(user_id=None):
    try:
        params = {"user_id": user_id} if user_id else {}
        return _get("/api/v1/chatbot/sessions", params=params).json()
    except Exception:
        return []

def api_messages(session_id):
    try:
        return _get(f"/api/v1/chatbot/sessions/{session_id}/messages").json()
    except Exception:
        return []

def api_delete(session_id):
    try:
        _delete(f"/api/v1/chatbot/sessions/{session_id}")
    except Exception:
        pass

MODELS_LIST, DEFAULT_MODEL = fetch_models()

# ── Tool badges ───────────────────────────────────────────────────────────

_TOOL_COLORS = {
    "search_pokemon_db":      ("#3B4CCA", "rgba(59,76,202,0.15)"),
    "search_flavor_text":     ("#7c3aed", "rgba(124,58,237,0.15)"),
    "search_evolution_chain": ("#059669", "rgba(5,150,105,0.15)"),
    "search_type_relations":  ("#d97706", "rgba(217,119,6,0.15)"),
    "web_search":             ("#6b7280", "rgba(107,114,128,0.15)"),
}
_TOOL_LABELS = {
    "search_pokemon_db":      "DB 검색",
    "search_flavor_text":     "도감 검색",
    "search_evolution_chain": "진화 체인",
    "search_type_relations":  "타입 상성",
    "web_search":             "웹 검색",
}

def render_user_bubble(content: str, avatar_url: str) -> None:
    escaped = _html.escape(content)
    st.markdown(
        f'<div style="display:flex;justify-content:flex-end;align-items:flex-end;'
        f'gap:10px;padding:6px 16px 6px 80px;">'
        f'<div style="background:linear-gradient(135deg,#EE1515 0%,#c0392b 100%);'
        f'color:#fff;padding:12px 16px;border-radius:18px 4px 18px 18px;'
        f'font-size:14px;line-height:1.75;font-family:Inter,sans-serif;'
        f'box-shadow:0 4px 14px rgba(238,21,21,0.22);word-break:break-word;'
        f'white-space:pre-wrap;">{escaped}</div>'
        f'<img src="{avatar_url}" style="width:51px;height:51px;border-radius:50%;'
        f'flex-shrink:0;object-fit:cover;border:2px solid #e2e8f0;"></div>',
        unsafe_allow_html=True,
    )

def render_tool_badges(tools: list) -> None:
    if not tools:
        return
    badges = []
    for t in tools:
        color, bg = _TOOL_COLORS.get(t, ("#64748b", "rgba(100,116,139,0.15)"))
        label = _TOOL_LABELS.get(t, t)
        badges.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'background:{bg};color:{color};border:1px solid {color}55;'
            f'border-radius:20px;padding:3px 10px;font-size:11px;font-weight:700;'
            f'letter-spacing:0.3px;margin-right:4px;">⚙ {label}</span>'
        )
    st.markdown(
        '<div style="margin-top:8px;line-height:2.2;">' + "".join(badges) + "</div>",
        unsafe_allow_html=True,
    )

# ── Page config ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="포켓몬 박사 챗봇",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True, hide_sidebar=True)

# ── CSS ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;500;600;700&display=swap');

/* ── White theme background ── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section[data-testid="stMain"],
.stMain {
    background: #ffffff !important;
}
.block-container {
    background: #ffffff !important;
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── No page scroll ── */
html, body { overflow: hidden !important; }

/* ── Main layout — stretch both columns to full height ── */
[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}

/* ── Left panel (Grey sidebar) — full viewport height ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
    background: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
    height: 100vh !important;
    position: sticky !important;
    top: 0 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    > [data-testid="stVerticalBlock"] {
    padding: 0 14px 14px !important;
    height: 100vh !important;
}

/* ── Right panel (White chat area) — full viewport height ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
    background: #ffffff !important;
    min-height: calc(100vh - 80px) !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
    > [data-testid="stVerticalBlock"] {
    padding: 0 !important;
    min-height: calc(100vh - 80px) !important;
}

/* ── Reset: nested columns inside left panel (Q-list rows) ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    background: transparent !important;
    min-height: unset !important;
    border: none !important;
}

/* ── Left panel header ── */
.cb-left-header {
    padding: 18px 0 14px;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 14px;
}
.cb-left-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 900;
    color: #1a1a2e;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.cb-pokeball {
    width: 28px; height: 28px;
    background: radial-gradient(circle at 38% 38%, #EE1515 50%, #c0392b 50%);
    border-radius: 50%;
    border: 2.5px solid #fff;
    position: relative;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(238,21,21,0.35);
}
.cb-pokeball::after {
    content: '';
    position: absolute;
    top: 50%; left: 0; right: 0;
    height: 2px; background: #222;
    transform: translateY(-50%);
}

/* ── Model selector radio ── */
[data-testid="stRadio"] [data-testid="stWidgetLabel"] { display: none !important; }
[data-testid="stRadio"] > div {
    flex-direction: row !important;
    gap: 4px !important;
    background: rgba(0,0,0,0.04);
    border-radius: 30px;
    padding: 3px 5px;
    border: 1px solid #e2e8f0;
    display: inline-flex !important;
    width: 100%;
    justify-content: center;
}
[data-testid="stRadio"] label {
    background: transparent !important;
    border: none !important;
    border-radius: 22px !important;
    padding: 5px 12px !important;
    font-size: 11.5px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    color: #9ca3af !important;
    white-space: nowrap !important;
    box-shadow: none !important;
    flex: 1;
    text-align: center;
    transition: all 0.2s !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #EE1515 0%, #c0392b 100%) !important;
    color: #fff !important;
    box-shadow: 0 2px 10px rgba(238,21,21,0.35) !important;
}
[data-testid="stRadio"] label input {
    position: absolute !important; opacity: 0 !important;
    width: 1px !important; height: 1px !important;
}
div:has(> [data-testid="stRadio"]) {
    margin: 10px 0 !important; padding: 0 !important;
}

/* ── Q list section label ── */
.cb-section-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.65rem;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #64748b;
    margin: 14px 0 8px;
    opacity: 0.8;
}

/* ── Q list buttons ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child button {
    background: transparent !important;
    color: #4b5563 !important;
    border: none !important;
    border-left: 2px solid transparent !important;
    border-radius: 0 8px 8px 0 !important;
    text-align: left !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 8px 10px !important;
    white-space: normal !important;
    height: auto !important;
    min-height: unset !important;
    box-shadow: none !important;
    width: 100% !important;
    line-height: 1.45 !important;
    transition: all 0.15s !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child button:hover {
    background: rgba(238,21,21,0.07) !important;
    color: #1a1a2e !important;
    border-left: 2px solid #EE1515 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stBaseButton-primary"] {
    background: rgba(238,21,21,0.1) !important;
    color: #b91c1c !important;
    border-left: 2px solid #EE1515 !important;
}

/* ── Delete button (Q-list 🗑) — compact icon-only ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child button {
    width: 30px !important;
    min-width: 30px !important;
    max-width: 30px !important;
    height: 30px !important;
    padding: 0 !important;
    font-size: 14px !important;
    border-radius: 6px !important;
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1.5px solid #e2e8f0 !important;
    box-shadow: none !important;
    line-height: 30px !important;
    text-align: center !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child button:hover {
    background: rgba(238,21,21,0.08) !important;
    color: #EE1515 !important;
    border-color: #EE1515 !important;
}

/* ── New chat button (outlined) ── */
.cb-new-btn button {
    background: transparent !important;
    border: 2px solid #EE1515 !important;
    border-radius: 10px !important;
    color: #EE1515 !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    font-family: 'Outfit', sans-serif !important;
    height: 40px !important;
    transition: all 0.2s !important;
    box-shadow: none !important;
}
.cb-new-btn button:hover {
    background: #EE1515 !important;
    color: #fff !important;
    box-shadow: 0 4px 14px rgba(238,21,21,0.35) !important;
}

/* ── Oak avatar — same size/shape as user icon (51px round) ── */
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
    width: 51px !important;
    height: 51px !important;
    border-radius: 50% !important;
    overflow: hidden !important;
    border: 2px solid #e2e8f0 !important;
    flex-shrink: 0 !important;
}
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] img,
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] > span {
    width: 51px !important;
    height: 51px !important;
    object-fit: cover !important;
    object-position: 50% 0% !important;
    font-size: 28px !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    border-radius: 0 !important;
    border: none !important;
    padding: 6px 16px !important;
    margin: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    align-items: flex-start !important;
}
[data-testid="stChatMessage"] .stMarkdown {
    font-size: 14.5px !important;
    line-height: 1.85 !important;
    font-family: 'Inter', sans-serif !important;
    color: #1f2937 !important;
}

/* Assistant message — no bubble, plain markdown */
[data-testid="stChatMessage"] > div:last-child {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 2px 0 4px !important;
    max-width: 85% !important;
}

/* Chat message code/table styling */
[data-testid="stChatMessage"] pre {
    background: #1f2937 !important; color: #e5e7eb;
    border-radius: 10px; padding: 12px 16px; font-size: 13px;
    border: 1px solid #374151;
}
[data-testid="stChatMessage"] code {
    background: rgba(238,21,21,0.08); color: #b91c1c;
    padding: 2px 6px; border-radius: 4px; font-size: 13px;
}
[data-testid="stChatMessage"] pre code { background: transparent; color: inherit; padding: 0; }
[data-testid="stChatMessage"] table {
    border-collapse: collapse; width: 100%;
    font-size: 13px; border-radius: 8px; overflow: hidden; margin: 8px 0;
}
[data-testid="stChatMessage"] th {
    background: #EE1515; color: #fff;
    padding: 8px 12px; font-size: 12px;
}
[data-testid="stChatMessage"] td {
    padding: 7px 12px; border-bottom: 1px solid #f3f4f6;
    color: #374151;
}
[data-testid="stChatMessage"] tr:nth-child(even) td { background: #f9fafb; }
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 { color: #b91c1c; margin: 12px 0 5px; }
[data-testid="stChatMessage"] blockquote {
    border-left: 3px solid #EE1515;
    padding: 6px 12px; margin: 8px 0;
    background: rgba(238,21,21,0.04);
    border-radius: 0 8px 8px 0;
    color: #6b7280;
}

/* ── Chat input — fixed inside right panel ── */
[data-testid="stBottom"],
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 25% !important;
    right: 0 !important;
    background: #ffffff !important;
    border-top: 1px solid #e2e8f0 !important;
    padding: 12px 20px 24px !important;
    z-index: 500 !important;
}

/* 챗 입력기 전체 바 (가장 안쪽 컨테이너만 테두리 부여) */
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 30px !important;
    padding: 2px 2px 2px 12px !important;
    display: flex !important;
    align-items: center !important;
    transition: all 0.2s ease !important;
}

/* 중첩된 내부 div들의 배경/테두리 제거 (중복 방지) */
[data-testid="stChatInput"] > div > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #EE1515 !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(238,21,21,0.1) !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #1a1a2e !important;
    font-size: 14.5px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 0 !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #9ca3af !important; }

[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #EE1515, #c0392b) !important;
    border-radius: 50% !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(238,21,21,0.3) !important;
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
    margin: 4px !important; /* 바 안쪽 여백 */
}
[data-testid="stChatInput"] button:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 4px 14px rgba(238,21,21,0.4) !important;
}
[data-testid="stChatInput"] button svg {
    fill: #ffffff !important;
    color: #ffffff !important;
    stroke: #ffffff !important;
    width: 18px !important;
    height: 18px !important;
}

/* ── Welcome screen ── */
.cb-welcome {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 400px; gap: 16px; padding: 40px;
    text-align: center;
}
.cb-welcome-ball {
    width: 80px; height: 80px;
    background: radial-gradient(circle at 38% 38%, #EE1515 50%, #c0392b 50%);
    border-radius: 50%;
    border: 4px solid #fff;
    position: relative;
    box-shadow: 0 8px 32px rgba(238,21,21,0.3);
    animation: cb-float 3s ease-in-out infinite;
}
.cb-welcome-ball::before {
    content: '';
    position: absolute;
    top: 50%; left: 0; right: 0;
    height: 4px; background: #222;
    transform: translateY(-50%);
}
.cb-welcome-ball::after {
    content: '';
    position: absolute;
    top: 50%; left: 50%;
    width: 18px; height: 18px;
    background: #fff; border: 3px solid #333;
    border-radius: 50%;
    transform: translate(-50%, -50%);
}
@keyframes cb-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
.cb-welcome-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem; font-weight: 900; color: #1a1a2e;
    letter-spacing: 1px;
}
.cb-welcome-sub {
    color: #6b7280;
    font-size: 0.9rem; line-height: 1.7;
}
.cb-welcome-chips {
    display: flex; flex-wrap: wrap;
    gap: 8px; justify-content: center;
    margin-top: 8px;
}
.cb-chip {
    background: #fff;
    border: 1.5px solid #fbd0d0;
    border-radius: 20px; padding: 7px 16px;
    font-size: 12.5px; color: #374151;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 1px 4px rgba(238,21,21,0.08);
}

/* ── Typing animation ── */
@keyframes cb-typing {
    0%, 80%, 100% { transform: scale(0.7); opacity: 0.3; }
    40% { transform: scale(1); opacity: 1; }
}
.cb-thinking {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 20px;
}
.cb-thinking-bubble {
    display: flex; gap: 6px; align-items: center;
    padding: 14px 20px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 4px 18px 18px 18px;
    width: fit-content;
}
.cb-thinking-dot {
    width: 8px; height: 8px;
    border-radius: 50%; background: #EE1515;
    animation: cb-typing 1.4s ease-in-out infinite;
}
.cb-thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.cb-thinking-dot:nth-child(3) { animation-delay: 0.4s; }
.cb-thinking-label {
    font-size: 12px; color: #9ca3af;
    font-family: 'Inter', sans-serif;
    margin-left: 4px;
}

/* ── Scrollbar light ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #fbd0d0; border-radius: 99px; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────

for k, v in {
    "session_id": None,
    "messages": [],
    "model": DEFAULT_MODEL,
    "selected_q": None,
    "is_loading": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.model not in MODELS_LIST:
    st.session_state.model = DEFAULT_MODEL

# ── User ID & Cookie 설정 ─────────────────────────────────────────────────

_cookie = st.session_state.get("cookie_controller")
_user_info = st.session_state.get("user") or {}

if _user_info:
    # 로그인: db_id 또는 github_id 사용
    USER_ID = str(_user_info.get("db_id") or _user_info.get("github_id") or "")
else:
    # 비로그인: 쿠키에서 UUID 복구 또는 신규 발급
    USER_ID = ""
    if _cookie:
        _anon = _cookie.get("anon_user_id")
        if not _anon:
            _anon = str(uuid.uuid4())
            try:
                _cookie.set("anon_user_id", _anon, max_age=30 * 24 * 3600)
            except Exception:
                pass
        USER_ID = _anon or ""

# 이전 session_id 쿠키 복구 → 메시지도 DB에서 즉시 로드
if st.session_state.session_id is None:
    _saved_sid = _cookie.get("cb_session_id") if _cookie else None
    if not _saved_sid and USER_ID:
        # 쿠키 없으면 이 유저의 가장 최근 세션 자동 로드
        _recent = api_sessions(user_id=USER_ID or None)
        if _recent:
            _saved_sid = str(_recent[0]["id"])
    if _saved_sid:
        try:
            _sid = int(_saved_sid)
            st.session_state.session_id = _sid
            if not st.session_state.messages:
                _loaded = api_messages(_sid)
                if _loaded:
                    st.session_state.messages = _loaded
        except Exception:
            pass

# ── Avatars ───────────────────────────────────────────────────────────────

def get_base64_img(file_name):
    # frontend/pages/chatbot.py 위치에서 한 단계 위(frontend)인 프로젝트 루트의 img 폴더 확인
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_path, "img", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

USER_AVATAR = (
    _user_info.get("avatar_url")
    or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png"
)
# 오박사 이미지를 Base64 데이터 URL로 로드하여 유저 아바타(URL)와 통일된 방식으로 처리합니다.
OAK_AVATAR = get_base64_img("Obak_chat.png")

# ── Layout ────────────────────────────────────────────────────────────────

left_col, right_col = st.columns([1, 3], gap="small")

# ═══════════════════════════════════════════════════
# LEFT PANEL
# ═══════════════════════════════════════════════════
with left_col:
    # Header
    st.markdown("""
    <div class="cb-left-header">
        <div class="cb-left-title">
            <div class="cb-pokeball"></div>
            POKÉDEX AI
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 새 채팅 시작 (헤더 바로 아래 최상단)
    st.markdown('<div class="cb-new-btn">', unsafe_allow_html=True)
    if st.button("＋ 새 채팅 시작", use_container_width=True, key="new_chat"):
        if _cookie:
            try:
                _cookie.remove("cb_session_id")
            except Exception:
                pass
        st.session_state.update(session_id=None, messages=[], selected_q=None, is_loading=False)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Model selector
    st.markdown('<div class="cb-section-label" style="margin-top:12px;">모델 선택</div>',
                unsafe_allow_html=True)
    st.session_state.model = st.radio(
        "모델",
        options=MODELS_LIST,
        index=MODELS_LIST.index(st.session_state.model) if st.session_state.model in MODELS_LIST else 0,
        horizontal=True,
        key="model_radio",
    )

    # 대화 기록 (현재 세션 Q 목록 + 삭제)
    user_msgs = [(i, m) for i, m in enumerate(st.session_state.messages) if m["role"] == "user"]
    count = len(user_msgs)
    badge = (
        f' <span style="background:#EE1515;color:#fff;font-size:9px;'
        f'padding:1px 6px;border-radius:10px;">{count}</span>'
        if count else ""
    )
    st.markdown(f'<div class="cb-section-label" style="margin-top:12px;">대화 기록{badge}</div>',
                unsafe_allow_html=True)

    if not user_msgs:
        st.markdown(
            '<div style="font-size:11.5px;color:#9ca3af;padding:10px 4px;line-height:1.8;">'
            '아직 질문이 없어요.<br>아래 입력창으로 시작하세요!</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.session_state.selected_q is not None:
            if st.button("↩ 전체 대화 보기", key="back_all", use_container_width=True):
                st.session_state.selected_q = None
                st.rerun()

        with st.container(height=400, border=False):
            for list_idx, (msg_idx, msg) in enumerate(user_msgs):
                text = msg["content"]
                display = text[:22] + "…" if len(text) > 22 else text
                is_sel = st.session_state.selected_q == msg_idx
                col_q, col_del = st.columns([5, 1])
                with col_q:
                    if st.button(
                        f"Q{list_idx + 1}. {display}",
                        key=f"qlist_{list_idx}",
                        use_container_width=True,
                        help=text,
                        type="primary" if is_sel else "secondary",
                    ):
                        st.session_state.selected_q = None if is_sel else msg_idx
                        st.rerun()
                with col_del:
                    if st.button("🗑", key=f"qdel_{list_idx}"):
                        # 해당 Q와 바로 다음 assistant 응답 함께 삭제
                        to_remove = {msg_idx}
                        for _i in range(msg_idx + 1, len(st.session_state.messages)):
                            if st.session_state.messages[_i]["role"] == "assistant":
                                to_remove.add(_i)
                                break
                        st.session_state.messages = [
                            m for _i, m in enumerate(st.session_state.messages)
                            if _i not in to_remove
                        ]
                        if st.session_state.selected_q in to_remove:
                            st.session_state.selected_q = None
                        st.rerun()

# ═══════════════════════════════════════════════════
# RIGHT PANEL — CHAT AREA
# ═══════════════════════════════════════════════════
with right_col:
    msgs = st.session_state.messages
    selected_q = st.session_state.selected_q
    is_loading = st.session_state.get("is_loading", False)

    # ── Empty state (welcome screen) ──
    if not msgs and not is_loading:
        st.markdown("""
        <div class="cb-welcome">
            <div class="cb-welcome-ball"></div>
            <div class="cb-welcome-title">포켓몬 박사에게 물어보세요!</div>
            <div class="cb-welcome-sub">
                타입 상성 · 스탯 · 진화 경로 · 도감 설명<br>
                무엇이든 답해드립니다
            </div>
            <div class="cb-welcome-chips">
                <span class="cb-chip">⚡ 피카츄의 스탯은?</span>
                <span class="cb-chip">🔥 불꽃 타입 약점</span>
                <span class="cb-chip">🌊 물 타입 추천 포켓몬</span>
                <span class="cb-chip">🐉 드래곤 진화 경로</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Q detail view (single Q&A) ──
    elif selected_q is not None:
        q_num = next(
            (i + 1 for i, (idx, _) in enumerate(user_msgs) if idx == selected_q), "?")
        st.markdown(
            f'<div style="padding:10px 20px;border-bottom:1px solid #f3f4f6;">'
            f'<span style="font-size:12px;color:#9ca3af;">Q{q_num} 보는 중 —</span>'
            f'<span style="font-size:12px;color:#6b7280;margin-left:6px;">'
            f'왼쪽 목록에서 다른 질문 선택 또는 ↩ 전체 대화 클릭</span></div>',
            unsafe_allow_html=True,
        )
        with st.container(height=700, border=False):
            render_user_bubble(msgs[selected_q]["content"], USER_AVATAR)
            for i in range(selected_q + 1, len(msgs)):
                if msgs[i]["role"] == "assistant":
                    with st.chat_message("assistant", avatar=OAK_AVATAR):
                        st.markdown(msgs[i]["content"])
                        render_tool_badges(msgs[i].get("used_tools") or [])
                    break

    # ── Full conversation (scrollable, input pinned bottom) ──
    else:
        with st.container(height=700, border=False):
            for msg in msgs:
                if msg["role"] == "user":
                    render_user_bubble(msg["content"], USER_AVATAR)
                else:
                    with st.chat_message("assistant", avatar=OAK_AVATAR):
                        st.markdown(msg["content"])
                        render_tool_badges(msg.get("used_tools") or [])

            if is_loading:
                st.markdown("""
                <div class="cb-thinking">
                    <div class="cb-thinking-bubble">
                        <div class="cb-thinking-dot"></div>
                        <div class="cb-thinking-dot"></div>
                        <div class="cb-thinking-dot"></div>
                    </div>
                    <span class="cb-thinking-label">포켓몬 박사가 생각 중...</span>
                </div>
                """, unsafe_allow_html=True)

                history = copy.deepcopy(msgs[:-1])
                try:
                    result = api_chat(
                        query=msgs[-1]["content"],
                        history=history,
                        model=st.session_state.model,
                        session_id=st.session_state.session_id,
                        user_id=USER_ID or None,
                    )
                    answer = result["answer"]
                    used_tools = result.get("used_tools", [])
                    st.session_state.session_id = result["session_id"]
                    if _cookie and st.session_state.session_id:
                        try:
                            _cookie.set("cb_session_id",
                                        str(st.session_state.session_id),
                                        max_age=30 * 24 * 3600)
                        except Exception:
                            pass
                except Exception as e:
                    answer = f"⚠️ 오류가 발생했어요 ({type(e).__name__}): {e}"
                    used_tools = []

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "used_tools": used_tools,
                })
                st.session_state.is_loading = False
                st.rerun()

    pass  # right panel end

# ── Chat input — columns 밖에 배치, CSS로 우측 패널 하단 고정 ──
if prompt := st.chat_input("포켓몬에 대해 무엇이든 물어보세요... ⚡"):
    st.session_state.selected_q = None
    st.session_state.messages.append({"role": "user", "content": prompt, "used_tools": []})
    st.session_state.is_loading = True
    st.rerun()
