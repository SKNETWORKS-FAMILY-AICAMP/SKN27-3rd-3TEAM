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


    /* ── Search Card Container ───────────────────────── */
    /* 신버전 Streamlit: border=True는 stVerticalBlock에 직접 적용 */
    [data-testid="stVerticalBlock"]:has(> .element-container .dex-search-card) {
        background: #2b2b2b !important;
        background-color: #2b2b2b !important;
        border: 1px solid #ffffff !important;
        border-radius: 24px !important;
        padding: 10px 20px 20px !important;
        margin-bottom: 30px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }
    /* 구버전 Streamlit 호환 */
    [data-testid="stVerticalBlockBorderWrapper"],
    .stVerticalBlockBorderWrapper {
        background: #2b2b2b !important;
        background-color: #2b2b2b !important;
        border: 1px solid #333333 !important;
        border-radius: 24px !important;
        padding: 20px 30px 30px !important;
        margin-bottom: 30px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }

    /* Ensure internal blocks are transparent and aligned */
    [data-testid="stVerticalBlock"]:has(> .element-container .dex-search-card) > [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
    .stVerticalBlockBorderWrapper [data-testid="stVerticalBlock"] {
        background: transparent !important;
        background-color: transparent !important;
        gap: 0.5rem !important;
    }

    /* Search row & Slider vertical alignment */
    [data-testid="stVerticalBlock"]:has(> .element-container .dex-search-card) [data-testid="stHorizontalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }

    .dex-search-card {
        position: absolute;
        width: 0;
        height: 0;
        opacity: 0;
        pointer-events: none;
    }

    /* ── Page Title ────────────────────────────────── */
    .dex-page-title {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }
    .dex-title-icon {
        width: 36px;
        height: 36px;
        object-fit: contain;
        filter: drop-shadow(0 2px 6px rgba(227, 53, 53, 0.5));
    }
    .dex-page-title span {
        font-family: 'Outfit', sans-serif;
        font-size: 1.6rem;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 1px;
        text-shadow: 0 2px 8px rgba(227, 53, 53, 0.4);
    }

    /* ── Inputs & Selects ──────────────────────────── */
    /* Search Bar */
    [data-testid="stTextInput"] label { display: none; }
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextInput"] [data-baseweb="base-input"] {
        background: #1e1e1e !important;
        border: 2px solid #444 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        min-height: 64px !important;
        display: flex !important;
        align-items: center !important;
    }
    [data-testid="stTextInput"]:focus-within [data-baseweb="input"],
    [data-testid="stTextInput"]:focus-within [data-baseweb="base-input"] {
        border-color: #E33535 !important;
        box-shadow: 0 0 12px rgba(227, 53, 53, 0.3) !important;
    }
    [data-testid="stTextInput"] input {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.25rem !important;
        padding: 22px 28px !important;
        background: transparent !important;
    }
    [data-testid="stTextInput"] input::placeholder {
        color: #666 !important;
    }

    /* ── Filter Labels (Styled like page title) ─────── */
    .stSelectbox label, .stSlider label, .stTextInput label,
    .stSelectbox label p, .stSlider label p, .stTextInput label p,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] div,
    [data-testid="stWidgetLabel"],
    label p,
    .dex-numrange-label,
    .dex-type-label,
    .dex-region-label {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        letter-spacing: 1px !important;
        text-shadow: 0 2px 6px rgba(227, 53, 53, 0.4) !important;
        text-transform: none !important;
        margin-bottom: 12px !important;
        display: block !important;
    }

    /* Selectbox 드롭다운 박스 */
    [data-testid="stSelectbox"] > div > div {
        background: #1e1e1e !important;
        border: 2px solid #444 !important;
        border-radius: 12px !important;
        color: #e0e0e0 !important;
    }
    [data-testid="stSelectbox"] > div > div:hover {
        border-color: #E33535 !important;
        box-shadow: 0 0 10px rgba(227, 53, 53, 0.2) !important;
    }
    [data-testid="stSelectbox"] span {
        color: #e0e0e0 !important;
    }
    [data-testid="stSelectbox"] svg {
        fill: #888 !important;
    }

    /* Number Input */
    [data-testid="stNumberInput"] [data-baseweb="input"],
    [data-testid="stNumberInput"] [data-baseweb="base-input"] {
        background: #1e1e1e !important;
        border: 2px solid #444 !important;
        border-radius: 12px !important;
    }
    [data-testid="stNumberInput"] input {
        color: #e0e0e0 !important;
        background: transparent !important;
    }
    [data-testid="stNumberInput"] button {
        color: #888 !important;
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stNumberInput"] button:hover {
        color: #ffffff !important;
        background: #E33535 !important;
    }

    .dex-range-sep { color: #888; font-weight: 900; line-height: 45px; }

    .region-btn-box {
        background: #1e1e1e;
        border: 1.5px solid #444;
        border-radius: 8px;
        padding: 7px 4px;
        text-align: center;
        color: #aaa;
        font-size: 0.78rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        min-height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        margin-bottom: 5px;
        transition: all 0.2s ease;
    }
    .region-btn-box.region-sel {
        background: #E33535;
        border-color: #E33535;
        color: #ffffff;
        box-shadow: 0 0 10px rgba(227, 53, 53, 0.4);
    }
    /* 오버레이 버튼 (클릭 감지용) */
    div[data-testid="stColumn"]:has(.region-btn-box) [data-testid="stVerticalBlock"] {
        position: relative;
    }
    div[data-testid="stColumn"]:has(.region-btn-box) .element-container:has(button) {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 36px;
        z-index: 10;
        margin: 0 !important;
    }
    div[data-testid="stColumn"]:has(.region-btn-box) button {
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        border: none !important;
        cursor: pointer !important;
        padding: 0 !important;
    }

    /* ── Slider ────────────────────────────────────── */
    [data-testid="stSlider"],
    [data-testid="stSlider"] > div,
    [data-testid="stSlider"] [data-baseweb="slider"] {
        overflow: visible !important;
        padding: 10px 0px !important;
    }
    /* 트랙 배경 */
    [data-testid="stSlider"] [role="slider"] ~ div {
        background: #444 !important;
        height: 6px !important;
    }
    /* 선택된 범위 트랙 */
    [data-testid="stSlider"] div[data-testid="stTickBar"] ~ div > div > div {
        background: #E33535 !important;
        height: 6px !important;
    }
    /* 썸(핸들) - 모든 핸들에 몬스터볼 아이콘 적용 */
    [data-testid="stSlider"] div[role="slider"] {
        background-color: transparent !important;
        background-image: url("https://pokemonkorea.co.kr/img/_con.ico") !important;
        background-size: 100% 100% !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3) !important;
        width: 32px !important;
        height: 32px !important;
        cursor: grab !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    /* 현재값 툴팁 */
    [data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
        color: #e0e0e0 !important;
        font-weight: 700 !important;
    }
    /* min/max 눈금 텍스트 */
    [data-testid="stTickBar"] {
        color: #666 !important;
    }

    /* ── Type Grid ─────────────────────────────────── */
    .type-icon-box {
        background: #555;
        border: none;
        border-radius: 12px;
        padding: 8px 12px;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        min-height: 48px;
        margin-bottom: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02);
        width: 100%;
        position: relative;
    }
    .type-icon-box:hover {
        transform: translateY(-3px);
        filter: brightness(1.2);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }
    .type-icon-box.type-sel {
        outline: 3px solid #ffffff;
        outline-offset: 2px;
        box-shadow: 0 0 16px rgba(255, 255, 255, 0.4);
    }
    .type-svg-wrap {
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
    }
    .type-icon-box span {
        color: #ffffff;
        font-size: 0.85rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 1px 3px rgba(0,0,0,0.5);
        line-height: 1;
    }

    /* 타입별 배경색 */
    .type-bg-normal   { background: #A8A77A; }
    .type-bg-fire     { background: #EE8130; }
    .type-bg-water    { background: #6390F0; }
    .type-bg-electric { background: #F7D02C; }
    .type-bg-grass    { background: #7AC74C; }
    .type-bg-ice      { background: #96D9D9; }
    .type-bg-fighting { background: #C22E28; }
    .type-bg-poison   { background: #A33EA1; }
    .type-bg-ground   { background: #E2BF65; }
    .type-bg-flying   { background: #A98FF3; }
    .type-bg-psychic  { background: #F95587; }
    .type-bg-bug      { background: #A6B91A; }
    .type-bg-rock     { background: #B6A136; }
    .type-bg-ghost    { background: #735797; }
    .type-bg-dragon   { background: #6F35FC; }
    .type-bg-steel    { background: #B7B7CE; }
    .type-bg-fairy    { background: #D685AD; }
    .type-bg-dark     { background: #705746; }

    /* Hide Streamlit Button Overlay */
    div[data-testid="stColumn"]:has(.type-icon-box) [data-testid="stVerticalBlock"] {
        position: relative;
    }
    div[data-testid="stColumn"]:has(.type-icon-box) .element-container:has(button) {
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 48px;
        z-index: 10;
        margin: 0 !important;
    }
    div[data-testid="stColumn"]:has(.type-icon-box) button {
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        border: none !important;
        cursor: pointer !important;
        padding: 0 !important;
    }

    /* ── Action Buttons (Slanted Design) ──────────────── */
    div[data-testid="stColumn"]:has(.dex-btn-search) button,
    div[data-testid="stColumn"]:has(.dex-btn-reset) button {
        border: none !important;
        border-radius: 0 !important;
        transform: skew(-20deg) !important;
        height: 50px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        margin-top: 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Button Text (Un-skew) */
    div[data-testid="stColumn"]:has(.dex-btn-search) button p,
    div[data-testid="stColumn"]:has(.dex-btn-reset) button p,
    div[data-testid="stColumn"]:has(.dex-btn-search) button div,
    div[data-testid="stColumn"]:has(.dex-btn-reset) button div,
    div[data-testid="stColumn"]:has(.dex-btn-search) button span,
    div[data-testid="stColumn"]:has(.dex-btn-reset) button span {
        transform: skew(0deg) rotate(0deg) !important;
        display: inline-block !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 900 !important;
        font-size: 1.1rem !important;
        letter-spacing: 1px !important;
        color: white !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stColumn"]:has(.dex-btn-reset) button p,
    div[data-testid="stColumn"]:has(.dex-btn-reset) button div,
    div[data-testid="stColumn"]:has(.dex-btn-reset) button span {
        color: #1a1a1a !important;
    }

    div[data-testid="stColumn"]:has(.dex-btn-search) button {
        background-color: #E33535 !important;
        box-shadow: -5px 5px 0px rgba(227, 53, 53, 0.3) !important;
    }
    div[data-testid="stColumn"]:has(.dex-btn-reset) button {
        background-color: #ffffff !important;
        box-shadow: -5px 5px 0px rgba(0, 0, 0, 0.15) !important;
    }

    div[data-testid="stColumn"]:has(.dex-btn-search) button:hover {
        background-color: #ff4d4d !important;
        transform: skew(-20deg) translateY(-2px) !important;
        box-shadow: -8px 8px 0px rgba(227, 53, 53, 0.4) !important;
    }
    div[data-testid="stColumn"]:has(.dex-btn-reset) button:hover {
        background-color: #f0f0f0 !important;
        transform: skew(-20deg) translateY(-2px) !important;
        box-shadow: -8px 8px 0px rgba(0, 0, 0, 0.3) !important;
    }

    div[data-testid="stColumn"]:has(.dex-btn-search) + div[data-testid="stColumn"]:has(.dex-btn-reset) {
        margin-left: 15px !important;
    }

    div[data-testid="stColumn"]:has(.dex-btn-search) div,
    div[data-testid="stColumn"]:has(.dex-btn-reset) div {
        background: transparent !important;
        border: none !important;
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


def render_pokemon_card(id, name, image_url, types_ko_en, display_id=None):
    d_id = display_id if display_id is not None else id
    type_badges = "".join(
        [f'<span class="type-badge type-{en.lower()}">{ko}</span>' for ko, en in types_ko_en]
    )
    return f'''<a href="/pokemon_detail?id={id}" target="_self" class="pokemon-card">
<div class="pokemon-image-wrapper">
<img src="{image_url}" class="pokemon-image" alt="{name}" loading="lazy">
</div>
<div class="pokemon-info">
<div class="pokemon-id-badge">No.{d_id:04d}</div>
<div class="pokemon-name">{name}</div>
<div class="type-container">{type_badges}</div>
</div>
</a>'''
