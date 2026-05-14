import requests
import streamlit as st
import streamlit.components.v1 as _components

from pokedex.constants import REGIONS, TYPE_ORDER, KO_TO_EN, EN_TO_KO
from pokedex.api import fetch_abilities, load_type_icons, BACKEND_URL, API_V1_STR
from pokedex.logic import toggle_type, do_reset, load_more, select_region, handle_search
from pokedex.styles import get_pokedex_styles, render_pokemon_card

_INFINITE_SCROLL_JS = """
<script>
    function findAndClick() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.textContent.includes("더 보기")) {
                btn.parentElement.style.display = 'none';
                btn.click();
                return true;
            }
        }
        return false;
    }
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => { if (entry.isIntersecting) { findAndClick(); } });
    }, { threshold: 0.1 });
    const interval = setInterval(() => {
        const marker = window.parent.document.querySelector('.load-more-marker');
        if (marker) { observer.observe(marker); clearInterval(interval); }
    }, 500);
</script>
"""

_LOAD_MORE_CSS = """
<style>
.load-more-marker + div[data-testid="stButton"] { display: none !important; }
.load-more-marker + div[data-testid="stButton"] button {
    opacity: 0 !important; height: 0 !important;
    padding: 0 !important; margin: 0 !important; pointer-events: none !important;
}
.infinite-loader { display:flex; flex-direction:column; align-items:center; padding:40px 0; gap:10px; color:#888; font-family:'Inter',sans-serif; }
.pokeball-loader {
    width:40px; height:40px; border:3px solid #333; border-radius:50%; position:relative;
    background:linear-gradient(to bottom, #EE1515 50%, white 50%);
    animation:spin 1s linear infinite;
}
.pokeball-loader::after { content:''; position:absolute; width:40px; height:3px; background:#333; top:50%; transform:translateY(-50%); }
.pokeball-loader::before {
    content:''; position:absolute; width:10px; height:10px; background:white;
    border:3px solid #333; border-radius:50%; top:50%; left:50%;
    transform:translate(-50%,-50%); z-index:10;
}
@keyframes spin { from { transform:rotate(0deg); } to { transform:rotate(360deg); } }
</style>
<div class="load-more-marker"></div>
<div class="infinite-loader"><div class="pokeball-loader"></div><span>포켓몬을 더 불러오고 있어요...</span></div>
"""


def show():
    st.write(get_pokedex_styles(), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for key, default in [
        ("pokemon_limit", 50), ("search_query", ""), ("selected_types", []),
        ("region_filter", "전체"), ("dex_start", 1), ("dex_end", 1025),
        ("ability_filter", "전체"), ("abilities_list", ["전체"]),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    if st.session_state.abilities_list == ["전체"]:
        st.session_state.abilities_list = fetch_abilities()

    type_icons = load_type_icons()

    with st.container(border=True):
        st.markdown('<div class="dex-search-card"></div>', unsafe_allow_html=True)
        st.markdown('<div class="dex-top-bg-marker"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="dex-page-title">
            <img src="https://pokemonkorea.co.kr/img/_con.ico" class="dex-title-icon">
            <span>포켓몬 도감</span>
        </div>
        """, unsafe_allow_html=True)

        sc1, sc2 = st.columns([1, 1])
        with sc1:
            st.text_input(
                "검색",
                value=st.session_state.search_query,
                placeholder="포켓몬 이름 또는 설명, 특성 키워드를 입력하세요.",
                key="search_input",
                on_change=handle_search,
            )
        with sc2:
            st.slider("도감번호", min_value=1, max_value=1025,
                      value=(st.session_state.dex_start, st.session_state.dex_end),
                      key="dex_range_slider")

        left_col, right_col = st.columns([1, 1.7])

        with left_col:
            ability_idx = 0
            if st.session_state.ability_filter in st.session_state.abilities_list:
                ability_idx = st.session_state.abilities_list.index(st.session_state.ability_filter)
            st.selectbox("특성", st.session_state.abilities_list, index=ability_idx, key="ability_sel")

            st.markdown('<div class="dex-region-label">지방</div>', unsafe_allow_html=True)
            for region_row in [REGIONS[:5], REGIONS[5:]]:
                rcols = st.columns(len(region_row))
                for rcol, region in zip(rcols, region_row):
                    with rcol:
                        is_sel = region == st.session_state.region_filter
                        st.markdown(
                            f'<div class="region-btn-box {"region-sel" if is_sel else ""}">{region}</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("", key=f"region_btn_{region}", use_container_width=True,
                                     on_click=select_region, args=(region,)):
                            pass

        with right_col:
            st.markdown('<div class="dex-type-label">타입</div>', unsafe_allow_html=True)
            rows = [TYPE_ORDER[:6], TYPE_ORDER[6:12], TYPE_ORDER[12:18]]
            for row in rows:
                cols = st.columns(len(row))
                for col, (ko, en) in zip(cols, row):
                    with col:
                        is_sel = en in st.session_state.selected_types
                        sel_cls = "type-sel" if is_sel else ""
                        svg_icon = type_icons.get(ko, "")
                        icon_html = f'<div class="type-svg-wrap">{svg_icon}</div>' if svg_icon else ""
                        st.markdown(
                            f'<div class="type-icon-box type-bg-{en.lower()} {sel_cls}">'
                            f'{icon_html}<span>{ko}</span></div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("", key=f"type_{en}", use_container_width=True):
                            toggle_type(en)
                            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        _, bc1, bc2, _ = st.columns([2, 2, 2, 2])
        with bc1:
            st.markdown('<div class="dex-btn-search">', unsafe_allow_html=True)
            if st.button("검색", key="btn_search", use_container_width=True):
                handle_search()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with bc2:
            st.markdown('<div class="dex-btn-reset">', unsafe_allow_html=True)
            st.button("초기화", key="btn_reset", use_container_width=True, on_click=do_reset)
            st.markdown("</div>", unsafe_allow_html=True)

    try:
        params = {
            "skip": 0,
            "limit": st.session_state.pokemon_limit,
            "search": st.session_state.search_query or None,
            "ability": st.session_state.ability_filter if st.session_state.ability_filter != "전체" else None,
        }
        response = requests.get(f"{BACKEND_URL}{API_V1_STR}/", params=params)
        if response.status_code == 200:
            data = response.json()
            pokemon_list = data.get("items", [])
            pokemon_list = [
                p for p in pokemon_list
                if st.session_state.dex_start <= (p.get("species_id") or p["id"]) <= st.session_state.dex_end
            ]
            if st.session_state.selected_types:
                selected_ko = {EN_TO_KO[en] for en in st.session_state.selected_types}
                pokemon_list = [
                    p for p in pokemon_list
                    if any(t.get("type_", {}).get("name") in selected_ko for t in p.get("types", []))
                ]
                display_total = 1025
            else:
                display_total = data.get("total", 0)

            if not pokemon_list:
                st.warning("검색 결과가 없습니다.")
            else:
                grid_html = '<div class="pokemon-grid">'
                for p in pokemon_list:
                    p_types_raw = sorted(p.get("types", []), key=lambda x: x.get("slot", 1))
                    p_types = [(t["type_"]["name"], KO_TO_EN.get(t["type_"]["name"], "normal")) for t in p_types_raw]
                    img_url = (p.get("image_url") or
                               "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/1.png")
                    grid_html += render_pokemon_card(p["id"], p["name"], img_url, p_types, display_id=p.get("species_id"))
                grid_html += "</div>"
                st.markdown(grid_html, unsafe_allow_html=True)

                if display_total > st.session_state.pokemon_limit:
                    st.markdown(_LOAD_MORE_CSS, unsafe_allow_html=True)
                    if st.button("더 보기", key="btn_load_more", on_click=load_more):
                        pass
                    _components.html(_INFINITE_SCROLL_JS, height=0)
        else:
            st.error(f"백엔드 서버와 통신할 수 없습니다. (Status: {response.status_code})")
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
