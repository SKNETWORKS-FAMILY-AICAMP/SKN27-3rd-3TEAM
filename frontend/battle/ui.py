import streamlit as st
from .data import BattlePokemon

def fmt_player(name: str) -> str:
    return f"<span class='player-text'>{name}</span>"

def fmt_bot(name: str) -> str:
    return f"<span class='bot-text'>{name}</span>"

def fmt_move(name: str) -> str:
    return f"<span class='move-text'>{name}</span>"

def inject_battle_styles():
    st.markdown(
        """
        <style>
        .stApp { background: #0f172a; }
        [data-testid="stAppViewBlockContainer"] {
            max-width: 1180px;
            padding-top: 1.2rem;
        }
        .battle-header {
            border: 1px solid rgba(148, 163, 184, .28);
            border-radius: 8px;
            padding: 18px;
            background: rgba(15, 23, 42, .78);
            margin-bottom: 16px;
        }
        .battle-header h1 {
            margin: 0;
            color: #f8fafc;
            font-size: 2rem;
            letter-spacing: 0;
        }
        .battle-header p {
            color: rgba(226, 232, 240, .78);
            margin: 8px 0 0;
        }
        .status-card {
            border: 1px solid rgba(148, 163, 184, .24);
            border-radius: 8px;
            background: rgba(30, 41, 59, .7);
            padding: 14px;
            text-align: center;
        }
        .status-card img {
            width: 150px;
            height: 150px;
            object-fit: contain;
            filter: drop-shadow(0 16px 24px rgba(0,0,0,.38));
        }
        .pokemon-name {
            color: #fff;
            font-weight: 900;
            font-size: 1.2rem;
        }
        .type-pill {
            display: inline-flex;
            padding: 3px 9px;
            margin: 6px 3px 0;
            border-radius: 999px;
            background: rgba(15, 23, 42, .85);
            color: #e5e7eb;
            font-size: .8rem;
            font-weight: 800;
        }
        .hp-label {
            color: #e5e7eb;
            font-weight: 800;
            font-size: .88rem;
            margin-top: 8px;
        }
        .move-chip {
            display: inline-flex;
            margin: 3px;
            padding: 5px 9px;
            border-radius: 999px;
            background: rgba(59, 130, 246, .18);
            border: 1px solid rgba(96, 165, 250, .28);
            color: #dbeafe;
            font-size: .84rem;
            font-weight: 800;
        }
        .stat-badge {
            display: inline-flex;
            margin: 2px;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 800;
            color: #fff;
        }
        .stat-up { background: #ef4444; }
        .stat-down { background: #3b82f6; }
        .stat-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 4px;
            margin-top: 8px;
        }
        .stat-item {
            background: rgba(15, 23, 42, 0.4);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.75rem;
            color: #cbd5e1;
            font-weight: 700;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        .secret-card {
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
        }
        .chat-tip {
            color: rgba(226,232,240,.72);
            font-size: .9rem;
            margin: 8px 0 14px;
        }
        div[data-testid="stChatMessage"] {
            background: #ffffff;
            border: 1px solid rgba(15, 23, 42, .16);
            border-radius: 8px;
            color: #000000 !important;
        }
        div[data-testid="stChatMessage"] * { color: #000000 !important; }
        div[data-testid="stChatMessage"] p {
            color: #000000 !important;
            font-weight: 650;
            line-height: 1.58;
        }
        .player-text { color: #0066ff !important; font-weight: 900; }
        .bot-text { color: #e11d48 !important; font-weight: 900; }
        .move-text { color: #c2410c !important; font-weight: 950; }
        h2, h3, label, p { color: #f8fafc; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_pokemon_status(title: str, pokemon: BattlePokemon, reveal_details: bool = True, show_moves: bool = True):
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
    
    for key in display_stats:
        label = STAT_SHORT_NAMES.get(key, key)
        stage_field = STAT_STAGE_MAP.get(key)
        
        # ui 표기를 위한 필드 변환 (ui의 데이터 구조상 sp_attack 등을 키로 쓰는지 확인)
        # 만약 db의 stats 내 키 이름이 sp_attack이라면:
        db_key = key.replace("special-", "sp_") if "special" in key else key
        base_val = pokemon.stats.get(db_key, 0)
        
        stage = getattr(pokemon, stage_field, 0) if stage_field else 0
        
        stage_html = ""
        if stage != 0:
            color = "#ef4444" if stage > 0 else "#3b82f6"
            sign = "+" if stage > 0 else ""
            stage_html = f"<span style='color:{color};'>{sign}{stage}</span>"
            
        if reveal_details:
            # 플레이어: 전체 스탯 + 랭크 변화 표시
            stage_text = f" ({stage_html})" if stage_html else ""
            stat_items.append(f"<span class='stat-item'>{label} {base_val}{stage_text}</span>")
        else:
            # 봇: 랭크 변화가 있는 경우에만 해당 스탯 이름과 랭크 표시
            if stage != 0:
                stat_items.append(f"<span class='stat-item'>{label} {stage_html}</span>")
    
    stat_html = f"<div class='stat-container'>{''.join(stat_items)}</div>" if stat_items else ""

    st.markdown(
        f"""
<div class="status-card" style="min-height: 280px;">
<div style="color:rgba(226,232,240,.72);font-weight:900;">{title}</div>
<img src="{pokemon.image_url}" alt="{pokemon.name}">
<div class="pokemon-name">{pokemon.name}</div>
<div>{type_html}</div>
<div class="hp-label">{hp_text}</div>
{stat_html}
<div style="margin-top:8px; margin-bottom: 14px;">{move_html}</div>
<div style="width: 100%; height: 24px; background-color: rgba(15, 23, 42, 0.6); border-radius: 12px; overflow: hidden; border: 1px solid rgba(148, 163, 184, 0.3);">
<div style="width: {hp_percent}%; height: 100%; background-color: {hp_color}; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: inset 0 2px 4px rgba(255,255,255,0.15);"></div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )
