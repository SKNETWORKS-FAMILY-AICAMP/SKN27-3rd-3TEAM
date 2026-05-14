import streamlit as st
import base64
import os
from .data import BattlePokemon

def fmt_player(name: str) -> str:
    return f"<span class='player-text'>{name}</span>"

def fmt_bot(name: str) -> str:
    return f"<span class='bot-text'>{name}</span>"

def fmt_move(name: str) -> str:
    return f"<span class='move-text'>{name}</span>"

from pathlib import Path

LEADER_IMAGE_MAP = {
    "웅이": "웅이_이미지.png",
    "이슬이": "이슬_이미지.png",
    "아이리스": "아이리스_이미지.png",
    "민화": "민화_이미지.png",
    "풍란": "풍란_이미지.png",
    "채두": "채두_이미지.png",
    "순무": "순무_이미지.png",
    "지우": "지우_이미지.png",
    "N": "N_이미지.png"
}

GYM_NAME_MAP = {
    "웅이": "1. 콘스탄트(Constant) 체육관",
    "이슬이": "2. 데이터 레이크(Data Lake) 체육관",
    "순무": "3. 오버클럭(Overclock) 체육관",
    "민화": "4. 랜덤 포레스트(Random Forest) 체육관",
    "풍란": "5. 클라우드(Cloud) 체육관",
    "채두": "6. 포스(force) 체육관",
    "아이리스": "7. 딥러닝(Deep Learning) 체육관",
    "지우": "8. 자율 에이전트(Autonomous Agent) 리그",
    "N": "Final. 플라스마단(Team Plasma) 성"
}

GYM_BG_MAP = {
    "웅이": "웅이_체육관.png",
    "이슬이": "이슬_체육관.png",
    "아이리스": "아이리스_체육관.png",
    "민화": "민화_체육관.png",
    "풍란": "풍란_체육관.png",
    "채두": "채두_체육관.png",
    "순무": "순무_체육관.png",
    "지우": "지우_체육관.png",
    "N": "N_체육관.png"
}

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
        .stApp {{ {bg_style} }}
        .stApp::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15, 23, 42, 0.6);
            z-index: -1;
        }}
        [data-testid="stAppViewBlockContainer"] {{
            max-width: 1180px;
            padding-top: 1.2rem;
        }}
        .battle-header {{
            border: 1px solid rgba(148, 163, 184, .28);
            border-radius: 8px;
            padding: 18px;
            background: rgba(15, 23, 42, .78);
            margin-bottom: 16px;
        }}
        .battle-header h1 {{
            margin: 0;
            color: #f8fafc;
            font-size: 2rem;
            letter-spacing: 0;
        }}
        .battle-header p {{
            color: rgba(226, 232, 240, .78);
            margin: 8px 0 0;
        }}
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
        /* 추가 효과: 스캔라인 */
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
        .stat-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 4px;
            margin-top: 8px;
        }}
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
        .chat-tip {{
            color: rgba(226,232,240,.72);
            font-size: .9rem;
            margin: 8px 0 14px;
        }}
        /* 반투명 컨테이너 스타일링 (배틀로그, 커맨드 영역) */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(15, 23, 42, 0.95) !important;
            border: 1px solid rgba(148, 163, 184, 0.3) !important;
            border-radius: 12px !important;
            backdrop-filter: blur(25px) !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6) !important;
            padding: 10px !important;
            margin-bottom: 10px !important;
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
            margin-bottom: -10px; /* 약간 겹치게 */
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
            background: rgba(15, 23, 42, 0.6);
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
            margin-bottom: -10px; /* 약간 겹치게 */
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
            background: rgba(15, 23, 42, 0.6);
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
