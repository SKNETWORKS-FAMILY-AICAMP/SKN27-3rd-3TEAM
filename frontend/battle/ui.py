import streamlit as st
import base64
from .utils import BattlePokemon

def fmt_player(name: str) -> str:
    return f"<span class='player-text'>{name}</span>"

def fmt_bot(name: str) -> str:
    return f"<span class='bot-text'>{name}</span>"

def fmt_move(name: str) -> str:
    return f"<span class='move-text'>{name}</span>"

from pathlib import Path

from .constants import LEADER_IMAGE_MAP, GYM_BG_MAP

def get_gym_bg_base64(leader_name: str) -> str:
    if not leader_name:
        return ""
    clean_name = leader_name.strip()
    file_name = GYM_BG_MAP.get(clean_name)
    if not file_name:
        for key, val in GYM_BG_MAP.items():
            if clean_name in key or key in clean_name:
                file_name = val
                break
    if not file_name:
        return ""
    try:
        current_dir = Path(__file__).resolve().parent
        path = current_dir.parent / "img" / "gym_background" / file_name
        if path.exists():
            with open(path, "rb") as f:
                data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except Exception as e:
        print(f"Error loading gym background for {leader_name}: {e}")
    return ""

def get_trainer_image_base64(leader_name: str) -> str:
    if not leader_name:
        return ""
    
    clean_name = leader_name.strip()
    file_name = LEADER_IMAGE_MAP.get(clean_name)
    
    if not file_name:
        # Fallback: check if clean_name is part of any key
        for key, val in LEADER_IMAGE_MAP.items():
            if clean_name in key or key in clean_name:
                file_name = val
                break
    
    if not file_name:
        print(f"Debug: No file name found for leader '{clean_name}'")
        return ""
    
    try:
        # 현재 파일(ui.py)의 절대 경로를 기준으로 이미지 폴더 경로 계산
        current_dir = Path(__file__).resolve().parent
        path = current_dir.parent / "img" / "gym_leaders" / file_name
        
        if path.exists():
            with open(path, "rb") as f:
                data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
        else:
            print(f"Debug: Image file not found at {path}")
            # 추가 시도: 현재 작업 디렉토리 기준
            alt_path = Path("frontend/img/gym_leaders") / file_name
            if alt_path.exists():
                with open(alt_path, "rb") as f:
                    data = f.read()
                return f"data:image/png;base64,{base64.b64encode(data).decode()}"
            print(f"Debug: Image file also not found at {alt_path.absolute()}")
    except Exception as e:
        print(f"Error loading trainer image for {leader_name}: {e}")
        
    return ""

def inject_battle_styles(bg_url: str = None):
    bg_style = f"background: url('{bg_url}') center/cover no-repeat fixed;" if bg_url else "background: #0f172a;"
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;600;700&display=swap');

        :root {{
            --poke-yellow: #FFCB05;
            --poke-blue: #2A75BB;
            --accent: #38bdf8;
            --glass-bg: rgba(15, 23, 42, 0.78);
            --glass-border: rgba(255, 255, 255, 0.1);
        }}

        .stApp {{ {bg_style} }}
        .stApp::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(10, 15, 30, 0.75);
            z-index: -1;
        }}
        [data-testid="stAppViewBlockContainer"] {{
            max-width: 1180px;
            padding-top: 1.2rem;
        }}

        /* ── Battle Header ── */
        .battle-header {{
            border: 1px solid rgba(56, 189, 248, 0.22);
            border-radius: 20px;
            padding: 28px 24px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(30, 41, 59, 0.85) 100%);
            backdrop-filter: blur(12px);
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }}
        .battle-header::after {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #38bdf8, transparent);
        }}
        .battle-header h1 {{
            margin: 0;
            color: #ffffff !important;
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: 0.5px;
            text-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}
        .battle-header p,
        .battle-header span {{
            color: #ffffff !important;
            margin: 8px 0 0;
            font-size: 0.95rem;
        }}

        /* ── Section title with accent bar (like pokemon_detail evo-title) ── */
        .battle-section-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.05rem;
            font-weight: 900;
            color: #f8fafc;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 18px 0 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .battle-section-title::before {{
            content: '';
            width: 5px;
            height: 20px;
            background: #38bdf8;
            border-radius: 3px;
            flex-shrink: 0;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.55);
        }}

        /* ── Gym leader roster (menu page) ── */
        .gym-roster-wrap {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 10px 0 16px;
        }}
        .gym-roster-card {{
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 14px;
            padding: 12px 8px 8px;
            text-align: center;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            flex: 1;
            min-width: 70px;
            backdrop-filter: blur(8px);
        }}
        .gym-roster-card:hover {{
            background: rgba(56, 189, 248, 0.1);
            border-color: rgba(56, 189, 248, 0.45);
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.35);
        }}
        .gym-roster-card img {{
            width: 75px;
            height: 75px;
            object-fit: contain;
            display: block;
            margin: 0 auto;
            filter: drop-shadow(0 5px 10px rgba(0,0,0,0.3));
            animation: float-anim 4s ease-in-out infinite;
        }}
        .gym-roster-name {{
            color: #ffffff;
            font-size: 0.8rem;
            font-weight: 700;
            margin-top: 6px;
        }}

        /* ── Glass divider ── */
        .battle-divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.25), transparent);
            border: none;
            margin: 14px 0;
        }}

        /* ── Pokemon status card ── */
        .status-card {{
            border: 1px solid rgba(148, 163, 184, .24);
            border-radius: 12px;
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
            padding: 16px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            position: relative;
            overflow: hidden;
            width: 100%;
        }}
        .status-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 100% 4px;
            pointer-events: none;
            z-index: 0;
        }}
        .status-card > * {{
            position: relative;
            z-index: 1;
        }}
        .pokemon-sprite {{
            width: 170px;
            height: 170px;
            object-fit: contain;
            filter: drop-shadow(0 15px 25px rgba(0,0,0,.5));
            animation: float-anim 4s ease-in-out infinite;
        }}
        @keyframes float-anim {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-8px); }}
        }}
        .pokemon-name {{
            color: #fff;
            font-weight: 900;
            font-size: 1.2rem;
        }}
        .type-pill {{
            display: inline-flex;
            padding: 3px 9px;
            margin: 6px 3px 0;
            border-radius: 999px;
            background: rgba(15, 23, 42, .85);
            color: #e5e7eb;
            font-size: .8rem;
            font-weight: 800;
        }}
        .hp-label {{
            color: #e5e7eb;
            font-weight: 800;
            font-size: .88rem;
            margin-top: 8px;
        }}
        .move-container-vertical {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding-right: 10px;
            border-right: 1px solid rgba(148, 163, 184, 0.2);
            min-width: 120px;
            text-align: left;
        }}
        .move-chip-v {{
            display: block;
            padding: 4px 8px;
            border-radius: 4px;
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(96, 165, 250, 0.2);
            color: #dbeafe;
            font-size: 0.75rem;
            font-weight: 800;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .stat-badge {{
            display: inline-flex;
            margin: 2px;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 800;
            color: #fff;
        }}
        .stat-up {{ background: #ef4444; }}
        .stat-down {{ background: #3b82f6; }}
        .stat-sidebar-item {{
            background: rgba(15, 23, 42, 0.5);
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            color: #94a3b8;
            font-weight: 700;
            border: 1px solid rgba(148, 163, 184, 0.1);
            text-align: center;
        }}
        .stat-sidebar-container {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dotted rgba(148, 163, 184, 0.3);
        }}
        .secret-card {{
            height: 235px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            border: 1px dashed rgba(226, 232, 240, .35);
            background: rgba(30, 41, 59, .52);
            color: #e5e7eb;
            font-size: 1.8rem;
            font-weight: 900;
            text-align: center;
        }}

        /* ── Battle log / command card containers ── */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(160deg, rgba(12, 20, 42, 0.96) 0%, rgba(18, 30, 55, 0.94) 100%) !important;
            border: 1px solid rgba(56, 189, 248, 0.28) !important;
            border-radius: 16px !important;
            backdrop-filter: blur(24px) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255,255,255,0.05) !important;
            padding: 16px !important;
            margin-bottom: 12px !important;
        }}
        div[data-testid="stChatMessage"] {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            padding: 12px !important;
            margin: 5px 0 !important;
        }}
        div[data-testid="stChatMessage"] *, div[data-testid="stChatMessage"] p {{
            color: #ffffff !important;
            font-weight: 700 !important;
        }}
        .player-text {{ color: #60a5fa !important; font-weight: 950; }}
        .bot-text {{ color: #fb7185 !important; font-weight: 950; }}
        .move-text {{ color: #fbbf24 !important; font-weight: 950; }}

        /* ── Trainer / battle display ── */
        .battle-display {{
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 15px;
            margin-bottom: 20px;
            min-height: 180px;
        }}
        .trainer-wrapper {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .trainer-img {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            border: 4px solid rgba(255, 255, 255, 0.15);
            object-fit: contain;
            background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 70%);
            box-shadow: 0 10px 25px rgba(0,0,0,0.6);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            margin-bottom: -10px;
        }}
        .trainer-img:hover {{
            transform: scale(1.1) rotate(3deg);
            border-color: #38bdf8;
            box-shadow: 0 0 35px rgba(56, 189, 248, 0.6);
        }}
        .vs-badge {{
            color: #fca5a5;
            font-weight: 950;
            font-size: 2.8rem;
            font-style: italic;
            text-shadow: 3px 3px 0 #7f1d1d, -1px -1px 0 #7f1d1d, 1px -1px 0 #7f1d1d, -1px 1px 0 #7f1d1d, 1px 1px 0 #7f1d1d, 0 10px 20px rgba(0,0,0,0.7);
            z-index: 5;
            letter-spacing: -2px;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}
        .gym-header-container {{
            width: 100%;
            text-align: center;
            padding: 25px 0;
            margin-bottom: 20px;
            background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.1), transparent);
            border-top: 1px solid rgba(56, 189, 248, 0.2);
            border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        }}
        .gym-header-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            color: #38bdf8;
            text-transform: uppercase;
            letter-spacing: 4px;
            text-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        }}
        .leader-portrait-card {{
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 10px;
            text-align: center;
        }}
        .leader-portrait-img {{
            width: 220px;
            height: 320px;
            border-radius: 8px;
            object-fit: contain;
            filter: drop-shadow(0 10px 20px rgba(0,0,0,0.6));
            transition: all 0.4s ease;
            background: rgba(255,255,255,0.05);
        }}
        .leader-portrait-img:hover {{
            transform: scale(1.05) translateY(-5px);
            filter: drop-shadow(0 15px 30px rgba(56, 189, 248, 0.4));
        }}

        /* ════════════════════════════════════════
           Streamlit widget overrides — dark theme
           ════════════════════════════════════════ */

        /* Subheaders */
        [data-testid="stHeading"] h2,
        [data-testid="stHeading"] h3 {{
            font-family: 'Outfit', sans-serif !important;
            color: #f8fafc !important;
            font-weight: 900 !important;
            letter-spacing: 0.5px !important;
        }}

        /* Captions */
        [data-testid="stCaptionContainer"] p {{
            color: rgba(203, 213, 225, 0.85) !important;
            font-weight: 600 !important;
        }}

        /* HR dividers */
        .stMarkdown hr {{
            border-top: 1px solid rgba(148, 163, 184, 0.2) !important;
            margin: 12px 0 !important;
        }}

        /* ════════════════════════════════════════
           버튼 오버라이드 — 3중 셀렉터로 Emotion 우선순위 제압
           ════════════════════════════════════════ */

        /* ── Primary: 파란 그라디언트, 흰 텍스트 ── */
        .stButton > button[kind="primary"],
        div[data-testid="stButton"] > button[data-testid="baseButton-primary"],
        button[data-testid="baseButton-primary"] {{
            background: linear-gradient(135deg, #2a75bb 0%, #38bdf8 100%) !important;
            background-color: #2a75bb !important;
            border: none !important;
            border-radius: 10px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 900 !important;
            letter-spacing: 0.5px !important;
            color: #ffffff !important;
            box-shadow: 0 6px 20px rgba(42, 117, 187, 0.35) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }}
        .stButton > button[kind="primary"] p,
        .stButton > button[kind="primary"] span,
        .stButton > button[kind="primary"] div,
        button[data-testid="baseButton-primary"] p,
        button[data-testid="baseButton-primary"] span,
        button[data-testid="baseButton-primary"] div,
        button[data-testid="baseButton-primary"] * {{
            color: #ffffff !important;
        }}
        .stButton > button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 28px rgba(42, 117, 187, 0.55) !important;
            filter: brightness(1.1) !important;
        }}
        .stButton > button[kind="primary"]:active,
        button[data-testid="baseButton-primary"]:active {{
            transform: translateY(0) !important;
        }}

        /* ── Secondary: 다크 배경, 흰 텍스트 ── */
        .stButton > button[kind="secondary"],
        .stButton > button:not([kind="primary"]),
        div[data-testid="stButton"] > button[data-testid="baseButton-secondary"],
        button[data-testid="baseButton-secondary"] {{
            background: rgba(22, 33, 54, 0.92) !important;
            background-color: #1a2236 !important;
            border: 1px solid rgba(148, 163, 184, 0.35) !important;
            border-radius: 10px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            color: #ffffff !important;
            transition: transform 0.2s ease, border-color 0.2s ease !important;
        }}
        .stButton > button[kind="secondary"] p,
        .stButton > button[kind="secondary"] span,
        .stButton > button[kind="secondary"] div,
        .stButton > button:not([kind="primary"]) p,
        .stButton > button:not([kind="primary"]) span,
        button[data-testid="baseButton-secondary"] p,
        button[data-testid="baseButton-secondary"] span,
        button[data-testid="baseButton-secondary"] div,
        button[data-testid="baseButton-secondary"] * {{
            color: #ffffff !important;
        }}
        .stButton > button[kind="secondary"]:hover,
        button[data-testid="baseButton-secondary"]:hover {{
            background-color: #223050 !important;
            border-color: rgba(56, 189, 248, 0.65) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
        }}
        .stButton > button[kind="secondary"]:active,
        button[data-testid="baseButton-secondary"]:active {{
            transform: translateY(0) !important;
        }}

        /* ── Disabled: 반투명 회색 ── */
        .stButton > button:disabled,
        button[data-testid^="baseButton"]:disabled {{
            background-color: rgba(30, 41, 59, 0.45) !important;
            border-color: rgba(148, 163, 184, 0.12) !important;
            color: rgba(255, 255, 255, 0.3) !important;
            cursor: not-allowed !important;
        }}
        .stButton > button:disabled *,
        button[data-testid^="baseButton"]:disabled * {{
            color: rgba(255, 255, 255, 0.3) !important;
        }}

        /* Selectbox — 컨트롤 */
        .stSelectbox label {{
            color: #ffffff !important;
            font-weight: 900 !important;
            font-size: 0.95rem !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .stSelectbox [data-baseweb="select"] > div:first-child {{
            background-color: #000000 !important;
            border: 1px solid #38bdf8 !important;
            border-radius: 10px !important;
        }}
        /* 선택된 텍스트와 입력 필드 텍스트 강제 화이트 */
        .stSelectbox [data-baseweb="select"] div,
        .stSelectbox [data-baseweb="select"] span,
        .stSelectbox [data-baseweb="select"] input {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
        /* Selectbox — 드랍다운 팝업 (포켓몬 검색 결과 목록) */
        [data-baseweb="popover"] [data-baseweb="menu"],
        [data-baseweb="menu"] {{
            background: rgba(12, 20, 42, 0.98) !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 12px !important;
            box-shadow: 0 12px 40px rgba(0,0,0,0.7) !important;
        }}
        [data-baseweb="menu"] li,
        [data-baseweb="menu-item"],
        li[role="option"] {{
            background: #000000 !important;
            color: #ffffff !important;
        }}
        [data-baseweb="menu"] li:hover,
        [data-baseweb="menu-item"]:hover,
        li[role="option"]:hover {{
            background: rgba(56, 189, 248, 0.18) !important;
            color: #ffffff !important;
        }}
        li[aria-selected="true"],
        [data-baseweb="menu-item"][aria-selected="true"] {{
            background: rgba(56, 189, 248, 0.25) !important;
            color: #ffffff !important;
        }}

        /* Alert / info / warning / success / error */
        div[data-testid="stAlert"] {{
            background: rgba(15, 23, 42, 0.88) !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(8px) !important;
        }}
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span {{
            color: #e2e8f0 !important;
        }}

        /* Radio */
        .stRadio [data-testid="stWidgetLabel"] p {{
            color: rgba(226, 232, 240, 0.85) !important;
            font-weight: 700 !important;
        }}

        /* Chat input */
        [data-testid="stChatInput"] {{
            background: rgba(15, 23, 42, 0.9) !important;
            border: 1px solid rgba(148, 163, 184, 0.25) !important;
            border-radius: 12px !important;
        }}
        .stChatInput textarea {{
            background: transparent !important;
            color: #e2e8f0 !important;
        }}

        /* st.write / st.markdown text */
        .stMarkdown p {{
            color: #e2e8f0;
        }}

        /* ── Leader info card (menu right panel) ── */
        .leader-info-card {{
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            padding: 28px 20px 24px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }}
        .leader-portrait-big {{
            width: 175px;
            height: 255px;
            object-fit: contain;
            filter: drop-shadow(0 15px 30px rgba(0,0,0,0.6));
            transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
        }}
        .leader-portrait-big:hover {{
            transform: scale(1.05) translateY(-6px);
            filter: drop-shadow(0 20px 40px rgba(56,189,248,0.45));
        }}
        .leader-name-big {{
            color: #f8fafc;
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 900;
        }}
        .leader-gym-name {{
            color: #ffffff;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .leader-quote-text {{
            color: #ffffff;
            font-size: 0.85rem;
            font-style: italic;
            line-height: 1.65;
            border-left: 3px solid rgba(56,189,248,0.5);
            padding-left: 12px;
            text-align: left;
            margin-top: 6px;
            width: 100%;
        }}

        /* ── Party slots (builder top bar) ── */
        .party-slot-empty {{
            background: rgba(15, 23, 42, 0.85);
            border: 2px dashed rgba(148,163,184,0.35);
            border-radius: 14px;
            padding: 16px 10px;
            text-align: center;
            color: rgba(203,213,225,0.55);
            font-size: 0.8rem;
            font-weight: 700;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 6px;
            backdrop-filter: blur(8px);
        }}

        /* ── Move selection badges ── */
        .move-selected-badge {{
            background: linear-gradient(135deg, #2a75bb, #38bdf8);
            color: #fff;
            padding: 5px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 800;
            display: inline-block;
        }}
        .move-empty-badge {{
            background: rgba(15, 23, 42, 0.82);
            border: 1px dashed rgba(148,163,184,0.4);
            color: rgba(203,213,225,0.55);
            padding: 5px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            display: inline-block;
        }}

        /* ── Search placeholder card ── */
        .search-placeholder-card {{
            background: rgba(15, 23, 42, 0.85);
            border: 2px dashed rgba(148,163,184,0.3);
            border-radius: 16px;
            padding: 40px 20px;
            text-align: center;
            color: rgba(203,213,225,0.6);
            min-height: 200px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
            backdrop-filter: blur(8px);
        }}
        .search-placeholder-card .placeholder-icon {{
            font-size: 2.5rem;
        }}
        .search-placeholder-card .placeholder-text {{
            font-size: 0.88rem;
            font-weight: 600;
            color: rgba(203,213,225,0.7);
        }}

        /* ════════════════════════════════════════
           사이트 공통 헤더(.top-nav) 보호
           battle 다크 CSS가 nav 텍스트를 덮어쓰지 않도록
           ════════════════════════════════════════ */
        .top-nav {{ background: #ffffff !important; }}
        .top-nav *, .top-nav span, .top-nav a,
        .nav-item, .nav-item span, .nav-item *,
        .nav-aux, .nav-aux span, .nav-aux * {{
            color: #000000 !important;
        }}
        .nav-item:hover, .nav-item:hover * {{ color: #3b82f6 !important; }}

        /* ════════════════════════════════════════
           배틀 콘텐츠 영역 텍스트 화이트
           (nav 제외한 메인 영역만 타겟)
           ════════════════════════════════════════ */
        [data-testid="stMainBlockContainer"] .stMarkdown p,
        [data-testid="stMainBlockContainer"] .stMarkdown li,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {{
            color: #e2e8f0;
        }}
        [data-testid="stText"] {{ color: #e2e8f0 !important; }}
        div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {{
            color: #f8fafc !important;
            font-weight: 700 !important;
        }}
        .stRadio label span {{ color: #e2e8f0 !important; }}
        [data-testid="stImageCaption"] {{ color: rgba(203,213,225,0.8) !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_pokemon_status(title: str, pokemon: BattlePokemon, reveal_details: bool = True, show_moves: bool = True, trainer_image_url: str = None):
    type_html = "".join(f"<span class='type-pill'>{type_name}</span>" for type_name in pokemon.type_names)
    move_html = "".join(f"<span class='move-chip'>{move['name']}</span>" for move in pokemon.moves) if reveal_details and show_moves else ""
    hp_text = f"HP {pokemon.current_hp}/{pokemon.max_hp}" if reveal_details else "HP"
    
    hp_ratio = max(0.0, min(1.0, pokemon.current_hp / pokemon.max_hp))
    hp_percent = hp_ratio * 100
    
    if hp_percent > 50:
        hp_color = "#22c55e"
    elif hp_percent > 20:
        hp_color = "#eab308"
    else:
        hp_color = "#ef4444"

    from .constants import STAT_SHORT_NAMES, STAT_STAGE_MAP
    
    # 스탯 표시 구성 (기본 스탯 + 랭크 변화)
    stat_items = []
    display_stats = ["attack", "defense", "special-attack", "special-defense", "speed"]
    
    stat_items_sidebar = []
    stat_items_inline = [] # 봇용 (랭크 변화만)
    
    for key in display_stats:
        label = STAT_SHORT_NAMES.get(key, key)
        stage_field = STAT_STAGE_MAP.get(key)
        db_key = key.replace("special-", "sp_") if "special" in key else key
        base_val = pokemon.stats.get(db_key, 0)
        stage = getattr(pokemon, stage_field, 0) if stage_field else 0
        
        stage_html = ""
        if stage != 0:
            color = "#ef4444" if stage > 0 else "#3b82f6"
            sign = "+" if stage > 0 else ""
            stage_html = f"<span style='color:{color};'>{sign}{stage}</span>"
            
        if reveal_details:
            # 플레이어용: 사이드바에 전체 정보
            stage_text = f" {stage_html}" if stage_html else ""
            stat_items_sidebar.append(f"<div class='stat-sidebar-item'>{label} {base_val}{stage_text}</div>")
        else:
            # 봇용: 랭크 변화가 있을 때만
            if stage != 0:
                stat_items_inline.append(f"<span class='stat-item' style='margin: 0 2px; background:rgba(15,23,42,0.4); padding:2px 6px; border-radius:4px; font-size:0.75rem;'>{label} {stage_html}</span>")
    
    stat_sidebar_html = f"<div class='stat-sidebar-container'>{''.join(stat_items_sidebar)}</div>" if stat_items_sidebar else ""
    stat_inline_html = f"<div style='margin-top:8px;'>{''.join(stat_items_inline)}</div>" if stat_items_inline else ""

    ailment_html = ""
    if getattr(pokemon, "ailment", None) and pokemon.ailment not in ["none", ""]:
        ailment_map = {
            "paralysis": ("마비", "#eab308"),
            "burn": ("화상", "#ef4444"),
            "poison": ("독", "#a855f7"),
            "sleep": ("잠듦", "#64748b"),
            "freeze": ("얼음", "#38bdf8"),
            "confusion": ("혼란", "#ec4899"),
        }
        kor_name, bg_color = ailment_map.get(pokemon.ailment, (pokemon.ailment, "#64748b"))
        ailment_html = f"<span style='background-color: {bg_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-left: 8px; vertical-align: middle;'>{kor_name}</span>"

    # 기술 목록 생성 (가로/세로 구분)
    if reveal_details and show_moves:
        move_html_v = "".join(f"<div class='move-chip-v'>{move['name']}</div>" for move in pokemon.moves)
        move_sidebar = f"<div class='move-container-vertical'>{move_html_v}{stat_sidebar_html}</div>"
    else:
        move_sidebar = ""

    # HP 영역 구성 (사이즈 동일하게 맞춤)
    label_width = "75px"
    if reveal_details:
        hp_area = (
            f'<div style="width: 100%; margin-top: auto;">'
            f'<div class="hp-label" style="text-align: right; margin-bottom: 4px; padding-right: 5px; font-size: 0.75rem;">{hp_text}</div>'
            f'<div style="display: flex; align-items: center; gap: 10px;">'
            f'<div style="width: {label_width};"></div>'
            f'<div style="flex: 1; height: 16px; background-color: rgba(15, 23, 42, 0.6); border-radius: 8px; overflow: hidden; border: 1px solid rgba(148, 163, 184, 0.3);">'
            f'<div style="width: {hp_percent}%; height: 100%; background-color: {hp_color}; transition: width 0.6s; box-shadow: inset 0 2px 4px rgba(255,255,255,0.15);"></div>'
            f'</div></div></div>'
        )
    else:
        hp_area = (
            f'<div style="width: 100%; margin-top: auto; display: flex; align-items: center; gap: 10px;">'
            f'<div class="hp-label" style="width: {label_width}; text-align: center; font-size: 0.8rem; white-space: nowrap;">{hp_text}</div>'
            f'<div style="flex: 1; height: 16px; background-color: rgba(15, 23, 42, 0.6); border-radius: 8px; overflow: hidden; border: 1px solid rgba(148, 163, 184, 0.3);">'
            f'<div style="width: {hp_percent}%; height: 100%; background-color: {hp_color}; transition: width 0.6s; box-shadow: inset 0 2px 4px rgba(255,255,255,0.15);"></div>'
            f'</div></div>'
        )

    st.markdown(
        f'<div class="status-card" style="height: 400px; display: flex; flex-direction: column;">'
        f'<div style="color:rgba(226,232,240,0.9); font-weight:900; margin-bottom:10px; font-size:0.95rem; letter-spacing:1px; text-transform:uppercase;">{title}</div>'
        f'<div style="display:flex; flex: 1; align-items: center; overflow: hidden;">'
        f'{move_sidebar}'
        f'<div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;">'
        f'<div style="min-height:160px; display:flex; align-items:center;">'
        f'<img src="{pokemon.image_url}" alt="{pokemon.name}" class="pokemon-sprite">'
        f'</div>'
        f'<div class="pokemon-name" style="margin-top: 5px;">{pokemon.name}{ailment_html}</div>'
        f'<div style="margin-bottom: 5px;">{type_html}</div>'
        f'{stat_inline_html}'
        f'</div>'
        f'</div>'
        f'{hp_area}'
        f'</div>',
        unsafe_allow_html=True,
    )
