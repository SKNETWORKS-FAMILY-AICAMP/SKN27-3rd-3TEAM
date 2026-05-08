import streamlit as st
import requests
import os
import sys
import urllib.parse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from utils.ui import inject_common_ui
from pages.style.detail_styles import get_detail_styles

st.set_page_config(
    page_title="포켓몬 비공식 사이트",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject common UI (Header)
inject_common_ui(spacer=True)

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# ── Query params ─────────────────────────────────────────────────────────────
query_params = st.query_params
pokemon_id_str = query_params.get("id", None)
if not pokemon_id_str:
    st.error("포켓몬 ID가 지정되지 않았습니다.")
    st.stop()
try:
    pokemon_id = int(pokemon_id_str)
except ValueError:
    st.error("유효하지 않은 포켓몬 ID입니다.")
    st.stop()

# ── Fetch current Pokémon ────────────────────────────────────────────────────
with st.spinner("데이터를 불러오는 중..."):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/pokemon/{pokemon_id}", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # 포켓몬의 타입 목록을 slot 순서대로 정렬
        if data.get("types"):
            data["types"] = sorted(data["types"], key=lambda x: x.get("slot", 1))
            
        # 포켓몬의 첫 번째 타입 추출 (배경용)
        main_type = "노말"
        if data.get("types"):
            main_type = data["types"][0]["type_"]["name"]
        st.markdown(get_detail_styles(main_type), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"데이터를 불러오지 못했습니다: {e}")
        st.stop()

# ── Fetch prev / next (silent) ───────────────────────────────────────────────
prev_data, next_data = None, None
if pokemon_id > 1:
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/pokemon/{pokemon_id - 1}", timeout=3)
        if r.ok:
            prev_data = r.json()
    except Exception:
        pass
try:
    r = requests.get(f"{BACKEND_URL}/api/v1/pokemon/{pokemon_id + 1}", timeout=3)
    if r.ok:
        next_data = r.json()
except Exception:
    pass

# ── Prepare data ─────────────────────────────────────────────────────────────
name           = data.get("name", "Unknown")
img_url        = data.get("image_url") or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/1.png"
classification = data.get("classification") or "기록 없음"
gender_ratio   = data.get("gender_ratio") or ""
height_m       = (data.get("height") or 0) / 10.0
weight_kg      = (data.get("weight") or 0) / 10.0
description    = data.get("description") or "설명이 없습니다."
game_versions  = data.get("game_versions", [])

# Type image loader (SVG → base64 data URI)
TYPE_IMG_DIR = os.path.join(current_dir, "..", "img", "type")
# API name → filename (대부분 동일, 얼음만 예외)
TYPE_FILE_MAP = {"얼음": "아이스"}

def get_type_img_src(ko_name: str) -> str:
    filename = TYPE_FILE_MAP.get(ko_name, ko_name)
    path = os.path.join(TYPE_IMG_DIR, f"{filename}.svg")
    try:
        with open(path, "r", encoding="utf-8") as f:
            svg = f.read()
        return f"data:image/svg+xml,{urllib.parse.quote(svg)}"
    except FileNotFoundError:
        return ""

def type_badge_html(ko: str) -> str:
    src = get_type_img_src(ko)
    if src:
        return (
            f'<div style="display:inline-flex;flex-direction:column;align-items:center;'
            f'gap:4px;margin-right:10px;">'
            f'<img src="{src}" width="30" height="30">'
            f'<span style="font-size:0.78rem;font-weight:600;color:#eee;">{ko}</span>'
            f'</div>'
        )
    return f'<span style="font-size:0.9rem;font-weight:600;color:#eee;">{ko}</span>'

types_html = "".join(
    type_badge_html(t["type_"]["name"]) for t in data.get("types", [])
) or '<span style="color:#888;">정보 없음</span>'

# Gender
g = str(gender_ratio).strip()
if not g or "무성" in g or "없음" in g:
    gender_html = '<span style="color:#888;font-size:0.9rem;">무성</span>'
elif "수컷만" in g:
    gender_html = '<span class="gender-male">♂</span>'
elif "암컷만" in g:
    gender_html = '<span class="gender-female">♀</span>'
else:
    gender_html = '<span class="gender-male">♂</span><span class="gender-female">♀</span>'

# Abilities
abilities_list = [a["ability"]["name"] for a in data.get("abilities", [])]
ability_items = "".join(
    f'<div class="ability-item"><span style="font-size:0.85rem;font-weight:600;">{ab}</span><span class="ability-help" title="특성 설명">?</span></div>'
    for ab in abilities_list
) or '<span style="color:#888;">정보 없음</span>'
abilities_html = f'<div class="ability-row">{ability_items}</div>'

# Version badges
badges_html = "".join(
    f'<span class="v-badge"><span class="v-check">✓</span>{ver}</span>'
    for ver in game_versions
)
badges_block = f'<div class="pk-badges">{badges_html}</div>' if badges_html else ""

# ── Nav bar ───────────────────────────────────────────────────────────────────
if prev_data:
    pid, pname = pokemon_id - 1, prev_data.get("name", "")
    nav_left = f'<a href="?id={pid}" target="_self" class="pk-nav-left"><div class="nav-circle">◀</div><div><div class="pk-nav-num">No.{pid:04d}</div><div class="pk-nav-name">{pname}</div></div></a>'
else:
    nav_left = '<div class="pk-nav-left" style="opacity:0.25;pointer-events:none;"><div class="nav-circle">◀</div></div>'

if next_data:
    nid, nname = pokemon_id + 1, next_data.get("name", "")
    nav_right = f'<a href="?id={nid}" target="_self" class="pk-nav-right"><div><div class="pk-nav-num">No.{nid:04d}</div><div class="pk-nav-name">{nname}</div></div><div class="nav-circle">▶</div></a>'
else:
    nav_right = '<div class="pk-nav-right" style="opacity:0.25;pointer-events:none;"><div class="nav-circle">▶</div></div>'

st.markdown(
    f'<div class="pk-nav">{nav_left}<div class="pk-nav-sep"></div>{nav_right}</div>',
    unsafe_allow_html=True,
)

# ── Varieties Selector ───────────────────────────────────────────────────────
varieties = data.get("varieties", [])
if len(varieties) > 1:
    v_items = ""
    for v in varieties:
        v_id, v_name = v["id"], v["name"]
        is_active = "active" if v_id == pokemon_id else ""
        v_items += f'<a href="?id={v_id}" target="_self" class="variety-btn {is_active}">{v_name}</a>'
    
    st.markdown(
        f'<div class="variety-section"><div class="variety-title">다른 모습</div><div class="variety-list">{v_items}</div></div>',
        unsafe_allow_html=True
    )

# ── Main card (no leading whitespace to avoid markdown code-block parsing) ───
st.markdown(
    f'<div class="pk-card">'
    f'<div class="pk-card-left"><img src="{img_url}" class="pk-card-img" alt="{name}"></div>'
    f'<div class="pk-card-right">'
    f'<div class="pk-id">No.{pokemon_id:04d}</div>'
    f'<div class="pk-name">{name}</div>'
    f'{badges_block}'
    f'<div class="pk-desc">{description}</div>'
    f'<div class="pk-stats">'
    f'<div class="pk-stat-cell"><div class="pk-stat-label">타입</div><div class="pk-stat-value">{types_html}</div></div>'
    f'<div class="pk-stat-cell"><div class="pk-stat-label">키</div><div class="pk-stat-value">{height_m}m</div></div>'
    f'<div class="pk-stat-cell"><div class="pk-stat-label">분류</div><div class="pk-stat-value">{classification}</div></div>'
    f'<div class="pk-stat-cell"><div class="pk-stat-label">성별</div><div class="pk-stat-value">{gender_html}</div></div>'
    f'<div class="pk-stat-cell"><div class="pk-stat-label">몸무게</div><div class="pk-stat-value">{weight_kg}kg</div></div>'
    f'<div class="pk-stat-cell"><div class="pk-stat-label">특성</div><div class="pk-stat-value">{abilities_html}</div></div>'
    f'</div>'
    f'<a href="/pokedex" target="_self" class="pk-cta">{name} 목록으로 돌아가기 ›</a>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Evolution chain ──────────────────────────────────────────────────────────
evo_chain = data.get("evolution_chain", [])

def render_evo_node(node, is_root=True):
    # Determine which varieties to show (Default + Regional forms like Hisui, Alola, etc.)
    all_vars = node.get("varieties", [])
    
    # Filter for default or regional forms (simple name matching for now)
    display_vars = [v for v in all_vars if v["is_default"] or any(x in v["name"] for x in ["히스이", "알로라", "가라르", "팔데아"])]
    if not display_vars and all_vars:
        display_vars = [all_vars[0]]

    # Render cards for each variety in this evolution step
    var_htmls = []
    for v in display_vars:
        v_id, v_name = v["id"], v["name"]
        v_img = v.get("image_url") or img_url
        is_active = "border: 2px solid #E3350D; background: #fff8f8;" if v_id == pokemon_id else ""
        
        # Build type badges for this variety
        v_types_html = "".join([
            f'<div style="background:#efefef; border-radius:4px; padding:2px 6px; font-size:0.65rem; color:#666; font-weight:600;">{t["type_"]["name"]}</div>'
            for t in v.get("types", [])
        ])
        
        var_htmls.append(f'''<a href="?id={v_id}" target="_self" style="text-decoration:none; color:inherit;"><div class="evo-card" style="{is_active}"><img src="{v_img}" class="evo-img" alt="{v_name}"><div style="font-size:0.85rem; color:rgba(255,255,255,0.6); margin-top:10px; font-weight:600;">No.{v_id:04d}</div><div style="font-weight:800; font-size:1.05rem; color:#fff; margin-bottom:12px; font-family:\'Outfit\', sans-serif;">{v_name}</div><div style="display:flex; justify-content:center; gap:6px;">{v_types_html}</div></div></a>''')
    
    varieties_block = "".join(var_htmls)
    
    # Combined block for this step
    step_html = f'<div style="display:flex; flex-direction:column; align-items:center; gap:10px;">{varieties_block}</div>'
    
    children = node.get("evolves_to", [])
    if children:
        child_htmls = [render_evo_node(child, is_root=False) for child in children]
        
        # Branching layout with arrows
        children_combined = "".join([
            f'<div style="display:flex; align-items:center; gap:15px;"><div class="evo-arrow">▶</div>{ch}</div>' 
            for ch in child_htmls
        ])
        
        return f'<div style="display:flex; align-items:center; gap:15px;">{step_html}<div style="display:flex; flex-direction:column; gap:25px;">{children_combined}</div></div>'
    return step_html

if evo_chain:
    # Start rendering from root nodes
    evo_items = "".join([render_evo_node(root) for root in evo_chain])
    st.markdown(
        f'<div class="evo-section"><div class="evo-title">진화</div>'
        f'<div style="display:flex; justify-content:center; padding:30px 0; overflow-x:auto; min-width: 100%;">{evo_items}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Forms Section (All Varieties) ────────────────────────────────────────────
if len(varieties) > 1:
    form_items = ""
    for v in varieties:
        v_id, v_name = v["id"], v["name"]
        v_img = v.get("image_url") or img_url
        is_active = "active" if v_id == pokemon_id else ""
        label = '<div class="form-label">현재</div>' if v_id == pokemon_id else ""
        
        form_items += (
            f'<a href="?id={v_id}" target="_self" style="text-decoration:none;color:inherit;">'
            f'<div class="form-card {is_active}">'
            f'{label}'
            f'<img src="{v_img}" class="form-img" alt="{v_name}">'
            f'<div class="form-name">{v_name}</div>'
            f'</div></a>'
        )
    
    st.markdown(
        f'<div class="forms-section"><div class="forms-title">다양한 모습</div><div class="forms-grid">{form_items}</div></div>',
        unsafe_allow_html=True
    )
