import streamlit as st


def get_pokedex_styles():
    return """
    <style>
    /* ── Top Background ────────────────────────────── */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    .main {
        background: transparent !important;
    }
    
    /* 동적 높이 컨테이너 배경 (검색/필터/버튼 영역만 정확하게 감싸기) */
    .main div[data-testid="stVerticalBlock"]:has(.dex-top-bg-marker) {
        background-color: #393939;
        margin-left: calc(-50vw + 50%);
        margin-right: calc(-50vw + 50%);
        padding-left: calc(50vw - 50% + 2rem);
        padding-right: calc(50vw - 50% + 2rem);
        padding-top: 20px;
        padding-bottom: 30px;
    }

    /* ── Page Header ───────────────────────────────── */
    .dex-page-header {
        background: #1a1a1a;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 30px;
        margin-bottom: 0;
    }
    .dex-filter-section {
        background: transparent;
        padding: 24px 30px 20px;
        margin-bottom: 30px;
    }
    .dex-header-icon { width: 28px; height: 28px; object-fit: contain; }
    .dex-header-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: white;
    }

    /* ── Search Section ────────────────────────────── */
    .dex-search-header {
        background: #1a1a1a;
        color: white;
        font-weight: 700;
        font-size: 1rem;
        padding: 14px 20px 10px;
        margin-left: calc(-50vw + 50%);
        margin-right: calc(-50vw + 50%);
        padding-left: calc(50vw - 50% + 20px);
        padding-right: calc(50vw - 50% + 20px);
    }

    /* Dark text input */
    [data-testid="stTextInput"] > div {
        background: #1a1a1a !important;
        border-radius: 0 !important;
        border: none !important;
    }
    [data-testid="stTextInput"] input {
        background: #1a1a1a !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 14px 16px !important;
        font-size: 0.95rem !important;
        caret-color: white !important;
    }
    [data-testid="stTextInput"] input::placeholder { color: #888 !important; }

    /* Red 🔍 icon button */
    .dex-filter-section [data-testid="stSelectbox"] label { color: #ffffff !important; font-size: 0.85rem !important; }
    .dex-search-icon-btn [data-testid="stBaseButton-secondary"] {
        background: #E3350D !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        min-height: 3.2rem !important;
        font-size: 1.1rem !important;
        padding: 0 !important;
    }

    /* ── Filter Section ────────────────────────────── */
    .dex-numrange-label {
        color: #888;
        font-size: 0.85rem;
        margin-bottom: 4px;
        margin-top: 8px;
    }
    .dex-range-sep {
        color: #888;
        text-align: center;
        padding-top: 10px;
        font-size: 1.1rem;
    }

    /* ── Type Icon Grid ─────────────────────────────── */
    .dex-type-label {
        color: #888;
        font-size: 0.85rem;
        margin-bottom: 16px;
    }

    .type-icon-box {
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 6px 2px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 64px;
        max-width: 75px; /* 가로 넓이 좁히기 */
        margin: 0 auto 16px auto; /* 가운데 정렬 및 위아래 간격 넓히기 */
        cursor: pointer;
        transition: border 0.15s;
    }

    /* 타입 아이콘 컬럼 가로 간격 좁히기 (부모 레이아웃 영향 방지) */
    div[data-testid="stColumn"] div[data-testid="stHorizontalBlock"]:has(.type-icon-box) {
        gap: 8px !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stColumn"] div[data-testid="stColumn"]:has(.type-icon-box) {
        flex: 0 0 auto !important;
        width: 75px !important;
        min-width: 75px !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    .type-svg-wrap {
        width: 36px;
        height: 36px;
        margin-bottom: 4px;
    }
    .type-svg-wrap svg {
        width: 36px !important;
        height: 36px !important;
    }
    .type-icon-box span {
        font-size: 0.65rem;
        color: #333;
        font-weight: 500;
    }
    .type-icon-box.type-sel {
        border: 2px solid #E3350D;
        background: #fff5f5;
    }

    /* Overlay the invisible Streamlit button over the icon box */
    div[data-testid="stColumn"]:has(.type-icon-box) [data-testid="stVerticalBlock"] {
        position: relative;
    }
    div[data-testid="stColumn"]:has(.type-icon-box) [data-testid="stVerticalBlock"] > .element-container:last-child {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        z-index: 5;
    }
    div[data-testid="stColumn"]:has(.type-icon-box) [data-testid="stBaseButton-secondary"] {
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
        padding: 0 !important;
    }

    /* ── Action Buttons ─────────────────────────────── */
    .dex-btn-search [data-testid="stBaseButton-secondary"] {
        background: #E3350D !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        font-weight: 700 !important;
        transform: skew(-12deg) !important;
        font-size: 1rem !important;
        letter-spacing: 0.05em !important;
    }
    .dex-btn-reset [data-testid="stBaseButton-secondary"] {
        background: #1a1a1a !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        font-weight: 700 !important;
        transform: skew(-12deg) !important;
        font-size: 1rem !important;
        letter-spacing: 0.05em !important;
    }

    /* ── Pokemon Grid ───────────────────────────────── */
    .pokemon-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 20px;
        padding: 0 20px 40px;
    }

    .pokemon-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        transition: transform 0.2s;
        cursor: pointer;
        border: 1px solid #e0e0e0;
        text-decoration: none !important;
        display: flex;
        flex-direction: column;
    }
    .pokemon-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }

    .pokemon-image-wrapper {
        padding: 10px;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 160px;
    }
    .pokemon-image {
        width: 130px;
        height: 130px;
        object-fit: contain;
    }

    .pokemon-info { padding-top: 10px; text-align: left; }
    .pokemon-id-badge { color: #999; font-size: 0.8rem; margin-bottom: 3px; }
    .pokemon-name { font-weight: 700; font-size: 1.05rem; color: #333; margin-bottom: 12px; }

    .type-container { display: flex; justify-content: center; gap: 5px; }
    .type-badge {
        flex: 1; padding: 5px 0; border-radius: 4px;
        font-size: 0.72rem; font-weight: 600; color: white; text-align: center;
    }

    /* Type badge colours */
    .type-normal   { background: #A8A77A; }
    .type-fire     { background: #F08030; }
    .type-water    { background: #6890F0; }
    .type-electric { background: #F8D030; color: #333; }
    .type-grass    { background: #78C850; }
    .type-ice      { background: #98D8D8; color: #333; }
    .type-fighting { background: #C03028; }
    .type-poison   { background: #A040A0; }
    .type-ground   { background: #E0C068; color: #333; }
    .type-flying   { background: #A890F0; }
    .type-psychic  { background: #F85888; }
    .type-bug      { background: #A8B820; }
    .type-rock     { background: #B8A038; }
    .type-ghost    { background: #705898; }
    .type-dragon   { background: #7038F8; }
    .type-steel    { background: #B8B8D0; color: #333; }
    .type-fairy    { background: #EE99AC; color: #333; }
    .type-dark     { background: #705848; }

    /* ── Load More ──────────────────────────────────── */
    .load-more-container { display: flex; justify-content: center; padding: 20px 0 40px; }
    </style>
    """


def render_pokemon_card(id, name, image_url, types_ko_en):
    type_badges = "".join(
        [f'<span class="type-badge type-{en.lower()}">{ko}</span>' for ko, en in types_ko_en]
    )
    return f'''<a href="/pokemon_detail?id={id}" target="_self" class="pokemon-card">
<div class="pokemon-image-wrapper">
<img src="{image_url}" class="pokemon-image" alt="{name}" loading="lazy">
</div>
<div class="pokemon-info">
<div class="pokemon-id-badge">No.{id:04d}</div>
<div class="pokemon-name">{name}</div>
<div class="type-container">{type_badges}</div>
</div>
</a>'''
