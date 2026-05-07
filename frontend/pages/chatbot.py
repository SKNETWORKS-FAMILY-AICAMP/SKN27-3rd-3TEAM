import os
import sys
# chatbot.py
import streamlit as st
import requests

# Ensure utils is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

st.set_page_config(
    page_title="Pokedex - Pokémon World",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
)

# Inject common UI (Header, Follower, Global Styles)
inject_common_ui(spacer=True)

def show():
    st.title("포켓몬 AI 챗봇")

# ── 페이지 설정 ────────────────────────
st.set_page_config(
    page_title="포켓몬 챗봇",
    page_icon="⚡",
    layout="centered"
)

# ── 스타일 ─────────────────────────────
st.markdown("""
    <style>
    .user-msg {
        background-color: #FFD700;
        border-radius: 10px;
        padding: 10px 15px;
        margin: 5px 0;
        text-align: right;
        color: black;
    }
    .bot-msg {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 10px 15px;
        margin: 5px 0;
        color: black;
    }
    .sql-box {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 10px;
        color: #00ff00;
        font-size: 0.85em;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ── 타이틀 ─────────────────────────────
st.title("⚡ 포켓몬 챗봇")
st.caption("포켓몬 DB에 대해 무엇이든 물어보세요!")

# ── 세션 상태 초기화 ───────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_sql" not in st.session_state:
    st.session_state.show_sql = False

# ── 사이드바 ───────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    # SQL 쿼리 표시 토글
    st.session_state.show_sql = st.toggle(
        "SQL 쿼리 보기",
        value=False
    )

    st.divider()

    # 예시 질문
    st.subheader("💡 예시 질문")
    example_questions = [
        "공격력 상위 5개 포켓몬은?",
        "1세대 포켓몬 총 몇마리야?",
        "피카츄 정보 알려줘",
        "불꽃타입 포켓몬 알려줘",
        "방어력이 가장 높은 포켓몬은?",
    ]

    for q in example_questions:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

    st.divider()

    # 대화 초기화
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── 대화 기록 출력 ─────────────────────
for msg in st.session_state.messages:

    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-msg">🧑 {msg["content"]}</div>',
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            f'<div class="bot-msg">⚡ {msg["content"]}</div>',
            unsafe_allow_html=True
        )

        # SQL 쿼리 표시
        if st.session_state.show_sql and msg.get("sql"):
            st.markdown(
                f'<div class="sql-box">🔍 SQL: {msg["sql"]}</div>',
                unsafe_allow_html=True
            )

# ── FastAPI 호출 함수 ──────────────────
def ask_chatbot(question: str) -> dict:
    try:
        response = requests.post(
            "http://localhost:8088/chat",
            json={"question": question},
            timeout=30
        )
        return response.json()

    except requests.exceptions.ConnectionError:
        return {
            "answer": "⚠️ 서버에 연결할 수 없습니다. FastAPI 서버를 실행해주세요.",
            "intent": "error",
            "sql"   : None
        }
    except Exception as e:
        return {
            "answer": f"⚠️ 오류 발생: {str(e)}",
            "intent": "error",
            "sql"   : None
        }

# ── 예시 질문 처리 ─────────────────────
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

    # 유저 메시지 추가
    st.session_state.messages.append({
        "role"   : "user",
        "content": question
    })

    # 챗봇 응답
    with st.spinner("⚡ 포켓몬 도감 검색 중..."):
        result = ask_chatbot(question)

    # 봇 메시지 추가
    st.session_state.messages.append({
        "role"   : "assistant",
        "content": result["answer"],
        "sql"    : result.get("sql")
    })

    st.rerun()

# ── 입력창 ─────────────────────────────
with st.container():
    col1, col2 = st.columns([5, 1])

    with col1:
        user_input = st.chat_input("포켓몬에 대해 물어보세요...")

    if user_input:
        # 유저 메시지 추가
        st.session_state.messages.append({
            "role"   : "user",
            "content": user_input
        })

        # 챗봇 응답
        with st.spinner("⚡ 포켓몬 도감 검색 중..."):
            result = ask_chatbot(user_input)

        # 봇 메시지 추가
        st.session_state.messages.append({
            "role"   : "assistant",
            "content": result["answer"],
            "sql"    : result.get("sql")
        })

        st.rerun()



if __name__ == "__main__":
    show()

