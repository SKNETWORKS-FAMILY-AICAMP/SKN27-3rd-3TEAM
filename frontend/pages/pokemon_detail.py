import streamlit as st
import requests
import os
import sys

# 백엔드 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from utils.ui import inject_common_ui

st.set_page_config(
    page_title="Pokemon Detail",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject common UI (Header)
inject_common_ui(spacer=True)

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# Hide sidebar completely for detail page to match mockup
st.markdown("""
<style>
[data-testid="collapsedControl"] { display: none; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Background pattern */
.stApp {
    background-color: #f2f2f2;
    background-image: radial-gradient(#d5d5d5 1px, transparent 1px);
    background-size: 20px 20px;
}

.detail-nav {
    background-color: #313131;
    padding: 15px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: -60px;
    margin-left: -50px;
    margin-right: -50px;
    margin-bottom: 40px;
}

.nav-btn {
    color: white;
    text-decoration: none;
    font-size: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.main-card {
    background: white;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    max-width: 800px;
    margin: 0 auto;
    padding: 40px;
    text-align: center;
    position: relative;
}

.detail-id {
    color: #999;
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    margin-bottom: 5px;
}

.detail-name {
    font-size: 2.5rem;
    font-weight: 800;
    color: #1a1a1a;
    margin-bottom: 30px;
}

.detail-image {
    width: 250px;
    height: 250px;
    object-fit: contain;
    margin: 0 auto 30px auto;
    display: block;
}

.detail-desc {
    color: #666;
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 40px;
    padding: 0 40px;
}

.info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    text-align: left;
    border-top: 1px solid #eee;
    padding-top: 20px;
}

.info-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.info-label {
    color: #999;
    font-size: 0.85rem;
}

.info-value {
    color: #333;
    font-weight: 600;
    font-size: 1rem;
}

/* Type Badge Mapping */
.t-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    color: white;
    font-size: 0.8rem;
    font-weight: bold;
    margin-right: 5px;
}
.t-normal { background: #A8A77A; }
.t-fire { background: #F08030; }
.t-water { background: #6890F0; }
.t-grass { background: #78C850; }
.t-electric { background: #F8D030; color: #333; }
.t-poison { background: #A040A0; }

.btn-red {
    background-color: #E3350D;
    color: white;
    border: none;
    padding: 15px 40px;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 4px;
    margin-top: 40px;
    cursor: pointer;
    display: inline-block;
    text-decoration: none;
}

/* Evolution Section */
.evo-section {
    max-width: 800px;
    margin: 40px auto;
    background: white;
    border-radius: 10px;
    padding: 30px;
}

.evo-title {
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.evo-chain {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
}

.evo-card {
    text-align: center;
    border: 1px solid #eee;
    border-radius: 10px;
    padding: 15px;
    width: 150px;
}

.evo-img {
    width: 100px;
    height: 100px;
    object-fit: contain;
}

.evo-arrow {
    color: #ccc;
    font-size: 24px;
}
</style>
""", unsafe_allow_html=True)

# Parse query params
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

# Fetch data
with st.spinner("데이터를 불러오는 중..."):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/pokemon/{pokemon_id}", timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"데이터를 불러오지 못했습니다: {e}")
        st.stop()

# Prepare Data
name = data.get("name", "Unknown")
img_url = data.get("image_url") or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/1.png"

# Mock missing data from DB
classification = "씨앗포켓몬"
gender_ratio = "♂ 87.5% ♀ 12.5%"

height_m = (data.get("height") or 0) / 10.0
weight_kg = (data.get("weight") or 0) / 10.0

types_html = ""
type_map = {
    "노말": "normal", "불꽃": "fire", "물": "water", "풀": "grass", "전기": "electric", "독": "poison"
}
for t in data.get("types", []):
    ko_name = t["type_"]["name"]
    en_class = type_map.get(ko_name, "normal")
    types_html += f'<span class="t-badge t-{en_class}">{ko_name}</span>'

abilities_list = [a["ability"]["name"] for a in data.get("abilities", [])]
abilities_str = ", ".join(abilities_list) if abilities_list else "심록"

# Render Nav
st.markdown(f'''<div class="detail-nav">
<a href="/pokedex" target="_self" class="nav-btn">← 뒤로가기</a>
<div style="color:white; font-size:1.2rem;">No.{pokemon_id:04d} {name}</div>
<div style="width: 100px;"></div>
</div>''', unsafe_allow_html=True)

# Render Main Card
st.markdown(f'''<div class="main-card">
<div class="detail-id">No.{pokemon_id:04d}</div>
<div class="detail-name">{name}</div>
<img src="{img_url}" class="detail-image" alt="{name}">
<div class="detail-desc">
태어났을 때부터 등에 식물의 씨앗이 있다. 태어날 때부터 등에 있는 이상한 씨앗과 함께 성장한다.
</div>
<div class="info-grid">
<div class="info-item">
<span class="info-label">타입</span>
<div style="margin-top:5px;">{types_html}</div>
</div>
<div class="info-item">
<span class="info-label">키</span>
<span class="info-value">{height_m}m</span>
</div>
<div class="info-item">
<span class="info-label">분류</span>
<span class="info-value">{classification}</span>
</div>
<div class="info-item">
<span class="info-label">몸무게</span>
<span class="info-value">{weight_kg}kg</span>
</div>
<div class="info-item">
<span class="info-label">성별</span>
<span class="info-value">{gender_ratio}</span>
</div>
<div class="info-item">
<span class="info-label">특성</span>
<span class="info-value">{abilities_str}</span>
</div>
</div>
<a href="/pokedex" target="_self" class="btn-red">목록으로 돌아가기</a>
</div>''', unsafe_allow_html=True)

# Render Evolution Chain
evo_chain = data.get("evolution_chain", [])
if evo_chain:
    evo_html = '<div class="evo-section"><div class="evo-title">🔴 진화</div><div class="evo-chain">'
    for i, evo in enumerate(evo_chain):
        if i > 0:
            evo_html += '<div class="evo-arrow">▶</div>'
        e_id = evo["id"]
        e_name = evo["name"]
        e_img = evo.get("image_url") or img_url
        evo_html += f'''<a href="?id={e_id}" target="_self" style="text-decoration:none; color:inherit;">
<div class="evo-card">
<img src="{e_img}" class="evo-img">
<div style="font-size:0.8rem; color:#999; margin-top:10px;">No.{e_id:04d}</div>
<div style="font-weight:bold;">{e_name}</div>
</div>
</a>'''
    evo_html += '</div></div>'
    st.markdown(evo_html, unsafe_allow_html=True)

