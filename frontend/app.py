import streamlit as st
import os

# 페이지 설정
st.set_page_config(
    page_title="Pokémon World",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 페이지 정의
def home_page():
    st.title("⚡ Pokémon Dashboard")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 배틀 시뮬레이터")
        st.write("전 세계 트레이너들과 실력을 겨뤄보세요!")
        if st.button("배틀 하러 가기", key="go_battle"):
            st.session_state.page = "Battle"
            st.rerun()

    with col2:
        st.subheader("💬 AI 챗봇")
        st.write("포켓몬 박사님에게 무엇이든 물어보세요.")
        if st.button("챗봇과 대화하기", key="go_chatbot"):
            st.session_state.page = "Chatbot"
            st.rerun()

    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📖 포켓몬 도감")
        st.write("모든 포켓몬의 상세 데이터를 확인하세요.")
        if st.button("도감 보기", key="go_pokedex"):
            st.session_state.page = "Pokedex"
            st.rerun()

    with col4:
        st.subheader("🛡️ 팀 빌더")
        st.write("최강의 팀을 구성하고 전략을 세우세요.")
        if st.button("팀 구성하기", key="go_team"):
            st.session_state.page = "Team Building"
            st.rerun()

# 라우터 로직
if 'page' not in st.session_state:
    st.session_state.page = "Home"

