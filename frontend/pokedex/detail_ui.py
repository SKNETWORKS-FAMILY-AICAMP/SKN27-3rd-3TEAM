import os
import requests
import streamlit as st

from pokedex.detail_styles import get_detail_styles
from pokedex.detail_helpers import type_badge_html, render_evo_node

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def show():
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

    with st.spinner("데이터를 불러오는 중..."):
        try:
            response = requests.get(f"{BACKEND_URL}/api/v1/pokemon/{pokemon_id}", timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("types"):
                data["types"] = sorted(data["types"], key=lambda x: x.get("slot", 1))
            main_type = data["types"][0]["type_"]["name"] if data.get("types") else "노말"
            st.markdown(get_detail_styles(main_type), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"데이터를 불러오지 못했습니다: {e}")
            st.stop()

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

    name           = data.get("name", "Unknown")
    img_url        = data.get("image_url") or "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/1.png"
    classification = data.get("classification") or "기록 없음"
    gender_ratio   = data.get("gender_ratio") or ""
    height_m       = (data.get("height") or 0) / 10.0
    weight_kg      = (data.get("weight") or 0) / 10.0
    description    = data.get("description") or "설명이 없습니다."
    game_versions  = data.get("game_versions", [])

    types_html = "".join(type_badge_html(t["type_"]["name"]) for t in data.get("types", [])) \
        or '<span style="color:#888;">정보 없음</span>'

    g = str(gender_ratio).strip()
    if not g or "무성" in g or "없음" in g:
        gender_html = '<span style="color:#888;font-size:0.9rem;">무성</span>'
    elif "수컷만" in g:
        gender_html = '<span class="gender-male">♂</span>'
    elif "암컷만" in g:
        gender_html = '<span class="gender-female">♀</span>'
    else:
        gender_html = '<span class="gender-male">♂</span><span class="gender-female">♀</span>'

    abilities_list = [a["ability"]["name"] for a in data.get("abilities", [])]
    ability_items = "".join(
        f'<div class="ability-item"><span style="font-size:0.85rem;font-weight:600;">{ab}</span>'
        f'<span class="ability-help" title="특성 설명">?</span></div>'
        for ab in abilities_list
    ) or '<span style="color:#888;">정보 없음</span>'
    abilities_html = f'<div class="ability-row">{ability_items}</div>'

    badges_html = "".join(
        f'<span class="v-badge"><span class="v-check">✓</span>{ver}</span>'
        for ver in game_versions
    )
    badges_block = f'<div class="pk-badges">{badges_html}</div>' if badges_html else ""

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

    varieties = data.get("varieties", [])
    if len(varieties) > 1:
        v_items = "".join(
            f'<a href="?id={v["id"]}" target="_self" class="variety-btn {"active" if v["id"] == pokemon_id else ""}">{v["name"]}</a>'
            for v in varieties
        )
        st.markdown(
            f'<div class="variety-section"><div class="variety-title">다른 모습</div><div class="variety-list">{v_items}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="pk-card">'
        f'<div class="pk-card-left"><img src="{img_url}" class="pk-card-img" alt="{name}"></div>'
        f'<div class="pk-card-right">'
        f'<div class="pk-id">No.{data.get("species_id") or pokemon_id:04d}</div>'
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
        f'<a href="/pokedex" target="_self" class="back-btn">{name} 목록으로 돌아가기 ›</a>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    evo_chain = data.get("evolution_chain", [])
    if evo_chain:
        evo_items = "".join(render_evo_node(root, pokemon_id, img_url) for root in evo_chain)
        st.markdown(
            f'<div class="evo-section"><div class="evo-title">진화</div>'
            f'<div style="display:flex; justify-content:center; padding:30px 0; overflow-x:auto; min-width:100%;">{evo_items}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if len(varieties) > 1:
        form_items = ""
        for v in varieties:
            v_id, v_name = v["id"], v["name"]
            v_img = v.get("image_url") or img_url
            is_active = "active" if v_id == pokemon_id else ""
            label = '<div class="form-label">현재</div>' if v_id == pokemon_id else ""
            form_items += (
                f'<a href="?id={v_id}" target="_self" style="text-decoration:none;color:inherit;">'
                f'<div class="form-card {is_active}">{label}'
                f'<img src="{v_img}" class="form-img" alt="{v_name}">'
                f'<div class="form-name">{v_name}</div></div></a>'
            )
        st.markdown(
            f'<div class="forms-section"><div class="forms-title">다양한 모습</div><div class="forms-grid">{form_items}</div></div>',
            unsafe_allow_html=True,
        )
