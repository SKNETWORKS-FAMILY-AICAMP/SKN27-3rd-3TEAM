import streamlit as st

import os
import copy
import uuid
import html as _html
import requests
import base64
import streamlit as st

sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys; sys.path.append(sys_path)
from utils.ui import inject_common_ui

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080")

# ── API helpers ───────────────────────────────────────────────────────────

def _get(path, params=None):
    return requests.get(f"{BACKEND_URL}{path}", params=params, timeout=10)

def _post(path, **kwargs):
    return requests.post(f"{BACKEND_URL}{path}", timeout=180, **kwargs)

def _delete(path):
    return requests.delete(f"{BACKEND_URL}{path}", timeout=10)

def _patch(path, **kwargs):
    return requests.patch(f"{BACKEND_URL}{path}", timeout=10, **kwargs)

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

def api_delete_session(session_id):
    try:
        _delete(f"/api/v1/chatbot/sessions/{session_id}")
    except Exception:
        pass

def api_rename_session(session_id, title):
    try:
        _patch(f"/api/v1/chatbot/sessions/{session_id}", params={"title": title})
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

def render_user_bubble(content: str, avatar_url: str) -> None:
    escaped = _html.escape(content)
    st.markdown(
        f'<div style="display:flex;justify-content:flex-end;align-items:flex-start;'
        f'gap:12px;padding:8px 16px;margin-bottom:8px;">'
        f'<div style="background:linear-gradient(135deg,#EE1515 0%,#c0392b 100%);'
        f'color:#fff;padding:12px 16px;border-radius:18px 4px 18px 18px;'
        f'font-size:14.5px;line-height:1.75;font-family:Inter,sans-serif;'
        f'box-shadow:0 4px 14px rgba(238,21,21,0.22);word-break:break-word;'
        f'white-space:pre-wrap;max-width:80%;">{escaped}</div>'
        f'<img src="{avatar_url}" style="width:48px;height:48px;border-radius:50%;'
        f'flex-shrink:0;object-fit:cover;border:2px solid #e2e8f0;"></div>',
        unsafe_allow_html=True,
    )

def render_assistant_bubble(content: str, avatar_url: str, used_tools: list = None) -> None:
    # 툴 배지 HTML 생성
    tool_html = ""
    if used_tools:
        badges = []
        for t in used_tools:
            badges.append(f'<span style="background:#f1f5f9;color:#475569;font-size:11px;padding:3px 8px;border-radius:6px;border:1px solid #e2e8f0;font-weight:600;">🛠️ {t}</span>')
        tool_html = f'<div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;">{"".join(badges)}</div>'

    st.markdown(
        f'<div style="display:flex;justify-content:flex-start;align-items:flex-start;'
        f'gap:12px;padding:12px 16px;margin-bottom:24px;overflow:visible;">'
        f'<img src="{avatar_url}" style="width:48px;height:48px;border-radius:50%;'
        f'flex-shrink:0;object-fit:contain;border:2px solid #e2e8f0;background:#fff;">'
        f'<div style="flex:1;max-width:85%;">'
        f'<div style="background:#f8fafc;color:#1e293b;padding:16px 20px;'
        f'border-radius:4px 22px 22px 22px;font-size:14.5px;line-height:1.85;'
        f'font-family:Inter,sans-serif;border:1px solid #e2e8f0;'
        f'box-shadow:0 2px 10px rgba(0,0,0,0.03);white-space:pre-wrap;">{content}</div>'
        f'{tool_html}</div></div>',
        unsafe_allow_html=True,
    )

# ── Page config ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="포켓몬 비공식 AI 박사",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_common_ui(spacer=True, hide_sidebar=True)

# ── CSS ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;500;600;700&display=swap');

/* ── 전체 레이아웃 고정 ── */
html, body { overflow: hidden !important; }
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section[data-testid="stMain"],
.stMain {
    background: #ffffff !important;
    height: 100vh !important;
    overflow: hidden !important;
}
.block-container {
    background: #ffffff !important;
    padding: 0 !important;
    max-width: 100% !important;
    height: 100vh !important;
    overflow: hidden !important;
}

/* ── 최상위 columns를 full-height stretch (메인 레이아웃 전용) ── */
[data-testid="stAppViewBlockContainer"] > div > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}

/* 다이얼로그 내 버튼 늘어남 방지 */
[data-testid="stDialog"] [data-testid="stHorizontalBlock"] {
    align-items: flex-start !important;
}

/* ── 왼쪽 패널 (커스텀 사이드바) ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
    background: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
    height: calc(100vh - 50px) !important;
    overflow: hidden !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    > [data-testid="stVerticalBlock"] {
    padding: 0 14px 14px !important;
    height: 100% !important;
    overflow-y: auto !important;
}

/* ── 오른쪽 패널 (채팅 영역) ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
    background: #ffffff !important;
    height: calc(100vh - 50px) !important;
    overflow: hidden !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
    > [data-testid="stVerticalBlock"] {
    padding: 0 0 180px 0 !important;
    height: 100% !important;
    overflow: hidden !important;
}

/* ── 왼쪽 패널 내부 중첩 columns 초기화 ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    background: transparent !important;
    min-height: unset !important;
    border: none !important;
    height: auto !important;
}

/* ── 왼쪽 헤더 ── */
.cb-left-header {
    padding: 18px 0 14px;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 14px;
}
.cb-left-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 900;
    color: #1a1a2e;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.cb-pokeball {
    width: 26px; height: 26px;
    background: radial-gradient(circle at 38% 38%, #EE1515 50%, #c0392b 50%);
    border-radius: 50%;
    border: 2px solid #fff;
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

/* ── 섹션 레이블 ── */
.cb-section-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.9rem;
    font-weight: 900;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #475569;
    margin: 18px 0 10px;
    opacity: 0.9;
}

/* ── 새 채팅 버튼 ── */
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

/* ── 모델 선택 radio ── */
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
    padding: 5px 10px !important;
    font-size: 11px !important;
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
    background: #ffffff !important;
    color: #1e293b !important;
    font-weight: 900 !important;
    border: 2px solid #1e293b !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
    transform: scale(1.02) !important;
}
[data-testid="stRadio"] label input {
    position: absolute !important; opacity: 0 !important;
    width: 1px !important; height: 1px !important;
}
div:has(> [data-testid="stRadio"]) { margin: 8px 0 !important; padding: 0 !important; }

/* ── 세션 목록 — 제목 버튼 ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child button {
    background: transparent !important;
    color: #4b5563 !important;
    border: none !important;
    border-left: 2px solid transparent !important;
    border-radius: 0 8px 8px 0 !important;
    text-align: left !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 7px 10px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    height: auto !important;
    min-height: 32px !important;
    box-shadow: none !important;
    width: 100% !important;
    line-height: 1.4 !important;
    transition: all 0.15s !important;
    display: block !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child button:hover {
    background: rgba(238,21,21,0.07) !important;
    color: #1a1a2e !important;
    border-left: 2px solid #EE1515 !important;
}
/* 활성 세션 (primary type) */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stBaseButton-primary"] {
    background: rgba(238,21,21,0.10) !important;
    color: #b91c1c !important;
    border-left: 2px solid #EE1515 !important;
    font-weight: 700 !important;
}

/* ── 세션 목록 — 편집/삭제 아이콘 버튼 ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) button,
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) button {
    width: 28px !important;
    min-width: 28px !important;
    max-width: 28px !important;
    height: 28px !important;
    min-height: 28px !important;
    padding: 0 !important;
    font-size: 12px !important;
    border-radius: 6px !important;
    background: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: none !important;
    opacity: 0 !important;
    transition: opacity 0.2s !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"]:hover > [data-testid="stColumn"]:nth-child(2) button,
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"]:hover > [data-testid="stColumn"]:nth-child(3) button {
    opacity: 1 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) button:hover,
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) button:hover {
    background: rgba(238,21,21,0.08) !important;
    color: #EE1515 !important;
    border-color: #EE1515 !important;
    opacity: 1 !important;
}

/* ── 오박사 아바타 & 메시지 간격 최적화 ── */
[data-testid="stChatMessage"] {
    gap: 15px !important;
    padding: 20px 0 !important;
    margin: 0 !important;
    background: transparent !important;
    min-height: 100px !important;
    display: flex !important;
    align-items: flex-start !important;
    overflow: visible !important;
}

/* ── 오박사 아바타 2배 확대 (컨테이너 포함 강제) ── */
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessage"] [data-avatar="assistant"] {
    width: 92px !important;
    height: 92px !important;
    min-width: 92px !important;
    flex-basis: 92px !important;
}

[data-testid="stChatMessage"] [data-testid="stChatAvatarImage"],
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] img {
    width: 100% !important;
    height: 100% !important;
    border: 3px solid #e2e8f0 !important;
    border-radius: 50% !important;
    object-fit: contain !important;
    background: #fff !important;
}

/* 아바타와 텍스트 레이아웃 정렬 */
[data-testid="stChatMessage"] > div:first-child {
    width: 92px !important;
    min-width: 92px !important;
    margin-right: 15px !important;
}

[data-testid="stChatMessage"] .stMarkdown {
    font-size: 14.5px !important;
    line-height: 1.85 !important;
    font-family: 'Inter', sans-serif !important;
    color: #1f2937 !important;
    padding-top: 10px !important;
}

[data-testid="stChatMessage"] .stMarkdown {
    font-size: 14.5px !important;
    line-height: 1.85 !important;
    font-family: 'Inter', sans-serif !important;
    color: #1f2937 !important;
}

[data-testid="stChatMessage"] > div:last-child {
    background: transparent !important;
    padding: 0 !important;
    max-width: 88% !important;
}
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
    border-collapse: collapse; width: 100%; font-size: 13px; margin: 8px 0;
}
[data-testid="stChatMessage"] th { background: #EE1515; color: #fff; padding: 8px 12px; font-size: 12px; }
[data-testid="stChatMessage"] td { padding: 7px 12px; border-bottom: 1px solid #f3f4f6; color: #374151; }
[data-testid="stChatMessage"] tr:nth-child(even) td { background: #f9fafb; }
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 { color: #b91c1c; margin: 12px 0 5px; }
[data-testid="stChatMessage"] blockquote {
    border-left: 3px solid #EE1515; padding: 6px 12px; margin: 8px 0;
    background: rgba(238,21,21,0.04); border-radius: 0 8px 8px 0; color: #6b7280;
}

/* ── 채팅 입력창 — 우측 패널 하단 고정 ── */
[data-testid="stBottom"],
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 20% !important;
    right: 0 !important;
    background: #ffffff !important;
    border-top: none !important;
    padding: 15px 25px 30px !important;
    z-index: 500 !important;
}
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 35px !important;
    padding: 2px 2px 2px 12px !important;
    display: flex !important; align-items: center !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] > div:focus-within {
    background: #ffffff !important;
    border-color: #EE1515 !important;
    box-shadow: 0 4px 20px rgba(238,21,21,0.1) !important;
}
[data-testid="stChatInput"] > div > div {
    background: #ffffff !important; border: none !important; box-shadow: none !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(238,21,21,0.10) !important;
}
[data-testid="stChatInput"] textarea {
    background: #ffffff !important; border: none !important; box-shadow: none !important;
    color: #1a1a2e !important; font-size: 14.5px !important;
    font-family: 'Inter', sans-serif !important; padding: 10px 0 !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #9ca3af !important; }
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #EE1515, #c0392b) !important;
    border-radius: 50% !important;
    border: none !important;
    outline: none !important;
    box-shadow: 0 2px 8px rgba(238,21,21,0.3) !important;
    width: 38px !important; height: 38px !important; min-width: 38px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    margin: 4px !important; transition: all 0.2s !important;
}
[data-testid="stChatInput"] button:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 4px 14px rgba(238,21,21,0.4) !important;
}
[data-testid="stChatInput"] button:focus,
[data-testid="stChatInput"] button:active,
[data-testid="stChatInput"] button:focus-visible {
    outline: none !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(238,21,21,0.4) !important;
}
[data-testid="stChatInput"] button svg {
    fill: #fff !important; color: #fff !important;
    stroke: none !important; stroke-width: 0 !important;
    width: 18px !important; height: 18px !important;
}

/* ── 웰컴 스크린 ── */
.cb-welcome {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 65vh; gap: 16px; padding: 40px; text-align: center;
}
.cb-welcome-ball {
    width: 80px; height: 80px;
    background: radial-gradient(circle at 38% 38%, #EE1515 50%, #c0392b 50%);
    border-radius: 50%; border: 4px solid #fff;
    position: relative; box-shadow: 0 8px 32px rgba(238,21,21,0.3);
    animation: cb-float 3s ease-in-out infinite;
}
.cb-welcome-ball::before {
    content: ''; position: absolute;
    top: 50%; left: 0; right: 0; height: 4px; background: #222;
    transform: translateY(-50%);
}
.cb-welcome-ball::after {
    content: ''; position: absolute;
    top: 50%; left: 50%; width: 18px; height: 18px;
    background: #fff; border: 3px solid #333; border-radius: 50%;
    transform: translate(-50%, -50%);
}
@keyframes cb-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
.cb-welcome-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem; font-weight: 900; color: #1a1a2e; letter-spacing: 1px;
}
.cb-welcome-sub { color: #6b7280; font-size: 0.9rem; line-height: 1.7; }
.cb-welcome-chips {
    display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 8px;
}
.cb-chip {
    background: #fff; border: 1.5px solid #fbd0d0; border-radius: 20px;
    padding: 7px 16px; font-size: 12.5px; color: #374151;
    box-shadow: 0 1px 4px rgba(238,21,21,0.08);
}

/* ── 로딩 애니메이션 ── */
@keyframes cb-typing {
    0%, 80%, 100% { transform: scale(0.7); opacity: 0.3; }
    40% { transform: scale(1); opacity: 1; }
}
.cb-thinking { display: flex; align-items: center; gap: 10px; padding: 10px 20px; }
.cb-thinking-bubble {
    display: flex; gap: 6px; align-items: center;
    padding: 14px 20px; background: #f9fafb;
    border: 1px solid #e5e7eb; border-radius: 4px 18px 18px 18px; width: fit-content;
}
.cb-thinking-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #EE1515;
    animation: cb-typing 1.4s ease-in-out infinite;
}
.cb-thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.cb-thinking-dot:nth-child(3) { animation-delay: 0.4s; }
.cb-thinking-label { font-size: 12px; color: #9ca3af; font-family: 'Inter', sans-serif; margin-left: 4px; }

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #fbd0d0; border-radius: 99px; }
</style>
""", unsafe_allow_html=True)

# ── Dialogs ───────────────────────────────────────────────────────────────

@st.dialog("✏️ 대화 이름 수정")
def show_rename_dialog(chat_id: int, current_title: str):
    st.write(f"현재 이름: **{current_title}**")
    new_title = st.text_input("새 이름", value=current_title, key="rename_input")
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("저장", type="primary", use_container_width=True, key="rename_save"):
            if new_title.strip():
                api_rename_session(chat_id, new_title.strip())
                for c in st.session_state.chat_history:
                    if c["id"] == chat_id:
                        c["title"] = new_title.strip()
                        break
                st.rerun()
            else:
                st.warning("이름을 입력해주세요.")
    with col_cancel:
        if st.button("취소", use_container_width=True, key="rename_cancel"):
            st.rerun()


@st.dialog("🗑️ 대화 삭제 확인")
def show_delete_dialog(chat_id: int, chat_title: str):
    st.warning(f"**'{chat_title}'** 대화를 삭제할까요?")
    st.write("이 작업은 되돌릴 수 없으며 대화 내용이 모두 사라집니다.")
    col_del, col_cancel = st.columns(2)
    with col_del:
        if st.button("삭제", type="primary", use_container_width=True, key="delete_confirm"):
            api_delete_session(chat_id)
            st.session_state.chat_history = [
                c for c in st.session_state.chat_history if c["id"] != chat_id
            ]
            if st.session_state.current_chat_id == chat_id:
                if st.session_state.chat_history:
                    new_id = st.session_state.chat_history[0]["id"]
                    st.session_state.current_chat_id = new_id
                    st.session_state.messages = api_messages(new_id)
                else:
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
            st.rerun()
    with col_cancel:
        if st.button("취소", use_container_width=True, key="delete_cancel"):
            st.rerun()

# ── Session state init ─────────────────────────────────────────────────────

for k, v in {
    "current_chat_id": None,
    "messages": [],
    "chat_history": [],
    "model": DEFAULT_MODEL,
    "is_loading": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.model not in MODELS_LIST:
    st.session_state.model = DEFAULT_MODEL

# ── User ID & Cookie ───────────────────────────────────────────────────────

_cookie = st.session_state.get("cookie_controller")
_user_info = st.session_state.get("user") or {}

if _user_info:
    USER_ID = str(_user_info.get("db_id") or _user_info.get("github_id") or "")
else:
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

# ── Data sync: 최초 렌더링 시 세션 목록 전체 로드 ─────────────────────────

if not st.session_state.chat_history:
    _sessions = api_sessions(user_id=USER_ID or None)
    if _sessions:
        st.session_state.chat_history = _sessions
        if st.session_state.current_chat_id is None:
            _first_id = _sessions[0]["id"]
            st.session_state.current_chat_id = _first_id
            if not st.session_state.messages:
                st.session_state.messages = api_messages(_first_id)

# ── Avatars ───────────────────────────────────────────────────────────────

def get_base64_img(file_name: str) -> str:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_path, "img", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

USER_AVATAR = (
    _user_info.get("avatar_url")
    or get_base64_img("지우.png")
    or "https://cdn-icons-png.flaticon.com/512/188/188987.png"
)
OAK_AVATAR = get_base64_img("Obak_chat.png")

# ═══════════════════════════════════════════════════════
# 레이아웃 — 커스텀 사이드바(left) + 채팅(right)
# ═══════════════════════════════════════════════════════

left_col, right_col = st.columns([1, 4], gap="small")

# ───────────────────────────────────────────────────────
# 왼쪽 패널 (커스텀 사이드바)
# ───────────────────────────────────────────────────────
with left_col:
    st.markdown("""
    <div class="cb-left-header">
        <div class="cb-left-title">
            <div class="cb-pokeball"></div>
            POKÉDEX AI
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 새 채팅 버튼
    st.markdown('<div class="cb-new-btn">', unsafe_allow_html=True)
    if st.button("＋ 새 채팅 시작", use_container_width=True, key="new_chat"):
        st.session_state.update(current_chat_id=None, messages=[], is_loading=False)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # 모델 선택
    st.markdown('<div class="cb-section-label" style="margin-top:12px;">모델 선택</div>',
                unsafe_allow_html=True)
    st.session_state.model = st.radio(
        "모델",
        options=MODELS_LIST,
        index=MODELS_LIST.index(st.session_state.model) if st.session_state.model in MODELS_LIST else 0,
        horizontal=True,
        key="model_radio",
    )

    # 대화 목록
    count = len(st.session_state.chat_history)
    badge = (
        f' <span style="background:#EE1515;color:#fff;font-size:11px;'
        f'padding:2px 8px;border-radius:12px;font-weight:900;vertical-align:middle;">{count}</span>'
        if count else ""
    )
    st.markdown(f'<div class="cb-section-label" style="margin-top:12px;">대화 목록{badge}</div>',
                unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.markdown(
            '<div style="font-size:11.5px;color:#9ca3af;padding:10px 4px;line-height:1.8;">'
            '대화 기록이 없습니다.<br>새 채팅을 시작하세요!</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.container(height=420, border=False):
            for chat in st.session_state.chat_history:
                chat_id = chat["id"]
                chat_title = chat.get("title") or f"대화 #{chat_id}"
                is_active = chat_id == st.session_state.current_chat_id

                col_t, col_e, col_d = st.columns([6, 1, 1])
                with col_t:
                    if st.button(
                        chat_title,
                        key=f"chat_{chat_id}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                    ):
                        if not is_active:
                            st.session_state.current_chat_id = chat_id
                            st.session_state.messages = api_messages(chat_id)
                            st.session_state.is_loading = False
                            st.rerun()
                with col_e:
                    if st.button("✏️", key=f"edit_{chat_id}", help="이름 수정"):
                        show_rename_dialog(chat_id, chat_title)
                with col_d:
                    if st.button("🗑️", key=f"del_{chat_id}", help="삭제"):
                        show_delete_dialog(chat_id, chat_title)

# ───────────────────────────────────────────────────────
# 오른쪽 패널 (채팅 영역)
# ───────────────────────────────────────────────────────
with right_col:
    msgs = st.session_state.messages
    is_loading = st.session_state.get("is_loading", False)

    # 웰컴 스크린
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
                <span class="cb-chip">피카츄의 스탯은?</span>
                <span class="cb-chip">불꽃 타입 약점</span>
                <span class="cb-chip">물 타입 추천 포켓몬</span>
                <span class="cb-chip">파이리 진화 경로</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 채팅 메시지
    else:
        with st.container(height=700, border=False):
            for msg in msgs:
                if msg["role"] == "user":
                    render_user_bubble(msg["content"], USER_AVATAR)
                else:
                    render_assistant_bubble(msg["content"], OAK_AVATAR, msg.get("used_tools"))
            
            # 하단 입력창에 가려지지 않도록 여백 추가
            st.markdown('<div style="height: 200px;"></div>', unsafe_allow_html=True)

            if is_loading:
                st.markdown(
                    f'<div style="display:flex;justify-content:flex-start;align-items:flex-start;'
                    f'gap:12px;padding:12px 16px;margin-bottom:12px;">'
                    f'<img src="{OAK_AVATAR}" style="width:48px;height:48px;border-radius:50%;'
                    f'flex-shrink:0;object-fit:contain;border:2px solid #e2e8f0;background:#fff;">'
                    f'<div style="flex:1;">'
                    f'<div class="cb-thinking-bubble">'
                    f'    <div class="cb-thinking-dot"></div>'
                    f'    <div class="cb-thinking-dot"></div>'
                    f'    <div class="cb-thinking-dot"></div>'
                    f'</div>'
                    f'<span class="cb-thinking-label">포켓몬 박사가 생각 중...</span>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )

                history = copy.deepcopy(msgs[:-1])
                try:
                    result = api_chat(
                        query=msgs[-1]["content"],
                        history=history,
                        model=st.session_state.model,
                        session_id=st.session_state.current_chat_id,
                        user_id=USER_ID or None,
                    )
                    answer = result["answer"]
                    used_tools = result.get("used_tools", [])
                    new_sid = result["session_id"]

                    st.session_state.current_chat_id = new_sid

                    # 새 세션 생성 시 목록 갱신
                    if new_sid not in {c["id"] for c in st.session_state.chat_history}:
                        refreshed = api_sessions(user_id=USER_ID or None)
                        if refreshed:
                            st.session_state.chat_history = refreshed
                        else:
                            first_q = msgs[0]["content"][:30] if msgs else f"대화 #{new_sid}"
                            st.session_state.chat_history.insert(0, {"id": new_sid, "title": first_q})

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

# ── 채팅 입력 (CSS로 우측 패널 하단 고정) ──────────────────────────────────

if prompt := st.chat_input("포켓몬에 대해 무엇이든 물어보세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "used_tools": []})
    st.session_state.is_loading = True
    st.rerun()
