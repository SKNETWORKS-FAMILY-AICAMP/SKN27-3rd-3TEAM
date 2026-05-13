import streamlit as st


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600;700&display=swap');
        .stApp, .stMarkdown, .stText, .stButton button, .stSelectbox label, .stTextInput label {
            font-size: 18px;
        }
        .stButton button {
            font-weight: 800;
            min-height: 44px;
        }
        .main-title {
            text-align: center;
            font-size: 56px;
            font-weight: 900;
            letter-spacing: -2px;
            margin-top: 4px;
        }
        .sub-title {
            text-align: center;
            font-size: 24px;
            margin-bottom: 24px;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) {
            background: #2b2b2b !important;
            border: 1px solid #ffffff !important;
            border-radius: 24px !important;
            padding: 24px 28px 28px !important;
            margin: 0 0 28px !important;
            box-shadow: 0 18px 36px rgba(15, 23, 42, 0.16) !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) > [data-testid="stVerticalBlock"] {
            background: transparent !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stHorizontalBlock"] {
            align-items: center !important;
        }
        .team-filter-panel-marker {
            position: absolute;
            width: 0;
            height: 0;
            opacity: 0;
            pointer-events: none;
        }
        .team-filter-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0 0 16px;
        }
        .team-filter-title-icon {
            width: 36px;
            height: 36px;
            object-fit: contain;
            filter: drop-shadow(0 2px 6px rgba(227, 53, 53, 0.5));
        }
        .team-filter-title span {
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: 1px;
            text-shadow: 0 2px 8px rgba(227, 53, 53, 0.4);
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) label,
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) label p,
        .team-filter-label {
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.1rem !important;
            font-weight: 900 !important;
            color: #ffffff !important;
            letter-spacing: 1px !important;
            text-shadow: 0 2px 6px rgba(227, 53, 53, 0.4) !important;
            margin-bottom: 12px !important;
            display: block !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] [data-baseweb="input"],
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] [data-baseweb="base-input"],
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stSelectbox"] > div > div {
            background: #1e1e1e !important;
            border: 2px solid #444 !important;
            border-radius: 12px !important;
            color: #e0e0e0 !important;
            min-height: 64px !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] input {
            color: #e0e0e0 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 1.25rem !important;
            padding: 22px 28px !important;
            background: transparent !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTextInput"] input::placeholder {
            color: #666 !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stSelectbox"] span {
            color: #e0e0e0 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 1rem !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stSlider"] div[role="slider"] {
            background-color: transparent !important;
            background-image: url("https://pokemonkorea.co.kr/img/_con.ico") !important;
            background-size: 100% 100% !important;
            border: none !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.35) !important;
            width: 34px !important;
            height: 34px !important;
        }
        [data-testid="stVerticalBlock"]:has(> .element-container .team-filter-panel-marker) [data-testid="stTickBar"] {
            color: #f8fafc !important;
            font-weight: 800 !important;
        }
        .team-region-button {
            min-height: 38px;
            padding: 8px 8px;
            margin-bottom: 8px;
            border: 1.5px solid #444;
            border-radius: 9px;
            background: #1e1e1e;
            color: #d1d5db;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            font-weight: 850;
            transition: all 0.2s ease;
        }
        .team-region-button.region-active {
            background: #ef3434;
            border-color: #ef3434;
            color: #ffffff;
            box-shadow: 0 0 14px rgba(239, 52, 52, 0.35);
        }
        div[data-testid="stColumn"]:has(.team-region-button) [data-testid="stVerticalBlock"] {
            position: relative;
        }
        div[data-testid="stColumn"]:has(.team-region-button) .element-container:has(button) {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 38px;
            z-index: 10;
            margin: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-region-button) button {
            width: 100% !important;
            height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            border: none !important;
            padding: 0 !important;
        }
        .type-svg-wrap {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            flex-shrink: 0;
        }
        .team-type-button {
            min-height: 48px;
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 12px;
            color: #ffffff;
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-size: 0.85rem;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
            transition: all 0.2s ease;
            position: relative;
            width: 100%;
            cursor: pointer;
        }
        .team-type-button span {
            color: #ffffff;
            font-size: 0.85rem;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
            text-shadow: 0 1px 3px rgba(0,0,0,0.5);
            line-height: 1;
        }
        .team-type-button.type-active {
            outline: 3px solid #ffffff;
            outline-offset: 2px;
            box-shadow: 0 0 18px rgba(255, 255, 255, 0.45);
            transform: translateY(-2px);
        }
        .type-bg-normal { background: #A8A77A; }
        .type-bg-fire { background: #EE8130; }
        .type-bg-water { background: #6390F0; }
        .type-bg-electric { background: #F7D02C; color: #111827; text-shadow: none; }
        .type-bg-grass { background: #7AC74C; }
        .type-bg-ice { background: #96D9D9; color: #111827; text-shadow: none; }
        .type-bg-fighting { background: #C22E28; }
        .type-bg-poison { background: #A33EA1; }
        .type-bg-ground { background: #E2BF65; color: #111827; text-shadow: none; }
        .type-bg-flying { background: #A98FF3; }
        .type-bg-psychic { background: #F95587; }
        .type-bg-bug { background: #A6B91A; }
        .type-bg-rock { background: #B6A136; }
        .type-bg-ghost { background: #735797; }
        .type-bg-dragon { background: #6F35FC; }
        .type-bg-dark { background: #705746; }
        .type-bg-steel { background: #B7B7CE; color: #111827; text-shadow: none; }
        .type-bg-fairy { background: #D685AD; }
        div[data-testid="stColumn"]:has(.team-type-button) [data-testid="stVerticalBlock"] {
            position: relative;
        }
        div[data-testid="stColumn"]:has(.team-type-button) .element-container:has(button) {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 48px;
            z-index: 10;
            margin: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-type-button) button {
            width: 100% !important;
            height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            border: none !important;
            padding: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button {
            height: 50px !important;
            border: none !important;
            border-radius: 0 !important;
            transform: skew(-20deg) !important;
            transition: all 0.2s ease !important;
            margin-top: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button div,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button div,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button span,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button span {
            transform: skew(0deg) !important;
            display: inline-block !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            letter-spacing: 1px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button {
            background: #E33535 !important;
            color: #ffffff !important;
            box-shadow: -5px 5px 0 rgba(227, 53, 53, 0.3) !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-search-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button span,
        div[data-testid="stColumn"]:has(.team-filter-search-button) button div {
            color: white !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button {
            background: #ffffff !important;
            box-shadow: -5px 5px 0 rgba(0, 0, 0, 0.15) !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button p,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button span,
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button div {
            color: #1a1a1a !important;
        }
        div[data-testid="stColumn"]:has(.team-filter-reset-button) button:hover {
            background: #f0f0f0 !important;
        }
        /* ── Team Side Panel ────────────────────────── */
        .ts-panel {
            background: rgba(20, 20, 30, 0.97);
            border: 1px solid rgba(255,255,255,0.08);
            border-top: 4px solid #FFCB05;
            border-radius: 18px;
            padding: 16px 12px 12px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        }
        .ts-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.07);
        }
        .ts-icon {
            width: 24px; height: 24px;
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(227,53,53,0.5));
        }
        .ts-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 900;
            color: #FFCB05;
            letter-spacing: 0.5px;
        }
        .ts-badge {
            margin-left: auto;
            background: rgba(255,203,5,0.12);
            border: 1px solid rgba(255,203,5,0.3);
            color: #FFCB05;
            font-size: 0.72rem;
            font-weight: 800;
            padding: 2px 9px;
            border-radius: 20px;
            font-family: 'Outfit', sans-serif;
        }
        /* 2열 3행 그리드 */
        .ts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
            margin-bottom: 10px;
        }
        .ts-slot {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            gap: 4px;
            padding: 8px 4px 7px;
            border-radius: 12px;
            background: rgba(255,255,255,0.025);
            border: 1px dashed rgba(255,255,255,0.09);
            min-height: 92px;
            transition: all 0.2s;
        }
        .ts-slot.filled {
            background: rgba(255,203,5,0.05);
            border: 1px solid rgba(255,203,5,0.22);
        }
        .ts-slot-locked {
            background: rgba(255,255,255,0.01) !important;
            border: 1px dashed rgba(255,255,255,0.05) !important;
            opacity: 0.45;
        }
        .ts-num {
            font-size: 0.52rem;
            font-weight: 800;
            color: #555;
            align-self: flex-start;
            padding-left: 5px;
            line-height: 1;
        }
        .ts-img {
            width: 52px; height: 48px;
            object-fit: contain;
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5));
        }
        .ts-empty-circle {
            width: 40px; height: 40px;
            border: 2px dashed rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: rgba(255,255,255,0.12);
            font-size: 1rem;
        }
        .ts-lock-circle {
            width: 40px; height: 40px;
            border: 2px dashed rgba(255,255,255,0.06);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: rgba(255,255,255,0.12);
            font-size: 1.1rem;
            font-weight: 900;
        }
        .ts-name {
            font-size: 0.62rem;
            font-weight: 700;
            color: #e0e0e0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            width: 100%;
            text-align: center;
            padding: 0 3px;
            font-family: 'Inter', sans-serif;
        }
        .ts-empty-text {
            font-size: 0.58rem;
            font-weight: 600;
            color: rgba(255,255,255,0.18);
            text-align: center;
            font-family: 'Inter', sans-serif;
        }
        .ts-hint {
            text-align: center;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 6px 0 2px;
            font-family: 'Outfit', sans-serif;
            letter-spacing: 0.2px;
        }

        /* ── Team Action Buttons ─────────────────────── */
        .element-container:has(.tb-act-reset) + .element-container button,
        .element-container:has(.tb-act-analyze) + .element-container button,
        .element-container:has(.tb-act-recommend) + .element-container button {
            height: 44px !important;
            border-radius: 10px !important;
            border: none !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 900 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.5px !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }
        .element-container:has(.tb-act-reset) + .element-container button {
            background: #2a2a2a !important;
            color: #c0c0c0 !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
        }
        .element-container:has(.tb-act-analyze) + .element-container button {
            background: #E33535 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(227,53,53,0.3) !important;
        }
        .element-container:has(.tb-act-analyze) + .element-container button:disabled {
            opacity: 0.35 !important;
            cursor: not-allowed !important;
            box-shadow: none !important;
        }

        .selected-count {
            text-align: center;
            color: #2563eb;
            font-weight: 800;
            font-size: 18px;
            margin-top: 18px;
        }
        .empty-slot {
            height: 138px;
            border: 2px dashed #a9b5c8;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #8b95a7;
            font-size: 18px;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.72);
        }
        .selected-slot {
            height: 138px;
            border: 1px solid #c9d3e2;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.84);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 18px rgba(30, 41, 59, 0.08);
            overflow: hidden;
        }
        .selected-slot-image {
            width: 96px;
            height: 92px;
            object-fit: contain;
        }
        .selected-slot-name {
            max-width: 100%;
            padding: 0 8px;
            font-size: 17px;
            font-weight: 800;
            color: #1f2937;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .pokemon-card {
            min-height: 220px;
            padding: 12px;
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            background: #ffffff;
            box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);
            display: flex;
            flex-direction: column;
            text-align: left;
            transition: all 0.25s ease;
            margin-bottom: 6px;
            overflow: hidden;
            position: relative;
        }
        .selected-card {
            border: 3px solid #2f80ed;
            box-shadow: 0 0 0 4px rgba(47, 128, 237, 0.16), 0 24px 50px rgba(37, 99, 235, 0.16);
        }
        .pokemon-image-wrapper {
            position: relative;
            height: 110px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f9fafb;
            border-radius: 14px;
            margin-bottom: 8px;
        }
        .pokemon-card-image {
            width: 90px;
            height: 90px;
            object-fit: contain;
            filter: drop-shadow(0 6px 12px rgba(15, 23, 42, 0.1));
            transition: transform 0.28s ease;
        }
        .pokemon-info {
            width: 100%;
            padding: 2px 2px 0;
        }
        .pokemon-id-badge {
            color: #9ca3af;
            font-size: 13px;
            font-weight: 900;
            margin-bottom: 3px;
        }
        .pokemon-card-title {
            width: 100%;
            font-size: 16px;
            font-weight: 900;
            color: #111827;
            margin-bottom: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .pokemon-type-row {
            min-height: 30px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 6px;
            flex-wrap: wrap;
        }
        .type-badge {
            flex: 1;
            min-width: 45px;
            padding: 4px 6px;
            border-radius: 6px;
            background: #e0f2fe;
            color: #075985;
            font-size: 12px;
            font-weight: 900;
            text-align: center;
            border: 1px solid #bae6fd;
        }
        .type-placeholder {
            color: #8b95a7;
            font-size: 14px;
            font-weight: 800;
        }
        /* ── Pokemon card — 투명 버튼 오버레이 (카드 클릭 = 선택/해제) ── */
        .pokemon-card-marker {
            position: absolute;
            width: 0;
            height: 0;
            opacity: 0;
            pointer-events: none;
        }
        div[data-testid="stColumn"]:has(.pokemon-card-marker) [data-testid="stVerticalBlock"] {
            position: relative;
        }
        /* element-container 전체를 카드 위에 덮도록 절대위치 */
        div[data-testid="stColumn"]:has(.pokemon-card-marker) .element-container:has(button) {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            z-index: 20 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        /* stButton div도 100% 채우기 */
        div[data-testid="stColumn"]:has(.pokemon-card-marker) [data-testid="stBaseButton-secondary"],
        div[data-testid="stColumn"]:has(.pokemon-card-marker) .element-container:has(button) > div {
            width: 100% !important;
            height: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        /* 버튼 자체를 절대위치로 카드 전체 커버 */
        div[data-testid="stColumn"]:has(.pokemon-card-marker) button {
            position: absolute !important;
            inset: 0 !important;
            width: 100% !important;
            height: 100% !important;
            min-height: unset !important;
            opacity: 0 !important;
            cursor: pointer !important;
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .pokemon-card {
            position: relative;
            z-index: 1;
            pointer-events: none;
        }
        .selected-card {
            border: 3px solid #3b82f6 !important;
            background: #eff6ff !important;
        }
        .analysis-summary-card {
            margin: 16px 0 18px 0;
            padding: 22px 24px;
            border: 1px solid #c7d2fe;
            border-radius: 22px;
            background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 58%, #ecfeff 100%);
            box-shadow: 0 14px 32px rgba(30, 41, 59, 0.08);
        }
        .analysis-kicker {
            color: #2563eb;
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .analysis-title {
            margin-top: 4px;
            color: #111827;
            font-size: 28px;
            font-weight: 900;
        }
        .analysis-summary-text {
            margin-top: 8px;
            color: #334155;
            font-size: 20px;
            line-height: 1.75;
            font-weight: 650;
        }
        .rag-answer-card {
            margin: 12px 0 20px 0;
            max-height: 360px;
            overflow-y: auto;
            padding: 24px 28px;
            border: 1px solid #a7f3d0;
            border-radius: 20px;
            background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 52%, #ecfeff 100%);
            box-shadow: 0 14px 30px rgba(15, 118, 110, 0.09);
            scrollbar-width: thin;
            scrollbar-color: #34d399 #e2e8f0;
        }
        .rag-answer-card::-webkit-scrollbar {
            width: 10px;
        }
        .rag-answer-card::-webkit-scrollbar-track {
            background: #e2e8f0;
            border-radius: 999px;
        }
        .rag-answer-card::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #34d399 0%, #38bdf8 100%);
            border-radius: 999px;
        }
        .rag-answer-kicker {
            position: sticky;
            top: -24px;
            z-index: 1;
            padding: 0 0 10px 0;
            background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 52%, #ecfeff 100%);
            color: #0f766e;
            font-size: 17px;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .rag-answer-conclusion {
            margin-bottom: 18px;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid #99f6e4;
            background: rgba(240, 253, 250, 0.9);
            color: #0f172a;
            font-size: 22px;
            line-height: 1.65;
            font-weight: 900;
        }
        .rag-answer-text {
            color: #1f2937;
            font-size: 20px;
            line-height: 1.85;
            font-weight: 650;
        }
        .rag-answer-text p {
            margin: 0 0 18px 0;
        }
        .analysis-section-header {
            margin: 22px 0 12px 0;
            color: #111827;
            font-size: 22px;
            font-weight: 900;
        }
        .analysis-team-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 22px;
        }
        .analysis-team-card {
            min-height: 168px;
            padding: 12px;
            border: 1px solid #dbe7f5;
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,251,255,0.92) 100%);
            box-shadow: 0 14px 28px rgba(30, 41, 59, 0.08);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            gap: 8px;
        }
        .analysis-team-image-wrap {
            width: 100%;
            height: 88px;
            border-radius: 16px;
            background: radial-gradient(circle at 50% 35%, #ffffff 0%, #eef6ff 72%);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .analysis-team-image {
            width: 92px;
            height: 84px;
            object-fit: contain;
            filter: drop-shadow(0 8px 10px rgba(30, 41, 59, 0.13));
        }
        .analysis-team-image-empty {
            color: #94a3b8;
            font-weight: 900;
        }
        .analysis-team-name {
            width: 100%;
            color: #111827;
            font-size: 17px;
            font-weight: 900;
            text-align: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .analysis-team-types {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 5px;
        }
        .analysis-detail-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px;
            margin: 18px 0 32px 0;
        }
        .analysis-detail-card {
            min-height: 360px;
            padding: 18px;
            border-radius: 24px;
            border: 1px solid #dbe7f5;
            box-shadow: 0 18px 36px rgba(30, 41, 59, 0.08);
        }
        .danger-panel {
            background: linear-gradient(180deg, #fff7f7 0%, #ffffff 100%);
            border-color: #fecaca;
        }
        .safe-panel {
            background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
            border-color: #bbf7d0;
        }
        .coverage-panel {
            background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
            border-color: #bfdbfe;
        }
        .analysis-detail-title {
            color: #111827;
            font-size: 22px;
            font-weight: 950;
            margin-bottom: 6px;
        }
        .analysis-detail-caption {
            min-height: 40px;
            color: #64748b;
            font-size: 17px;
            line-height: 1.55;
            font-weight: 700;
            margin-bottom: 14px;
        }
        .analysis-metric-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 11px 0;
            border-top: 1px solid rgba(148, 163, 184, 0.22);
        }
        .analysis-metric-left {
            min-width: 92px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .analysis-metric-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 2px;
            color: #334155;
            font-size: 17px;
            font-weight: 750;
        }
        .analysis-metric-right span {
            color: #64748b;
            font-size: 15px;
            font-weight: 700;
        }
        .analysis-empty-row {
            padding: 16px;
            color: #64748b;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 14px;
            font-weight: 700;
        }
        .coverage-row {
            padding: 11px 0;
            border-top: 1px solid rgba(148, 163, 184, 0.22);
        }
        .coverage-row-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            color: #334155;
            font-size: 17px;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .coverage-bar {
            height: 8px;
            border-radius: 999px;
            background: #e2e8f0;
            overflow: hidden;
        }
        .coverage-bar-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
        }
        .recommend-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            margin: 18px 0 32px 0;
        }
        .recommend-card {
            position: relative;
            min-height: 420px;
            padding: 22px 18px 18px 18px;
            border-radius: 28px;
            border: 1px solid #dbe7f5;
            background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,251,255,0.96) 100%);
            box-shadow: 0 20px 42px rgba(30, 41, 59, 0.11);
            overflow: hidden;
        }
        .recommend-card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 8px;
            background: linear-gradient(90deg, #60a5fa 0%, #34d399 100%);
        }
        .recommend-card.rank-1::before {
            background: linear-gradient(90deg, #f59e0b 0%, #facc15 100%);
        }
        .recommend-rank {
            color: #111827;
            font-size: 30px;
            font-weight: 950;
            letter-spacing: -0.02em;
            margin-bottom: 10px;
        }
        .recommend-image-wrap {
            height: 150px;
            border-radius: 22px;
            background: radial-gradient(circle at 50% 35%, #ffffff 0%, #eef6ff 76%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
        }
        .recommend-image {
            width: 150px;
            height: 140px;
            object-fit: contain;
            filter: drop-shadow(0 12px 14px rgba(30, 41, 59, 0.16));
        }
        .recommend-image-empty {
            color: #94a3b8;
            font-size: 28px;
            font-weight: 900;
        }
        .recommend-name {
            color: #111827;
            font-size: 21px;
            font-weight: 950;
            margin-bottom: 8px;
        }
        .recommend-types {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            min-height: 26px;
            margin-bottom: 12px;
        }
        .recommend-score {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 14px;
            background: #f1f5f9;
            color: #475569;
            font-size: 17px;
            font-weight: 850;
            margin-bottom: 12px;
        }
        .recommend-score strong {
            color: #2563eb;
            font-size: 22px;
            font-weight: 950;
        }
        .recommend-reasons {
            margin: 0;
            padding-left: 18px;
            color: #334155;
            max-height: 220px;
            overflow-y: auto;
            font-size: 17px;
            line-height: 1.75;
            font-weight: 700;
        }
        .recommend-reasons li {
            margin-bottom: 8px;
        }
        @media (max-width: 1100px) {
            .analysis-team-grid,
            .analysis-detail-grid,
            .recommend-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 720px) {
            .analysis-team-grid,
            .analysis-detail-grid,
            .recommend-grid {
                grid-template-columns: 1fr;
            }
        }
        .insight-card {
            min-height: 110px;
            margin: 10px 0;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid #d8dee9;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 10px 24px rgba(30, 41, 59, 0.07);
        }
        .risk-high {
            border-color: #fecaca;
            background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%);
        }
        .risk-medium {
            border-color: #fed7aa;
            background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
        }
        .strength-card {
            border-color: #bbf7d0;
            background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
        }
        .direction-card {
            border-color: #bae6fd;
            background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 100%);
        }
        .insight-card-title {
            color: #111827;
            font-size: 19px;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .insight-card-text {
            color: #475569;
            font-size: 18px;
            line-height: 1.65;
            font-weight: 650;
        }
        .analysis-type-balance {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }
        /* ── Streamlit Widget Overrides (Perfect Sync with Pokedex) ── */
        
        /* 1. 필터 라벨 공통 스타일 (빨간 그림자 효과 포함) */
        .stSelectbox label p, .stSlider label p, .stTextInput label p,
        [data-testid="stWidgetLabel"] p, .team-filter-label {
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.1rem !important;
            font-weight: 900 !important;
            color: #ffffff !important;
            letter-spacing: 1px !important;
            text-shadow: 0 2px 6px rgba(227, 53, 53, 0.4) !important;
            margin-bottom: 12px !important;
        }

        /* 2. 검색창 (Text Input) - 도감과 100% 일치 */
        [data-testid="stTextInput"] [data-baseweb="input"] {
            background: #1e1e1e !important;
            border: 2px solid #444 !important;
            border-radius: 12px !important;
            min-height: 64px !important;
        }
        [data-testid="stTextInput"] input {
            color: #e0e0e0 !important;
            font-size: 1.25rem !important;
            padding: 22px 28px !important;
        }

        /* 3. 특성 선택창 (Selectbox) - 수직 중앙 정렬 정밀 수정 */
        [data-testid="stSelectbox"] > div > div {
            background: #1e1e1e !important;
            border: 2px solid #444 !important;
            border-radius: 12px !important;
            min-height: 42px !important; /* 비율에 맞춘 42px */
            height: 42px !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            padding: 0 12px !important; /* 내부 패딩 초기화 */
            min-height: 42px !important;
            height: 42px !important;
            display: flex !important;
            align-items: center !important; /* 텍스트 수직 중앙 정렬 */
        }
        [data-testid="stSelectbox"] span {
            color: #e0e0e0 !important;
            font-size: 1.05rem !important;
            line-height: 42px !important; /* 줄높이로 한 번 더 중앙 고정 */
        }
        /* 화살표 아이콘 위치 고정 */
        [data-testid="stSelectbox"] svg {
            fill: #888 !important;
        }
        [data-testid="stSelectbox"] [data-testid="stSelectboxArrow"] {
            top: 50% !important;
            transform: translateY(-50%) !important;
        }
        
        /* 4. 지방 버튼 - 도감과 100% 일치 */
        .team-region-button {
            min-height: 36px !important;
            font-size: 0.78rem !important;
            padding: 7px 4px !important;
            background: #1e1e1e !important;
            border: 1.5px solid #444 !important;
            border-radius: 8px !important;
            color: #aaa !important;
            font-weight: 700 !important;
        }
        .region-active {
            background: #E33535 !important;
            border-color: #E33535 !important;
            color: #ffffff !important;
            box-shadow: 0 0 10px rgba(227, 53, 53, 0.4) !important;
        }

        /* 5. 타입 버튼 - 도감과 100% 일치 */
        .team-type-button {
            min-height: 48px !important;
            padding: 8px 12px !important;
            border-radius: 12px !important;
        }
        .team-type-button span {
            font-size: 0.85rem !important;
            font-weight: 700 !important;
        }

        /* 6. 슬라이더 - 도감과 100% 일치 */
        [data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
            color: #e0e0e0 !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
        }
        [data-testid="stTickBar"] div {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* 7. 하단 액션 버튼 (검색/초기화) - 도감 사선 스타일 적용 */
        .team-filter-search-button + div button,
        .team-filter-reset-button + div button {
            transform: skew(-20deg) !important;
            height: 50px !important;
            border-radius: 0 !important;
            border: none !important;
        }
        .team-filter-search-button + div button p,
        .team-filter-reset-button + div button p {
            transform: skew(20deg) !important;
            font-size: 1.1rem !important;
            font-weight: 900 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
