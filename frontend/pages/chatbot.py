import os
import sys
import copy
import requests
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080")

# ── 백엔드 API 헬퍼 ──────────────────────────────────────────
def _get(path):
    return requests.get(f"{BACKEND_URL}{path}", timeout=10)

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

def api_chat(query, history, model, session_id=None):
    r = _post("/api/v1/chatbot/chat", json={
        "query": query, "history": history,
        "model": model, "session_id": session_id,
    })
    r.raise_for_status()
    return r.json()   # {answer, used_tools, session_id}

def api_sessions():
    try:
        return _get("/api/v1/chatbot/sessions").json()
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

def render_tool_badges(tools: list) -> None:
    if not tools:
        return
    TOOL_COLORS = {
        "search_pokemon_db":      ("#3B4CCA", "#e8edff"),
        "search_flavor_text":     ("#7c3aed", "#f3e8ff"),
        "search_evolution_chain": ("#059669", "#d1fae5"),
        "search_type_relations":  ("#d97706", "#fef3c7"),
        "web_search":             ("#6b7280", "#f3f4f6"),
    }
    TOOL_LABELS = {
        "search_pokemon_db":      "DB 검색",
        "search_flavor_text":     "도감 검색",
        "search_evolution_chain": "진화 체인",
        "search_type_relations":  "타입 상성",
        "web_search":             "웹 검색",
    }
    badges = []
    for t in tools:
        color, bg = TOOL_COLORS.get(t, ("#64748b", "#f1f5f9"))
        label = TOOL_LABELS.get(t, t)
        badges.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'background:{bg};color:{color};border:1px solid {color}33;'
            f'border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700;'
            f'letter-spacing:0.3px;margin-right:4px;">'
            f'⚙ {label}</span>'
        )
    st.markdown(
        '<div style="margin-top:6px;line-height:2;">' + "".join(badges) + "</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 박사 챗봇",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_common_ui(spacer=True, hide_sidebar=False)

# ── Pokemon Theme CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

[data-testid="stRadio"] [data-testid="stWidgetLabel"] { display: none !important; }
[data-testid="stRadio"] > div {
    flex-direction: row !important;
    gap: 6px !important;
    background: rgba(255,255,255,0.06);
    border-radius: 30px;
    padding: 4px 6px;
    border: 1.5px solid rgba(255,255,255,0.15);
    display: inline-flex !important;
}
[data-testid="stRadio"] label {
    background: transparent !important;
    border: none !important;
    border-radius: 22px !important;
    padding: 6px 22px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    color: rgba(255,255,255,0.45) !important;
    white-space: nowrap !important;
    box-shadow: none !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #EE1515 0%, #c0392b 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 3px 12px rgba(238,21,21,0.45) !important;
}
[data-testid="stRadio"] label input {
    position: absolute !important; opacity: 0 !important;
    width: 1px !important; height: 1px !important;
}
div:has(> [data-testid="stRadio"]) {
    margin-top: -6px !important; margin-bottom: 4px !important; padding: 0 !important;
}

.block-container [data-testid="stHorizontalBlock"] {
    gap: 0 !important; align-items: stretch !important;
    border-radius: 20px; overflow: hidden; border: none !important;
    box-shadow: 0 8px 40px rgba(26,31,58,0.18), 0 2px 8px rgba(0,0,0,0.06);
    margin-top: 0;
}
.block-container [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:first-child {
    background: linear-gradient(175deg, #1a1f3a 0%, #111827 100%);
    border-right: 3px solid #EE1515; min-height: 620px;
}
.block-container [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:first-child button {
    background: transparent !important; color: #64748b !important;
    border: none !important; border-bottom: 1px solid rgba(255,255,255,0.04) !important;
    border-radius: 0 !important; border-left: 3px solid transparent !important;
    text-align: left !important; font-size: 12.5px !important; line-height: 1.5 !important;
    padding: 10px 14px 10px 13px !important; white-space: normal !important;
    height: auto !important; min-height: unset !important; box-shadow: none !important;
    transition: all 0.15s !important; width: 100% !important;
}
.block-container [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:first-child button:hover {
    background: rgba(238,21,21,0.08) !important; color: #94a3b8 !important;
    border-left: 3px solid rgba(238,21,21,0.3) !important;
}
.block-container [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:first-child [data-testid="stBaseButton-primary"] {
    background: rgba(238,21,21,0.12) !important; color: #fca5a5 !important;
    border-left: 3px solid #EE1515 !important;
}
.block-container [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:last-child {
    background: #f8f9ff; min-height: 620px;
}
.q-panel-header {
    padding: 14px 16px 10px; border-bottom: 1px solid rgba(255,255,255,0.07);
    color: #475569; font-size: 10px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase;
}
.q-empty { padding: 32px 14px; color: #334155; font-size: 12px; text-align: center; line-height: 1.9; }

[data-testid="stChatMessage"] {
    border-radius: 12px; border: 1px solid #e2e8f0;
    padding: 12px 16px !important; margin-bottom: 8px;
    background: #ffffff; box-shadow: 0 1px 6px rgba(59,76,202,0.06);
}
[data-testid="stChatMessage"] .stMarkdown { font-size: 15px; line-height: 1.8; }
[data-testid="stChatMessage"] pre {
    background: #1a1f3a; color: #cdd6f4; border-radius: 10px;
    padding: 14px 18px; overflow-x: auto; font-size: 13px; margin: 10px 0;
}
[data-testid="stChatMessage"] code {
    background: #fdf2f8; color: #c026d3; padding: 2px 6px; border-radius: 4px; font-size: 13px;
}
[data-testid="stChatMessage"] pre code { background: transparent; color: inherit; padding: 0; }
[data-testid="stChatMessage"] table {
    border-collapse: collapse; width: 100%; margin: 12px 0;
    font-size: 14px; border-radius: 8px; overflow: hidden;
}
[data-testid="stChatMessage"] th {
    background: #3B4CCA; color: #fff;
    padding: 9px 14px; text-align: left; font-weight: 700; font-size: 13px;
}
[data-testid="stChatMessage"] td { padding: 8px 14px; border-bottom: 1px solid #e5e7eb; }
[data-testid="stChatMessage"] tr:nth-child(even) td { background: #f0f4ff; }
[data-testid="stChatMessage"] tr:hover td { background: #e8edff; }
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 { color: #3B4CCA; margin: 14px 0 6px; }
[data-testid="stChatMessage"] ul,
[data-testid="stChatMessage"] ol { padding-left: 22px; }
[data-testid="stChatMessage"] li { margin: 4px 0; }
[data-testid="stChatMessage"] blockquote {
    border-left: 4px solid #FFCB05; padding: 8px 14px;
    color: #555; margin: 10px 0; background: #fffbeb;
    border-radius: 0 8px 8px 0; font-style: italic;
}
[data-testid="stChatMessage"] hr { border: none; border-top: 1px solid #e5e7eb; margin: 12px 0; }

[data-testid="stChatInput"] textarea {
    border-radius: 25px !important; border: 2px solid #c7d2fe !important;
    background: #ffffff !important; font-size: 14px !important;
    padding: 12px 22px !important; transition: all 0.2s !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #3B4CCA !important;
    box-shadow: 0 0 0 3px rgba(59,76,202,0.15) !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #EE1515, #c0392b) !important;
    border-radius: 50% !important; border: none !important;
    box-shadow: 0 2px 8px rgba(238,21,21,0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 ─────────────────────────────────────────────────
for k, v in {"session_id": None, "messages": [], "model": DEFAULT_MODEL, "selected_q": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# DEFAULT_MODEL 변경 시 session_state 동기화
if st.session_state.model not in MODELS_LIST:
    st.session_state.model = DEFAULT_MODEL

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🔴 포켓몬 챗봇")

    if st.button("➕ 새 대화", use_container_width=True):
        st.session_state.update(session_id=None, messages=[], selected_q=None)
        st.rerun()

    st.divider()
    st.caption("이전 대화")

    for s in api_sessions():
        # created_at은 ISO 문자열로 옴 ("2024-01-15T10:30:00")
        created = s["created_at"][:16].replace("T", " ")
        is_current = st.session_state.session_id == s["id"]
        label = f"{'▶ ' if is_current else ''}{s['title']}"

        col_btn, col_del = st.columns([6, 1])
        with col_btn:
            if st.button(label, key=f"sess_{s['id']}",
                         help=f"{s['model']} · {created}", use_container_width=True):
                st.session_state.update(
                    session_id=s["id"], model=s["model"],
                    messages=api_messages(s["id"]), selected_q=None,
                )
                st.rerun()
        with col_del:
            if st.button("🗑", key=f"del_{s['id']}"):
                api_delete(s["id"])
                if st.session_state.session_id == s["id"]:
                    st.session_state.update(session_id=None, messages=[], selected_q=None)
                st.rerun()

# ── 최상단 헤더 바 ────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, #1a1f3a 0%, #2d1f5e 50%, #1a1f3a 100%);
    border-radius: 16px; padding: 14px 24px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(26,31,58,0.25);
    border: 1px solid rgba(255,255,255,0.08);
">
    <div style="display:flex; align-items:center; gap:14px;">
        <div style="
            width:42px; height:42px;
            background: radial-gradient(circle at 35% 35%, #EE1515 50%, #c0392b 50%);
            border-radius: 50%; border: 3px solid #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3); position: relative; flex-shrink: 0;
        ">
            <div style="position:absolute; top:50%; left:0; right:0;
                height:3px; background:#111; transform:translateY(-50%);"></div>
            <div style="position:absolute; top:50%; left:50%;
                width:10px; height:10px; background:#fff; border:2px solid #333;
                border-radius:50%; transform:translate(-50%,-50%);"></div>
        </div>
        <div>
            <div style="font-size:20px; font-weight:900; color:#ffffff;
                        letter-spacing:1px; font-family:'Black Han Sans',sans-serif;">
                POKÉDEX AI
            </div>
            <div style="font-size:11px; color:rgba(255,255,255,0.4); letter-spacing:0.5px;">
                포켓몬 박사와 대화하세요
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 모델 선택
st.session_state.model = st.radio(
    "모델",
    options=MODELS_LIST,
    index=MODELS_LIST.index(st.session_state.model) if st.session_state.model in MODELS_LIST else 0,
    horizontal=True,
    key="model_radio",
)

# ── 메인 레이아웃 ─────────────────────────────────────────────
left_col, right_col = st.columns([1, 3])

# ─── 왼쪽: 질문 목록 ─────────────────────────────────────────
with left_col:
    user_msgs = [
        (i, m) for i, m in enumerate(st.session_state.messages)
        if m["role"] == "user"
    ]
    count = len(user_msgs)
    badge = (
        f'<span style="background:#EE1515;color:#fff;font-size:9px;'
        f'padding:1px 7px;border-radius:10px;margin-left:6px;">{count}</span>'
        if count else ""
    )
    st.markdown(f'<div class="q-panel-header">🗂 질문 목록{badge}</div>', unsafe_allow_html=True)

    if not user_msgs:
        st.markdown(
            '<div class="q-empty">🔴<br>아직 질문이 없습니다.<br>아래 입력창에서<br>대화를 시작하세요!</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.session_state.selected_q is not None:
            if st.button("↩ 전체 대화", key="back_all", use_container_width=True):
                st.session_state.selected_q = None
                st.rerun()

        with st.container(height=500, border=False):
            for list_idx, (msg_idx, msg) in enumerate(user_msgs):
                text = msg["content"]
                display = text[:30] + "…" if len(text) > 30 else text
                is_sel = st.session_state.selected_q == msg_idx
                if st.button(
                    f"Q{list_idx + 1}.  {display}",
                    key=f"qlist_{list_idx}",
                    use_container_width=True,
                    help=text,
                    type="primary" if is_sel else "secondary",
                ):
                    st.session_state.selected_q = None if is_sel else msg_idx
                    st.rerun()

# ─── 오른쪽: 채팅 ────────────────────────────────────────────
with right_col:
    selected_q = st.session_state.selected_q

    if selected_q is not None:
        q_num = next(
            (i + 1 for i, (idx, _) in enumerate(user_msgs) if idx == selected_q), "?")
        st.markdown(
            f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
            f'padding:10px 16px;font-size:13px;color:#1d4ed8;margin-bottom:12px;">'
            f'🔍 <b>Q{q_num}</b> 보는 중 &nbsp;—&nbsp; '
            f'왼쪽 목록에서 다른 질문을 선택하거나 <b>↩ 전체 대화</b>를 눌러주세요.</div>',
            unsafe_allow_html=True,
        )
        with st.container(height=530, border=False):
            user_msg = st.session_state.messages[selected_q]
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_msg["content"], unsafe_allow_html=True)
            asst_msg = None
            for i in range(selected_q + 1, len(st.session_state.messages)):
                if st.session_state.messages[i]["role"] == "assistant":
                    asst_msg = st.session_state.messages[i]
                    break
            if asst_msg:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(asst_msg["content"], unsafe_allow_html=True)
                    render_tool_badges(asst_msg.get("used_tools") or [])
            else:
                st.caption("아직 답변이 없습니다.")
    else:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align:center; padding:70px 20px; color:#94a3b8; line-height:1.9;">
                <div style="font-size:52px; margin-bottom:10px;">⚫</div>
                <div style="font-size:20px; font-weight:900; color:#3B4CCA;
                    margin-bottom:6px; font-family:'Black Han Sans',sans-serif; letter-spacing:1px;">
                    포켓몬 박사에게 물어보세요!
                </div>
                <div style="font-size:14px; color:#64748b;">
                    타입 · 스탯 · 진화 경로 · 도감 설명<br>무엇이든 답해드립니다 🔴
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.container(height=570, border=False):
                for msg in st.session_state.messages:
                    avatar = "🤖" if msg["role"] == "assistant" else "🧑"
                    with st.chat_message(msg["role"], avatar=avatar):
                        st.markdown(msg["content"], unsafe_allow_html=True)
                        if msg["role"] == "assistant":
                            render_tool_badges(msg.get("used_tools") or [])

# ── 입력 처리 ─────────────────────────────────────────────────
if prompt := st.chat_input("포켓몬에 대해 무엇이든 물어보세요... ⚡"):
    st.session_state.selected_q = None
    history = copy.deepcopy(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": prompt, "used_tools": []})

    with st.spinner("포켓몬 박사가 생각 중..."):
        try:
            result = api_chat(
                query=prompt,
                history=history,
                model=st.session_state.model,
                session_id=st.session_state.session_id,
            )
            answer = result["answer"]
            used_tools = result["used_tools"]
            st.session_state.session_id = result["session_id"]
        except Exception as e:
            answer = f"⚠️ 오류 ({type(e).__name__}): {e}"
            used_tools = []

    st.session_state.messages.append({
        "role": "assistant", "content": answer, "used_tools": used_tools,
    })
    st.rerun()
