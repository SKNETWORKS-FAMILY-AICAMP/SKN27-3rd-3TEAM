import os
import sys
import copy
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

from common.pokemon_agent import chat_with_tools, MODELS, DEFAULT_MODEL
from common.chat_history import (
    init_tables, create_session, save_message,
    load_sessions, load_messages, delete_session,
)

st.set_page_config(
    page_title="포켓몬 박사 챗봇",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_common_ui(spacer=True, hide_sidebar=False)

try:
    init_tables()
except Exception:
    pass

# ──────────────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model" not in st.session_state:
    st.session_state.model = DEFAULT_MODEL

# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.title("🔴 포켓몬 챗봇")

    st.session_state.model = st.selectbox(
        "모델 선택",
        options=list(MODELS.keys()),
        index=list(MODELS.keys()).index(st.session_state.model),
    )

    if st.button("➕ 새 대화", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("이전 대화")

    for s in load_sessions():
        created = s["created_at"].strftime("%m/%d %H:%M")
        is_current = st.session_state.session_id == s["id"]
        label = f"{'▶ ' if is_current else ''}{s['title']}"

        col_btn, col_del = st.columns([6, 1])
        with col_btn:
            if st.button(label, key=f"sess_{s['id']}", help=f"{s['model']} · {created}", use_container_width=True):
                st.session_state.session_id = s["id"]
                st.session_state.model = s["model"]
                st.session_state.messages = load_messages(s["id"])
                st.rerun()
        with col_del:
            if st.button("🗑", key=f"del_{s['id']}"):
                delete_session(s["id"])
                if st.session_state.session_id == s["id"]:
                    st.session_state.session_id = None
                    st.session_state.messages = []
                st.rerun()

# ──────────────────────────────────────────────
# 메인 영역
# ──────────────────────────────────────────────
st.header("⚫ POKÉDEX AI")

if not st.session_state.messages:
    st.info("포켓몬에 대해 무엇이든 물어보세요! 🔴")

for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        tools = msg.get("used_tools") or []
        if tools and msg["role"] == "assistant":
            st.caption("사용 툴: " + " · ".join(f"`{t}`" for t in tools))

# ──────────────────────────────────────────────
# 입력 처리
# ──────────────────────────────────────────────
if prompt := st.chat_input("포켓몬에 대해 무엇이든 물어보세요... ⚡"):
    if st.session_state.session_id is None:
        st.session_state.session_id = create_session(prompt, st.session_state.model)

    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    history = copy.deepcopy(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": prompt, "used_tools": []})
    save_message(st.session_state.session_id, "user", prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("포켓몬 박사가 생각 중..."):
            try:
                answer, used_tools = chat_with_tools(
                    prompt,
                    history=history,
                    model=st.session_state.model,
                )
            except Exception as e:
                answer = f"⚠️ 오류 ({type(e).__name__}): {e}"
                used_tools = []

        st.markdown(answer)
        if used_tools:
            st.caption("사용 툴: " + " · ".join(f"`{t}`" for t in used_tools))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "used_tools": used_tools,
    })
    save_message(st.session_state.session_id, "assistant", answer, used_tools)
    st.rerun()
