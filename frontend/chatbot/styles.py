import streamlit as st


def inject_chatbot_styles() -> None:
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
div:has(> [data-testid="stHorizontalBlock"]) {
    margin-bottom: -10px !important; /* 세션 항목 간격 축소 */
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
    background: linear-gradient(to bottom, #EE1515 50%, #ffffff 50%);
    border-radius: 50%;
    border: 2px solid #333;
    position: relative;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(238,21,21,0.35);
}
.cb-pokeball::before {
    content: '';
    position: absolute;
    top: 50%; left: 0; right: 0;
    height: 2px; background: #333;
    transform: translateY(-50%);
}
.cb-pokeball::after {
    content: '';
    position: absolute;
    top: 50%; left: 50%;
    width: 8px; height: 8px;
    background: #fff;
    border: 2px solid #333;
    border-radius: 50%;
    transform: translate(-50%, -50%);
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

/* ── 모델 선택 라디오 버튼 흔들림 방지 ── */
[data-testid="stRadio"] div[data-baseweb="radio"] p {
    font-weight: 600 !important;
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

/* ── 드롭다운 아래 수정/삭제 버튼 ── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] button {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 6px 0 !important;
    height: 38px !important;
    min-height: 38px !important;
    background: transparent !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    transition: all 0.2s !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* 두 버튼 모두 삭제(빨간색) 스타일로 통일 */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] button {
    color: #ef4444 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] button:hover {
    color: #dc2626 !important;
    border-color: #ef4444 !important;
    background: rgba(239,68,68,0.08) !important;
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
    margin-top: 8vh;
}
.cb-welcome-ball {
    width: 80px; height: 80px;
    background: linear-gradient(to bottom, #EE1515 50%, #ffffff 50%);
    border-radius: 50%; border: 4px solid #333;
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
