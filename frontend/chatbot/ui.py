import copy
import uuid
import streamlit as st

from chatbot.api import (
    api_chat, api_sessions, api_messages,
    api_delete_session, api_rename_session,
)
from chatbot.constants import MODELS_LIST, DEFAULT_MODEL, MODEL_DISPLAY_NAMES
from chatbot.components import get_base64_img, render_user_bubble, render_assistant_bubble


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


def show():
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

    if not st.session_state.chat_history:
        _sessions = api_sessions(user_id=USER_ID or None)
        if _sessions:
            st.session_state.chat_history = _sessions
            if st.session_state.current_chat_id is None:
                _first_id = _sessions[0]["id"]
                st.session_state.current_chat_id = _first_id
                if not st.session_state.messages:
                    st.session_state.messages = api_messages(_first_id)

    USER_AVATAR = (
        _user_info.get("avatar_url")
        or get_base64_img("default.png")
        or "https://cdn-icons-png.flaticon.com/512/188/188987.png"
    )
    OAK_AVATAR = get_base64_img("ai_default.png")

    left_col, right_col = st.columns([1, 4], gap="small")

    with left_col:
        st.markdown("""
        <div class="cb-left-header">
            <div class="cb-left-title">
                <div class="cb-pokeball"></div>
                POKÉDEX AI
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="cb-new-btn">', unsafe_allow_html=True)
        if st.button("＋ 새 채팅 시작", use_container_width=True, key="new_chat"):
            st.session_state.update(current_chat_id=None, messages=[], is_loading=False)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="cb-section-label" style="margin-top:12px;">모델 선택</div>',
                    unsafe_allow_html=True)
        st.session_state.model = st.radio(
            "모델",
            options=MODELS_LIST,
            format_func=lambda x: MODEL_DISPLAY_NAMES.get(x, x),
            index=MODELS_LIST.index(st.session_state.model) if st.session_state.model in MODELS_LIST else 0,
            horizontal=True,
            key="model_radio",
            label_visibility="collapsed",
        )

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
                    return next(
                        (c.get("title") or f"대화 #{c['id']}")
                        for c in st.session_state.chat_history if c["id"] == x
                    )

                current_idx = 0
                if st.session_state.current_chat_id in chat_options:
                    current_idx = chat_options.index(st.session_state.current_chat_id)

                selected_chat_id = st.selectbox(
                    "대화 선택",
                    options=chat_options,
                    format_func=chat_format,
                    index=current_idx,
                    label_visibility="collapsed",
                    key="chat_history_select",
                )

                if selected_chat_id != st.session_state.current_chat_id:
                    st.session_state.current_chat_id = selected_chat_id
                    st.session_state.messages = api_messages(selected_chat_id) if selected_chat_id else []
                    st.session_state.is_loading = False
                    st.rerun()

                col_e, col_d = st.columns(2)
                with col_e:
                    btn_disabled = selected_chat_id is None
                    if st.button("✏️ 이름 수정", key="btn_rename_current",
                                 use_container_width=True, disabled=btn_disabled):
                        show_rename_dialog(selected_chat_id, chat_format(selected_chat_id))
                with col_d:
                    if st.button("🗑️ 삭제", key="btn_delete_current",
                                 use_container_width=True, disabled=btn_disabled):
                        show_delete_dialog(selected_chat_id, chat_format(selected_chat_id))

    with right_col:
        msgs = st.session_state.messages
        is_loading = st.session_state.get("is_loading", False)

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
        else:
            with st.container(height=700, border=False):
                for msg in msgs:
                    if msg["role"] == "user":
                        render_user_bubble(msg["content"], USER_AVATAR)
                    else:
                        render_assistant_bubble(msg["content"], OAK_AVATAR, msg.get("used_tools"))

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
                        unsafe_allow_html=True,
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

    if prompt := st.chat_input("포켓몬에 대해 무엇이든 물어보세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt, "used_tools": []})
        st.session_state.is_loading = True
        st.rerun()
