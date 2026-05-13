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
from chatbot.styles import inject_chatbot_styles

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
MODEL_DISPLAY_NAMES = {
    "gpt-4o-mini": "빠른 모델",
    "gemma4:e2b": "사고 모델"
}

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
# ── CSS ───────────────────────────────────────────────────────────────────

inject_chatbot_styles()


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
        format_func=lambda x: MODEL_DISPLAY_NAMES.get(x, x),
        index=MODELS_LIST.index(st.session_state.model) if st.session_state.model in MODELS_LIST else 0,
        horizontal=True,
        key="model_radio",
        label_visibility="collapsed"
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
        with st.container(border=False):
            chat_options = [None] + [chat["id"] for chat in st.session_state.chat_history]
            
            def chat_format(x):
                if x is None:
                    return "✨ 새 채팅"
                return next((c.get("title") or f"대화 #{c['id']}") for c in st.session_state.chat_history if c["id"] == x)
            
            # current_chat_id에 맞는 인덱스 찾기
            current_idx = 0
            if st.session_state.current_chat_id in chat_options:
                current_idx = chat_options.index(st.session_state.current_chat_id)
                
            selected_chat_id = st.selectbox(
                "대화 선택",
                options=chat_options,
                format_func=chat_format,
                index=current_idx,
                label_visibility="collapsed",
                key="chat_history_select"
            )
            
            if selected_chat_id != st.session_state.current_chat_id:
                st.session_state.current_chat_id = selected_chat_id
                st.session_state.messages = api_messages(selected_chat_id) if selected_chat_id else []
                st.session_state.is_loading = False
                st.rerun()

            col_e, col_d = st.columns(2)
            with col_e:
                # 새 채팅 상태(None)일 때는 수정/삭제 비활성화
                btn_disabled = (selected_chat_id is None)
                if st.button("✏️ 이름 수정", key="btn_rename_current", use_container_width=True, disabled=btn_disabled):
                    show_rename_dialog(selected_chat_id, chat_format(selected_chat_id))
            with col_d:
                if st.button("🗑️ 삭제", key="btn_delete_current", use_container_width=True, disabled=btn_disabled):
                    show_delete_dialog(selected_chat_id, chat_format(selected_chat_id))

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
