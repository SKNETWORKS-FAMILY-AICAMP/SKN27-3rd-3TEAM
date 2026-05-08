import streamlit as st

def get_pokedex_styles():
    return """
    <style>
    /* Pokedex Container */
    .pokedex-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0;
    }

    /* Page Header */
    .pokedex-header {
        background-color: #313131;
        padding: 20px 40px;
        color: white;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .pokedex-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.5rem;
        color: white;
        margin: 0;
    }

    /* Dark Search & Filter Section */
    .filter-section {
        background-color: #424242;
        padding: 30px 40px;
        color: white;
        margin-bottom: 40px;
    }

    /* Override Streamlit Input Styles for Dark Theme */
    .filter-section div[data-testid="stTextInput"] input {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #000 !important;
        border-radius: 0 !important;
        padding: 15px !important;
    }
    
    .filter-section div[data-testid="stSelectbox"] > div > div {
        background-color: #313131 !important;
        color: white !important;
        border: 1px solid #555 !important;
        border-radius: 0 !important;
    }
    
    .filter-section label {
        color: #ddd !important;
        font-size: 0.9rem !important;
    }

    /* Pokemon Grid */
    .pokemon-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 20px;
        padding: 0 40px;
    }

    /* Clean Pokemon Card */
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

    /* Image Container */
    .pokemon-image-wrapper {
        padding: 10px;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 180px;
        background: transparent;
    }

    .pokemon-image {
        width: 140px;
        height: 140px;
        object-fit: contain;
    }

    /* Card Info Section */
    .pokemon-info {
        padding-top: 15px;
        text-align: left;
    }

    .pokemon-id-badge {
        font-family: 'Inter', sans-serif;
        color: #999;
        font-size: 0.8rem;
        margin-bottom: 4px;
    }

    .pokemon-name {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: #333;
        margin-bottom: 15px;
    }

    /* Type Badges - Pill shaped */
    .type-container {
        display: flex;
        justify-content: center;
        gap: 5px;
    }

    .type-badge {
        flex: 1;
        padding: 6px 0;
        border-radius: 4px;
        font-size: 0.75rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: white;
        text-align: center;
    }

    /* Flat Type Colors based on reference */
    .type-normal { background: #A8A77A; }
    .type-fire { background: #F08030; }
    .type-water { background: #6890F0; }
    .type-electric { background: #F8D030; color: #333; }
    .type-grass { background: #78C850; }
    .type-ice { background: #98D8D8; color: #333; }
    .type-fighting { background: #C03028; }
    .type-poison { background: #A040A0; }
    .type-ground { background: #E0C068; color: #333;}
    .type-flying { background: #A890F0; }
    .type-psychic { background: #F85888; }
    .type-bug { background: #A8B820; }
    .type-rock { background: #B8A038; }
    .type-ghost { background: #705898; }
    .type-dragon { background: #7038F8; }
    .type-steel { background: #B8B8D0; color: #333; }
    .type-fairy { background: #EE99AC; color: #333; }
    .type-dark { background: #705848; }

    /* Type Icon Grid Filters */
    .type-icon-btn {
        background: white;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 5px;
        text-align: center;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 60px;
    }
    .type-icon-btn img {
        width: 24px;
        height: 24px;
    }
    .type-icon-btn span {
        font-size: 0.7rem;
        color: #333;
        margin-top: 4px;
    }
    .type-icon-btn.selected {
        border: 2px solid #E3350D;
        background: #fdf5f5;
    }

    /* Buttons */
    .btn-search {
        background-color: #E3350D !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 10px 40px !important;
        font-weight: bold !important;
        transform: skew(-15deg);
    }
    .btn-search > span { transform: skew(15deg); display: block; }
    
    .btn-reset {
        background-color: #1a1a1a !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 10px 40px !important;
        font-weight: bold !important;
        transform: skew(-15deg);
    }
    .btn-reset > span { transform: skew(15deg); display: block; }

    /* Load More Button */
    .load-more-container {
        display: flex;
        justify-content: center;
        margin-top: 40px;
        padding-bottom: 40px;
    }

    .stButton.load-more>button {
        background: white !important;
        color: #333 !important;
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
        padding: 10px 30px !important;
    }
    </style>
    """

def render_pokemon_card(id, name, image_url, types_ko_en):
    """
    types_ko_en: List of tuples/dicts [(ko, en), ...]
    """
    type_badges = "".join([f'<span class="type-badge type-{en.lower()}">{ko}</span>' for ko, en in types_ko_en])
    
    return f'''<a href="/pokemon_detail?id={id}" target="_self" class="pokemon-card">
<div class="pokemon-image-wrapper">
<img src="{image_url}" class="pokemon-image" alt="{name}" loading="lazy">
</div>
<div class="pokemon-info">
<div class="pokemon-id-badge">No.{id:04d}</div>
<div class="pokemon-name">{name}</div>
<div class="type-container">
{type_badges}
</div>
</div>
</a>'''

