"""
포켓몬 챗봇 Streamlit UI
========================
pokemon_agent.py 와 같은 디렉터리에 있어야 합니다.
.env 파일에 아래 키가 있어야 합니다:
  OPENAI_API_KEY=...
  TAVILY_API_KEY=...
  DATABASE_URL=postgresql://...  (없으면 기본값 사용)
"""

import copy
import streamlit as st
from common.pokemon_agent import chat_with_tools, MODELS, DEFAULT_MODEL



# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="포켓몬 박사 챗봇",
    page_icon="🔴",
    layout="centered",
)

# ──────────────────────────────────────────────
# CSS — 포켓볼 감성 다크 테마
# ──────────────────────────────────────────────
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;900&family=Space+Mono:wght@400;700&display=swap');

/* 전체 배경 */
html, body, [data-testid="stAppViewContainer"] {
    background: #1a1a2e !important;
    font-family: 'Nunito', sans-serif;
}

[data-testid="stHeader"] { background: transparent !important; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #16213e !important;
    border-right: 2px solid #e63946;
}
[data-testid="stSidebar"] * { color: #edf2f4 !important; }

/* 메인 컨테이너 */
.block-container {
    max-width: 780px !important;
    padding-top: 1.5rem !important;
}

/* 헤더 */
.pk-header {
    text-align: center;
    padding: 1.6rem 1rem 1rem;
    background: linear-gradient(135deg, #e63946 0%, #c1121f 50%, #1a1a2e 100%);
    border-radius: 20px;
    margin-bottom: 1.4rem;
    border: 2px solid #e63946;
    position: relative;
    overflow: hidden;
}
.pk-header::before {
    content: '';
    position: absolute;
    top: 50%; left: 0; right: 0;
    height: 3px;
    background: #fff;
    transform: translateY(-50%);
}
.pk-header::after {
    content: '';
    position: absolute;
    top: 50%; left: 50%;
    width: 28px; height: 28px;
    background: #fff;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    border: 3px solid #1a1a2e;
    box-shadow: 0 0 0 3px #fff;
}
.pk-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.7rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 2px;
    margin: 0;
    text-shadow: 2px 2px 0 #c1121f;
    position: relative;
    z-index: 1;
}
.pk-sub {
    color: rgba(255,255,255,0.85);
    font-size: 0.82rem;
    margin-top: 0.25rem;
    position: relative;
    z-index: 1;
}

/* 채팅 버블 공통 */
.bubble-wrap { display: flex; margin-bottom: 1rem; align-items: flex-end; gap: 10px; }
.bubble-wrap.user  { flex-direction: row-reverse; }
.bubble-wrap.bot   { flex-direction: row; }

.avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.avatar.bot  { background: #e63946; border: 2px solid #fff; }
.avatar.user { background: #4cc9f0; border: 2px solid #fff; }

.bubble {
    max-width: 75%;
    padding: 0.75rem 1.1rem;
    border-radius: 18px;
    font-size: 0.93rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble.bot {
    background: #16213e;
    color: #edf2f4;
    border: 1.5px solid #e63946;
    border-bottom-left-radius: 4px;
}
.bubble.user {
    background: #4cc9f0;
    color: #1a1a2e;
    font-weight: 600;
    border-bottom-right-radius: 4px;
}

/* 타이핑 인디케이터 */
.typing { display: flex; gap: 5px; padding: 0.6rem 0.8rem; }
.typing span {
    width: 8px; height: 8px;
    background: #e63946;
    border-radius: 50%;
    animation: bounce 1.2s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
    40%            { transform: translateY(-8px); opacity: 1; }
}

/* 입력창 래퍼 */
.input-area {
    position: sticky;
    bottom: 0;
    background: #1a1a2e;
    padding: 0.8rem 0 0.4rem;
    border-top: 2px solid #e63946;
    margin-top: 0.5rem;
}

/* 입력창 */
[data-testid="stChatInput"] textarea {
    background: #16213e !important;
    color: #edf2f4 !important;
    border: 1.5px solid #e63946 !important;
    border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #4cc9f0 !important;
    box-shadow: 0 0 0 2px rgba(76,201,240,0.25) !important;
}

/* 예시 버튼 */
.stButton > button {
    background: #16213e !important;
    color: #4cc9f0 !important;
    border: 1.5px solid #4cc9f0 !important;
    border-radius: 20px !important;
    font-size: 0.78rem !important;
    padding: 0.3rem 0.8rem !important;
    transition: all 0.2s;
    font-family: 'Nunito', sans-serif !important;
    white-space: nowrap;
}
.stButton > button:hover {
    background: #4cc9f0 !important;
    color: #1a1a2e !important;
}

/* 사이드바 라디오/슬라이더 */
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSlider label { color: #edf2f4 !important; }

/* 도구 사용 뱃지 */
.tool-badge {
    display: inline-block;
    font-size: 0.68rem;
    padding: 1px 7px;
    border-radius: 20px;
    margin: 2px 2px 6px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.tool-db      { background: #264653; color: #2a9d8f; border: 1px solid #2a9d8f; }
.tool-vector  { background: #3d2b69; color: #b388ff; border: 1px solid #b388ff; }
.tool-neo4j   { background: #1a3a2a; color: #4ade80; border: 1px solid #4ade80; }
.tool-web     { background: #6b3a1f; color: #f4a261; border: 1px solid #f4a261; }

/* 스크롤바 */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #1a1a2e; }
::-webkit-scrollbar-thumb { background: #e63946; border-radius: 3px; }

/* 구분선 */
hr { border-color: #e6394630 !important; }

/* 푸터 텍스트 */
.footer-txt {
    text-align: center;
    font-size: 0.7rem;
    color: #555;
    margin-top: 0.5rem;
}
</style>
""")

# ──────────────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = {}   # {msg_index: [tool_name, ...]}

if "model" not in st.session_state:
    st.session_state.model = DEFAULT_MODEL

# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    st.markdown("---")

    selected_model = st.selectbox(
        "🤖 모델 선택",
        options=list(MODELS.keys()),
        index=list(MODELS.keys()).index(st.session_state.model),
    )
    if selected_model != st.session_state.model:
        st.session_state.model = selected_model
        st.session_state.messages = []
        st.session_state.tool_logs = {}
        st.rerun()

    st.markdown("---")

    show_tools = st.toggle("🔧 툴 사용 내역 표시", value=True)

    st.markdown("---")
    st.markdown("### 📖 사용 가능한 툴")
    st.markdown("""
- 🗄️ **search_pokemon_db**
  SQL로 스탯·타입·세대 검색
- 🔮 **search_flavor_text**
  BM25 + 벡터 + Cross-encoder Rerank
  도감 설명·분위기 검색
- 🔗 **search_evolution_chain**
  Neo4j로 진화 경로·조건 탐색
- ⚔️ **search_type_relations**
  Neo4j로 타입 상성·약점 탐색
- 🌐 **web_search**
  DB에 없는 최신 정보
""")

    st.markdown("---")
    st.markdown("### 💡 질문 팁")
    st.markdown("""
- 타입 + 스탯 조건으로 질문
- 분위기나 느낌으로 추천 요청
- 특정 포켓몬 상세 정보 질문
""")

    st.markdown("---")
    if st.button("🗑️ 대화 초기화"):
        st.session_state.messages = []
        st.session_state.tool_logs = {}
        st.rerun()

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.html("""
<div class="pk-header">
    <p class="pk-title">⚫ POKÉDEX AI ⚫</p>
    <p class="pk-sub">하이브리드 검색 · Cross-encoder Re-ranking · Tool-calling Agent</p>
</div>
""")

# ──────────────────────────────────────────────
# 예시 질문 버튼
# ──────────────────────────────────────────────
EXAMPLE_QUESTIONS = [
    "불꽃 타입 공격력 TOP 3",
    "귀엽고 작은 포켓몬 추천",
    "피카츄의 도감 설명",
    "1세대 HP 최강은?",
    "물 타입이면서 바다 느낌 포켓몬",
]

cols = st.columns(len(EXAMPLE_QUESTIONS))
clicked_example = None
for col, q in zip(cols, EXAMPLE_QUESTIONS):
    with col:
        if st.button(q, key=f"ex_{q}"):
            clicked_example = q

# ──────────────────────────────────────────────
# 채팅 히스토리 렌더링
# ──────────────────────────────────────────────
_BADGE_MAP = [
    ("db",      "tool-db",     "🗄️"),
    ("flavor",  "tool-vector", "🔮"),
    ("evol",    "tool-neo4j",  "🔗"),
    ("type_rel","tool-neo4j",  "⚔️"),
    ("web",     "tool-web",    "🌐"),
]

def render_tool_badges(tool_names: list[str]) -> str:
    badge_html = ""
    for t in tool_names:
        for key, css, emoji in _BADGE_MAP:
            if key in t:
                badge_html += f'<span class="tool-badge {css}">{emoji} {t}</span>'
                break
    return badge_html


chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.html("""
<div style='text-align:center; color:#555; margin-top:3rem; font-size:0.9rem;'>
    🔴 포켓몬에 대해 무엇이든 물어보세요!<br>
    <span style='font-size:0.78rem;'>위 예시 버튼을 눌러도 됩니다.</span>
</div>
""")
    else:
        for i, msg in enumerate(st.session_state.messages):
            role = msg["role"]
            content = msg["content"]
            avatar = "🤖" if role == "assistant" else "🧑"
            cls    = "bot" if role == "assistant" else "user"

            tool_html = ""
            if role == "assistant" and show_tools and i in st.session_state.tool_logs:
                tool_html = render_tool_badges(st.session_state.tool_logs[i])

            st.html(f"""
<div class="bubble-wrap {cls}">
    <div class="avatar {cls}">{avatar}</div>
    <div>
        {f'<div style="margin-bottom:2px">{tool_html}</div>' if tool_html else ''}
        <div class="bubble {cls}">{content}</div>
    </div>
</div>
""")

# ──────────────────────────────────────────────
# 입력 처리
# ──────────────────────────────────────────────
def handle_query(user_input: str):
    """질문 처리 → agent 호출 → 결과 저장"""
    user_input = user_input.strip()
    if not user_input:
        return

    history = copy.deepcopy(st.session_state.messages)

    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner(""):
        try:
            answer, used_tools = chat_with_tools(user_input, history=history, model=st.session_state.model)
        except Exception as e:
            answer = f"⚠️ 오류가 발생했습니다: {e}"
            used_tools = []

    # 응답 저장
    bot_idx = len(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": answer})

    if used_tools:
        st.session_state.tool_logs[bot_idx] = used_tools

    st.rerun()


# 예시 버튼 클릭
if clicked_example:
    handle_query(clicked_example)

# 채팅 입력창
user_input = st.chat_input("포켓몬에 대해 무엇이든 물어보세요... ⚡")
if user_input:
    handle_query(user_input)

# ──────────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────────
st.html("""
<p class="footer-txt">
    Powered by LangGraph · OpenAI · Groq · BAAI/bge-reranker · Tavily · pgvector · Neo4j
</p>
""")