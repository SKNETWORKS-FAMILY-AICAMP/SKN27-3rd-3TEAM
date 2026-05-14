import copy
import uuid
import streamlit as st

from chatbot.api import (
    api_chat, api_chat_stream, api_sessions, api_messages,
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

    # [핵심] 화면 허얘짐 방지 CSS
    st.markdown("""
        <style>
            /* 로딩 중 흐려짐 방지 */
            div[data-testid="stStatusWidget"] { display: none !important; }
            .stApp { opacity: 1 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # [핵심] 강력한 자동 스크롤 옵저버 주입 (iframe에서 상위 DOM 제어)
    import streamlit.components.v1 as components
    components.html("""
        <script>
            const setupObserver = () => {
                const parent = window.parent.document;
                const target = parent.querySelector('.main');
                if (!target) {
                    setTimeout(setupObserver, 500);
                    return;
                }
                
                const scrollToBottom = () => {
                    // 고정 높이 컨테이너에서 스크롤을 잡기 위한 다양한 타겟 설정
                    const selectors = [
                        'div[data-testid="stVerticalBlockBorderWrapper"] > div',
                        'div[data-testid="stScrollableContainer"]',
                        '.stScrollableContainer'
                    ];
                    
                    let scrolled = false;
                    selectors.forEach(selector => {
                        const containers = parent.querySelectorAll(selector);
                        containers.forEach(el => {
                            if (el.scrollHeight > el.clientHeight) {
                                el.scrollTop = el.scrollHeight;
                                scrolled = true;
                            }
                        });
                    });
                    
                    // 만약 특정 컨테이너 스크롤에 실패했다면 전체 화면을 내림
                    if (!scrolled) {
                        const mainContainer = parent.querySelector('.main .block-container');
                        if (mainContainer) {
                            mainContainer.scrollTop = mainContainer.scrollHeight;
                        }
                        parent.defaultView.scrollTo(0, parent.document.body.scrollHeight);
                    }
                };

                // 초기 1회 실행
                setTimeout(scrollToBottom, 300);

                // DOM 변화 감지 시 실행
                const observer = new MutationObserver(() => {
                    scrollToBottom();
                });
                
                observer.observe(target, { childList: true, subtree: true, characterData: true });
            };
            
            // 로드 대기 후 실행
            setTimeout(setupObserver, 100);
        </script>
    """, height=0)

    with right_col:
        msgs = st.session_state.messages
        is_loading = st.session_state.get("is_loading", False)

        # 1. 채팅창 컨테이너 (위아래 명확한 분리)
        st.markdown("""
        <style>
            /* 채팅창 컨테이너 스타일링 */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 16px;
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
                margin-bottom: 70px !important;
            }
            /* 하단 입력창 래퍼 여백 축소 */
            div[data-testid="stBottom"] {
                background: #ffffff;
                padding-top: 0px !important;
                padding-bottom: 0px !important;
                z-index: 999;
            }
            div[data-testid="stBottom"] > div {
                padding-bottom: 0px !important;
                padding-top: 0px !important;
            }
            /* 실제 입력창 영역 여백 완전 제거 */
            div[data-testid="stChatInput"] {
                padding-bottom: 10px !important;
                padding-top: 0px !important;
                margin-bottom: 0px !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        chat_container = st.container(height=550, border=True)
        with chat_container:
            for msg in msgs:
                if msg["role"] == "user":
                    render_user_bubble(msg["content"], USER_AVATAR)
                else:
                    render_assistant_bubble(msg["content"], OAK_AVATAR, msg.get("used_tools"))

            # 2. 스트리밍 처리 (내부에 JS 주입 제거하여 깜빡임 원천 차단)
            if is_loading:
                with st.empty():
                    full_answer = ""
                    used_tools = []
                    
                    try:
                        history = copy.deepcopy(msgs[:-1])
                        response = api_chat_stream(
                            query=msgs[-1]["content"],
                            history=history,
                            model=st.session_state.model,
                            session_id=st.session_state.current_chat_id,
                            user_id=USER_ID or None,
                        )
                        
                        import json
                        import re
                        import time

                        for line in response.iter_lines():
                            if line:
                                decoded = line.decode('utf-8')
                                if decoded.startswith("data: "):
                                    try:
                                        data = json.loads(decoded[6:])
                                    except:
                                        continue
                                    
                                    if data["type"] == "token":
                                        full_answer += data["content"]
                                        display_text = re.sub(r'\n{3,}', '\n\n', full_answer)
                                        render_assistant_bubble(display_text + " ▌", OAK_AVATAR)
                                        
                                        # 타이핑 속도감 조절
                                        time.sleep(0.03)

                                    elif data["type"] == "tools":
                                        used_tools = data["content"]
                                    
                                    elif data["type"] == "end":
                                        st.session_state.current_chat_id = data["session_id"]
                                        break
                        
                        # 최종 답변 확정
                        final_display = re.sub(r'\n{3,}', '\n\n', full_answer)
                        render_assistant_bubble(final_display, OAK_AVATAR, used_tools)
                        
                        # 상태 업데이트
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": final_display,
                            "used_tools": used_tools,
                        })

                        if st.session_state.current_chat_id not in {c["id"] for c in st.session_state.chat_history}:
                            refreshed = api_sessions(user_id=USER_ID or None)
                            if refreshed:
                                st.session_state.chat_history = refreshed

                    except Exception as e:
                        error_msg = f"⚠️ 오류가 발생했어요 ({type(e).__name__}): {e}"
                        render_assistant_bubble(error_msg, OAK_AVATAR)
                        st.session_state.messages.append({
                            "role": "assistant", "content": error_msg, "used_tools": []
                        })
                    
                    st.session_state.is_loading = False
                    st.rerun()

            else:
                st.markdown('<div style="height: 1px;"></div>', unsafe_allow_html=True)

        if not msgs and not is_loading:
            # Modern Welcome Screen
            st.markdown("""
            <style>
                .welcome-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    min-height: 50vh;
                    text-align: center;
                    padding: 0 20px;
                    animation: fadeIn 0.8s ease-out;
                }
                .welcome-icon {
                    font-size: 48px;
                    margin-bottom: 16px;
                    filter: drop-shadow(0 4px 12px rgba(238, 21, 21, 0.3));
                    animation: float 3s ease-in-out infinite;
                }
                .welcome-title {
                    font-size: 28px;
                    font-weight: 800;
                    color: #1e293b;
                    margin-bottom: 12px;
                    letter-spacing: -0.5px;
                }
                .welcome-subtitle {
                    font-size: 15px;
                    color: #64748b;
                    margin-bottom: 40px;
                    line-height: 1.6;
                    max-width: 400px;
                }
                .chip-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 12px;
                    width: 100%;
                    max-width: 600px;
                }
                .suggestion-chip {
                    background: #ffffff;
                    border: 1px solid rgba(226, 232, 240, 0.8);
                    border-radius: 16px;
                    padding: 16px;
                    text-align: left;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
                    transition: all 0.2s ease;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                .suggestion-chip:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
                    border-color: #cbd5e1;
                }
                .chip-icon {
                    font-size: 20px;
                }
                .chip-text {
                    font-size: 14px;
                    color: #334155;
                    font-weight: 600;
                }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
                @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
            </style>
            
            <div class="welcome-container">
                <div class="welcome-icon">⚡</div>
                <div class="welcome-title">오박사님의 포켓몬 연구소</div>
                <div class="welcome-subtitle">
                    타입 상성부터 능력치 비교, 진화 경로까지<br>포켓몬에 관한 모든 지식을 물어보세요.
                </div>
                
                <div class="chip-grid">
                    <div class="suggestion-chip">
                        <span class="chip-icon">📊</span>
                        <span class="chip-text">피카츄와 라이츄의 능력치 비교해줘</span>
                    </div>
                    <div class="suggestion-chip">
                        <span class="chip-icon">🔥</span>
                        <span class="chip-text">불꽃 타입의 가장 큰 약점은 뭐야?</span>
                    </div>
                    <div class="suggestion-chip">
                        <span class="chip-icon">🧬</span>
                        <span class="chip-text">이브이의 진화 경로를 모두 알려줘</span>
                    </div>
                    <div class="suggestion-chip">
                        <span class="chip-icon">📖</span>
                        <span class="chip-text">잠만보에 대한 도감 설명을 읽어줄래?</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if prompt := st.chat_input("포켓몬에 대해 무엇이든 물어보세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt, "used_tools": []})
        st.session_state.is_loading = True
        st.rerun()

