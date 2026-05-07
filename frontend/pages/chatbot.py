import streamlit as st
import sys
import os
from common.pokemon_rag import chat, ingest_embeddings

# utils 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui

st.set_page_config(
    page_title="포켓몬 박사",
    page_icon="🔴",
    layout="centered",
)

inject_common_ui(spacer=True)  # 한 번만

# 나머지 코드는 그대로 유지...


# ══════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════

st.markdown("""
<style>
  /* 전체 배경 */
  .stApp { background-color: #f5f5f0; }

  /* 헤더 */
  .chat-header {
    background: linear-gradient(135deg, #cc0000 0%, #ff4444 100%);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(204,0,0,0.2);
  }
  .chat-header h1 { color: white; margin: 0; font-size: 2rem; }
  .chat-header p  { color: rgba(255,255,255,0.85); margin: 6px 0 0; font-size: 0.9rem; }

  /* 메시지 버블 */
  .msg-user {
    background: #cc0000;
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px;
    margin: 8px 0 8px 20%;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    line-height: 1.5;
  }
  .msg-bot {
    background: white;
    color: #1a1a1a;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 16px;
    margin: 8px 20% 8px 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    border-left: 3px solid #cc0000;
    line-height: 1.6;
  }
  .msg-label-user {
    text-align: right;
    font-size: 0.75rem;
    color: #888;
    margin: 0 4px 2px 0;
  }
  .msg-label-bot {
    font-size: 0.75rem;
    color: #888;
    margin: 0 0 2px 4px;
  }

  /* 라우트 배지 */
  .badge {
    display: inline-block;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    margin-top: 6px;
    font-weight: 600;
  }
  .badge-sql       { background: #e3f0ff; color: #1565c0; }
  .badge-embedding { background: #e8f5e9; color: #2e7d32; }
  .badge-web       { background: #fff3e0; color: #e65100; }

  /* 사이드바 */
  .sidebar-section {
    background: white;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .sidebar-section h4 { margin: 0 0 8px; color: #cc0000; font-size: 0.85rem; }

  /* 예시 버튼 */
  .stButton > button {
    width: 100%;
    text-align: left;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.82rem;
    color: #333;
    transition: all 0.15s;
  }
  .stButton > button:hover {
    border-color: #cc0000;
    color: #cc0000;
    background: #fff5f5;
  }

  /* 입력창 */
  .stTextInput > div > div > input {
    border-radius: 24px;
    border: 2px solid #e0e0e0;
    padding: 10px 18px;
    font-size: 0.95rem;
  }
  .stTextInput > div > div > input:focus {
    border-color: #cc0000;
    box-shadow: 0 0 0 2px rgba(204,0,0,0.1);
  }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# 세션 초기화
# ══════════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""


# ══════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 🔴 포켓몬 박사")
    st.markdown("---")

    # 예시 질문 — SQL 경로
    st.markdown('<div class="sidebar-section"><h4>📊 데이터 검색 (SQL)</h4>', unsafe_allow_html=True)
    sql_examples = [
        "🔥 불꽃 타입 공격력 TOP 5",
        "⚡ 피카츄 스탯 알려줘",
        "💧 물 타입 중 빠른 포켓몬",
        "🌿 1세대 포켓몬 목록",
        "⚔️ 공격력 120 이상인 포켓몬",
    ]
    for ex in sql_examples:
        if st.button(ex, key=f"sql_{ex}"):
            st.session_state.pending_query = ex
    st.markdown("</div>", unsafe_allow_html=True)

    # 예시 질문 — Embedding 경로
    st.markdown('<div class="sidebar-section"><h4>✨ 의미 검색 (AI)</h4>', unsafe_allow_html=True)
    emb_examples = [
        "🐱 귀엽고 작은 포켓몬 추천",
        "🌊 바다 느낌 나는 포켓몬",
        "😤 피카츄는 어떤 성격이야?",
        "🌙 밤에 활동하는 포켓몬",
        "💪 강하고 용감한 느낌의 포켓몬",
    ]
    for ex in emb_examples:
        if st.button(ex, key=f"emb_{ex}"):
            st.session_state.pending_query = ex
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # 대화 초기화
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # 임베딩 초기화 (관리자용)
    st.markdown("---")
    st.markdown("**🛠️ 관리자**")
    if st.button("임베딩 생성 (최초 1회)", use_container_width=True):
        with st.spinner("임베딩 생성 중..."):
            try:
                ingest_embeddings()
                st.success("✅ 완료!")
            except Exception as e:
                st.error(f"실패: {e}")

    # 경로 범례
    st.markdown("---")
    st.markdown("""
<div style='font-size:0.75rem; color:#888;'>
<b>검색 경로</b><br>
🔵 SQL — 수치/조건 검색<br>
🟢 AI — 의미/느낌 검색<br>
🟠 웹 — DB 미보유 정보
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# 메인 헤더
# ══════════════════════════════════════════════════════════

st.markdown("""
<div class="chat-header">
  <h1>🔴 포켓몬 박사</h1>
  <p>포켓몬에 대해 무엇이든 물어보세요!</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# 대화 히스토리 출력
# ══════════════════════════════════════════════════════════

chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown("""
<div style='text-align:center; color:#aaa; padding: 40px 0;'>
  <div style='font-size:3rem;'>🎮</div>
  <div style='margin-top:8px;'>포켓몬에 대해 질문해보세요!</div>
  <div style='font-size:0.82rem; margin-top:4px;'>왼쪽 예시를 클릭하거나 직접 입력하세요</div>
</div>
""", unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-label-user">나</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="msg-label-bot">🔴 포켓몬 박사</div>', unsafe_allow_html=True)
            badge = ""
            if msg.get("route") == "sql":
                badge = '<span class="badge badge-sql">🔵 SQL 검색</span>'
            elif msg.get("route") == "embedding":
                badge = '<span class="badge badge-embedding">🟢 AI 의미 검색</span>'
            elif msg.get("route") == "web":
                badge = '<span class="badge badge-web">🟠 웹 검색</span>'
            st.markdown(
                f'<div class="msg-bot">{msg["content"]}{("<br>" + badge) if badge else ""}</div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════
# 입력창 + 전송
# ══════════════════════════════════════════════════════════

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])

with col_input:
    user_input = st.text_input(
        label="질문",
        value=st.session_state.pending_query,
        placeholder="예) 피카츄 공격력은? / 귀여운 포켓몬 추천해줘",
        label_visibility="collapsed",
        key="chat_input",
    )

with col_btn:
    send = st.button("전송 ➤", use_container_width=True)

# 예시 버튼 클릭 시 자동 전송
if st.session_state.pending_query and st.session_state.pending_query != user_input:
    user_input = st.session_state.pending_query
    send = True

# ══════════════════════════════════════════════════════════
# 메시지 처리
# ══════════════════════════════════════════════════════════

if send and user_input.strip():
    query = user_input.strip()

    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": query})

    # pending 초기화
    st.session_state.pending_query = ""

    # LangGraph RAG 실행
    with st.spinner("🔍 포켓몬 데이터 검색 중..."):
        try:
            from common.pokemon_rag import app as rag_app

            result = rag_app.invoke({
                "query":       query,
                "route":       "",
                "sql":         "",
                "db_result":   "",
                "vector_docs": [],
                "web_result":  "",
                "context":     "",
                "answer":      "",
            })

            answer = result["answer"]
            route  = result.get("route", "")

            # ✅ 수정 - route 문자열만 보거나 값이 있는지 체크
            if "web" in route:
                badge_route = "web"
            elif "embedding" in route or "vector" in route:
                badge_route = "embedding"
            elif "sql" in route:
                badge_route = "sql"
            else:
                badge_route = "sql"  # 기본값

        except Exception as e:
            answer     = f"오류가 발생했어요: {e}"
            badge_route = ""

    # 봇 응답 추가
    st.session_state.messages.append({
        "role":    "assistant",
        "content": answer,
        "route":   badge_route,
    })

    st.rerun()

if __name__ == "__main__":
    pass # Main code is executed at top level in Streamlit

