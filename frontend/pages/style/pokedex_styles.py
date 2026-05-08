def get_pokedex_styles():
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600&display=swap');

    :root {
        --poke-yellow: #FFCB05;
        --poke-blue: #2A75BB;
        --light-glass-bg: rgba(255, 255, 255, 0.8);
        --light-glass-border: rgba(0, 0, 0, 0.05);
        --main-bg: #f8f9fa;
        --text-main: #1a1a1a;
        --text-muted: #666;
    }

    /* ── Global Styles ────────────────────────────── */
    [data-testid="stAppViewContainer"] {
        background-color: var(--main-bg) !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(42, 117, 187, 0.03) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(255, 203, 5, 0.03) 0%, transparent 40%) !important;
        background-attachment: fixed !important;
    }
    .main { background: transparent !important; }

    /* ── Search & Filter Section (White Glass Card) ── */
    .main div[data-testid="stVerticalBlock"]:has(.dex-top-bg-marker) {
        background: white !important;
        border: 1px solid var(--light-glass-border) !important;
        border-radius: 30px !important;
        margin-left: 20px !important;
        margin-right: 20px !important;
        padding: 40px !important;
        box-shadow: 0 15px 40px rgba(0,0,0,0.06) !important;
    }

    /* ── Inputs & Selects ──────────────────────────── */
    /* Search Bar */
    [data-testid="stTextInput"] label { display: none; }
    [data-testid="stTextInput"] > div {
        background: #f1f3f5 !important;
        border: 1px solid transparent !important;
        border-radius: 15px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stTextInput"] > div:focus-within {
        background: white !important;
        border-color: var(--poke-blue) !important;
        box-shadow: 0 0 15px rgba(42, 117, 187, 0.1) !important;
    }
    [data-testid="stTextInput"] input {
        color: var(--text-main) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.1rem !important;
        padding: 15px 20px !important;
    }

    /* Selectboxes & Number Inputs */
    [data-testid="stSelectbox"] label, .dex-numrange-label, .dex-type-label {
        color: var(--text-muted) !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stSelectbox"] > div > div, [data-testid="stNumberInput"] > div > div {
        background: #f1f3f5 !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        color: var(--text-main) !important;
    }
    
    .dex-range-sep { color: #ccc; font-weight: 900; line-height: 45px; }

    /* ── Type Grid ─────────────────────────────────── */
    .type-icon-box {
        background: #fff;
        border: 1px solid #eee;
        border-radius: 15px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        min-height: 85px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    }
    .type-icon-box:hover {
        transform: translateY(-5px);
        border-color: var(--poke-blue);
        box-shadow: 0 8px 20px rgba(42, 117, 187, 0.1);
    }
    .type-icon-box.type-sel {
        background: #fff;
        border: 2px solid var(--poke-blue);
        box-shadow: 0 0 20px rgba(42, 117, 187, 0.15);
    }
    .type-svg-wrap { width: 32px; height: 32px; margin-bottom: 8px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1)); }
    .type-icon-box span { color: var(--text-main); font-size: 0.8rem; font-weight: 600; font-family: 'Inter', sans-serif; }
    
    /* Hide Streamlit Button Overlay */
    div[data-testid="stColumn"]:has(.type-icon-box) [data-testid="stBaseButton-secondary"] {
        position: absolute; inset: 0; opacity: 0 !important; z-index: 10;
    }

    /* ── Action Buttons ────────────────────────────── */
    .dex-btn-search [data-testid="stBaseButton-secondary"],
    .dex-btn-reset [data-testid="stBaseButton-secondary"] {
        border-radius: 12px !important;
        padding: 20px !important;
        font-weight: 800 !important;
        font-family: 'Outfit', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
    }
    .dex-btn-search [data-testid="stBaseButton-secondary"] {
        background: var(--poke-blue) !important;
        color: #fff !important;
        box-shadow: 0 10px 20px rgba(42, 117, 187, 0.2) !important;
    }
    .dex-btn-reset [data-testid="stBaseButton-secondary"] {
        background: #f1f3f5 !important;
        color: var(--text-main) !important;
        border: 1px solid #ddd !important;
    }
    .dex-btn-search [data-testid="stBaseButton-secondary"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(42, 117, 187, 0.3) !important;
        filter: brightness(1.1);
    }

    /* ── Pokemon Grid & Cards ──────────────────────── */
    .pokemon-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 30px;
        padding: 60px 40px;
    }

    .pokemon-card {
        background: white;
        border: 1px solid #eee;
        border-radius: 24px;
        padding: 25px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-decoration: none !important;
        display: flex;
        flex-direction: column;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
    }
    .pokemon-card:hover {
        transform: translateY(-12px);
        border-color: #ddd;
        box-shadow: 0 30px 60px rgba(0,0,0,0.1);
    }

    .pokemon-image-wrapper {
        position: relative;
        z-index: 1;
        padding: 10px;
        height: 180px;
        display: flex; align-items: center; justify-content: center;
        background: #f9f9f9;
        border-radius: 18px;
        margin-bottom: 5px;
    }
    .pokemon-image {
        width: 150px; height: 150px;
        object-fit: contain;
        filter: drop-shadow(0 10px 20px rgba(0,0,0,0.1));
        transition: transform 0.4s ease;
    }
    .pokemon-card:hover .pokemon-image { transform: scale(1.1); }

    .pokemon-info { position: relative; z-index: 1; padding-top: 15px; text-align: left; }
    .pokemon-id-badge {
        font-family: 'Outfit', sans-serif;
        color: #999;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .pokemon-name {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.2rem;
        color: var(--text-main);
        margin-bottom: 12px;
    }

    .type-container { display: flex; gap: 6px; }
    .type-badge {
        flex: 1; padding: 5px 0; border-radius: 6px;
        font-size: 0.72rem; font-weight: 700; color: #fff; text-align: center;
        text-transform: uppercase;
    }

    /* Modern Type Colors */
    .type-normal   { background: #A8A77A; }
    .type-fire     { background: #EE8130; }
    .type-water    { background: #6390F0; }
    .type-electric { background: #F7D02C; color: #000; }
    .type-grass    { background: #7AC74C; }
    .type-ice      { background: #96D9D9; color: #000; }
    .type-fighting { background: #C22E28; }
    .type-poison   { background: #A33EA1; }
    .type-ground   { background: #E2BF65; color: #000; }
    .type-flying   { background: #A98FF3; }
    .type-psychic  { background: #F95587; }
    .type-bug      { background: #A6B91A; }
    .type-rock     { background: #B6A136; }
    .type-ghost    { background: #735797; }
    .type-dragon   { background: #6F35FC; }
    .type-steel    { background: #B7B7CE; color: #000; }
    .type-fairy    { background: #D685AD; }
    .type-dark     { background: #705746; }

    /* ── Load More ──────────────────────────────────── */
    .load-more-container { display: flex; justify-content: center; padding: 40px 0 80px; }
    .load-more-container button {
        background: white !important;
        color: var(--text-main) !important;
        border: 1px solid #ddd !important;
        border-radius: 12px !important;
        padding: 12px 40px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }
    .load-more-container button:hover {
        border-color: var(--poke-blue) !important;
        color: var(--poke-blue) !important;
        transform: translateY(-2px);
    }
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
