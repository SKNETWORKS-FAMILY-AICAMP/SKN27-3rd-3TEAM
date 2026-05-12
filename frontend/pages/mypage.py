import streamlit as st
import os
import base64
import math
import requests
from datetime import datetime
import textwrap
from utils.ui import inject_common_ui

_FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _b64_img(rel_path: str) -> str:
    full = os.path.join(_FRONTEND_DIR, rel_path)
    if os.path.exists(full):
        with open(full, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def fetch_user_stats(user_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user_id}/stats", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

def fetch_user_logs(user_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user_id}/logs?limit=8", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

def fetch_github_details(username):
    from concurrent.futures import ThreadPoolExecutor
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Pokemon-Trainer-App"}

    def fetch_user():
        try:
            r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=5)
            if r.status_code == 200:
                d = r.json()
                return d.get("public_repos", 0), d.get("followers", 0)
        except: pass
        return 0, 0

    def fetch_commits():
        try:
            h = {**headers, "Accept": "application/vnd.github.cloak-preview+json"}
            r = requests.get(f"https://api.github.com/search/commits?q=author:{username}", headers=h, timeout=5)
            if r.status_code == 200:
                return r.json().get("total_count", 0)
        except: pass
        return 0

    def fetch_stars():
        try:
            r = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers, timeout=5)
            if r.status_code == 200:
                return sum(repo.get("stargazers_count", 0) for repo in r.json())
        except: pass
        return 0

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_user = ex.submit(fetch_user)
        f_commits = ex.submit(fetch_commits)
        f_stars = ex.submit(fetch_stars)
        repos, followers = f_user.result()
        commits = f_commits.result()
        stars = f_stars.result()

    return {"repos": repos, "followers": followers, "commits": commits, "stars": stars}


def get_mypage_styles():
    return textwrap.dedent("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600;700&display=swap');

    :root {
        --neon-blue: #0984e3;
        --neon-yellow: #f1c40f;
        --neon-green: #27ae60;
        --neon-red: #e74c3c;
        --glass-border: rgba(0, 0, 0, 0.06);
        --text-main: #2d3436;
        --text-sub: #636e72;
        --card-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        --section-gap: 40px;
    }

    .stApp { background-color: #f0f2f5 !important; }

    .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }

    .mypage-container {
        padding: 0 6% 80px;
        background: #f0f2f5;
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }

    /* ── Profile Hero ── */
    .profile-hero {
        background: #fff;
        border-radius: 32px;
        padding: 50px 60px;
        margin-bottom: var(--section-gap);
        display: flex;
        align-items: center;
        gap: 50px;
        box-shadow: var(--card-shadow);
        border: 1px solid var(--glass-border);
    }
    .profile-avatar {
        width: 160px; height: 160px;
        border-radius: 50%;
        border: 4px solid var(--neon-blue);
        object-fit: cover;
        animation: float 6s ease-in-out infinite;
        flex-shrink: 0;
    }
    @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }

    .profile-info { flex: 1; }
    .profile-info h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        font-size: clamp(1.8rem, 4vw, 3rem);
        color: var(--text-main);
        margin: 0 0 6px;
        letter-spacing: -1.5px;
    }
    .profile-info .sub { color: var(--text-sub); font-size: 1rem; margin-bottom: 16px; }

    .tier-badge {
        display: inline-block;
        padding: 6px 20px;
        background: var(--neon-yellow);
        color: #000;
        border-radius: 50px;
        font-weight: 900;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-right: 10px;
    }

    .xp-wrap { margin-top: 20px; }
    .xp-label { font-size: 0.8rem; color: var(--text-sub); font-weight: 700; margin-bottom: 6px; }
    .xp-track {
        background: #e9ecef;
        border-radius: 99px;
        height: 10px;
        overflow: hidden;
        width: 100%;
        max-width: 400px;
    }
    .xp-fill {
        height: 100%;
        border-radius: 99px;
        background: linear-gradient(90deg, #0984e3, #00cec9);
        transition: width 1s ease;
    }

    .logout-btn {
        display: inline-block;
        padding: 8px 20px;
        background: #f1f2f6;
        color: var(--text-main) !important;
        text-decoration: none !important;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.85rem;
        margin-top: 16px;
        transition: background 0.2s;
    }
    .logout-btn:hover { background: #dfe6e9; }

    /* ── Quick Actions ── */
    .quick-actions {
        margin-bottom: var(--section-gap);
    }
    .section-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        font-size: 1.5rem;
        margin-bottom: 20px;
        color: var(--text-main);
    }
    .action-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 16px;
    }
    .action-card {
        background: #fff;
        border-radius: 20px;
        padding: 28px 20px;
        text-align: center;
        text-decoration: none !important;
        color: var(--text-main) !important;
        border: 1px solid var(--glass-border);
        box-shadow: var(--card-shadow);
        transition: all 0.25s ease;
        display: block;
    }
    .action-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.10);
    }
    .action-icon { font-size: 2.2rem; margin-bottom: 10px; }
    .action-label { font-weight: 700; font-size: 0.9rem; }
    .action-sub { font-size: 0.75rem; color: var(--text-sub); margin-top: 4px; }

    /* ── Stats Grid ── */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-bottom: var(--section-gap);
    }
    .stat-card {
        background: #fff;
        border-radius: 24px;
        padding: 32px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--card-shadow);
        transition: all 0.3s ease;
    }
    .stat-card:hover { transform: translateY(-4px); box-shadow: 0 15px 35px rgba(0,0,0,0.08); }
    .stat-label { font-size: 0.78rem; color: var(--text-sub); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; }
    .stat-value { font-family: 'Outfit', sans-serif; font-size: 2.6rem; font-weight: 900; line-height: 1; }
    .stat-desc { font-size: 0.82rem; color: var(--text-sub); margin-top: 8px; }

    /* ── Game Performance ── */
    .game-section {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: var(--section-gap);
    }
    .game-card {
        background: #fff;
        border-radius: 24px;
        padding: 36px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--card-shadow);
    }
    .game-card-title { font-size: 0.85rem; font-weight: 700; color: var(--text-sub); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 16px; }
    .game-big { font-family: 'Outfit', sans-serif; font-size: 2.8rem; font-weight: 900; line-height: 1; margin-bottom: 6px; }
    .game-sub { font-size: 0.85rem; color: var(--text-sub); margin-bottom: 20px; }

    .acc-track { background: #f0f2f5; border-radius: 99px; height: 8px; overflow: hidden; margin-bottom: 6px; }
    .acc-fill { height: 100%; border-radius: 99px; }
    .acc-label { font-size: 0.78rem; color: var(--text-sub); font-weight: 600; }

    /* Pokédex progress full-width card */
    .pokedex-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 24px;
        padding: 36px;
        margin-bottom: var(--section-gap);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: var(--card-shadow);
        color: #fff;
    }
    .pokedex-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }
    .pokedex-title { font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 1.4rem; }
    .pokedex-count { font-family: 'Outfit', sans-serif; font-size: 2.4rem; font-weight: 900; color: #f1c40f; }
    .pokedex-track { background: rgba(255,255,255,0.1); border-radius: 99px; height: 14px; overflow: hidden; }
    .pokedex-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #f1c40f, #fd9644); }
    .pokedex-foot { margin-top: 10px; font-size: 0.82rem; color: rgba(255,255,255,0.4); }

    /* ── Gym Badge Wheel ── */
    .badge-section {
        background: #fff;
        border-radius: 24px;
        padding: 40px;
        margin-bottom: var(--section-gap);
        border: 1px solid var(--glass-border);
        box-shadow: var(--card-shadow);
        display: flex;
        align-items: center;
        gap: 60px;
    }
    .badge-wheel-wrap { flex-shrink: 0; }
    .badge-wheel {
        position: relative;
        width: 320px; height: 320px;
        border-radius: 50%;
        background: radial-gradient(circle at 40% 35%, #f5e87a, #d4a830 55%, #a07420);
        box-shadow: 0 0 0 6px #c8993a, 0 0 0 10px #e8c060, 0 12px 40px rgba(180,130,30,0.5);
    }
    /* sector dividers */
    .badge-wheel::before {
        content: '';
        position: absolute; inset: 12px;
        border-radius: 50%;
        background: transparent;
        border: 2px solid rgba(255,255,255,0.15);
        pointer-events: none;
    }
    .badge-slot {
        position: absolute;
        width: 72px; height: 72px;
        border-radius: 50%;
        overflow: hidden;
        transition: all 0.4s ease;
    }
    .badge-slot img {
        width: 100%; height: 100%;
        object-fit: contain;
        display: block;
        transition: all 0.4s ease;
    }
    .badge-slot.locked img {
        filter: grayscale(1) brightness(0.35);
    }
    .badge-slot.unlocked {
        box-shadow: 0 0 16px 4px rgba(255,230,80,0.7), 0 0 0 2px rgba(255,220,50,0.5);
    }
    .badge-slot.unlocked img {
        filter: drop-shadow(0 0 6px rgba(255,230,100,0.9));
    }
    .wheel-center {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        background: radial-gradient(circle, #7a5010, #4a3008);
        border-radius: 50%;
        width: 72px; height: 72px;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        box-shadow: 0 0 0 3px #c8993a, inset 0 2px 8px rgba(0,0,0,0.5);
    }
    .wheel-count { font-family: 'Outfit', sans-serif; font-size: 1.6rem; font-weight: 900; color: #f5e87a; line-height: 1; }
    .wheel-label { font-size: 0.6rem; color: rgba(245,232,122,0.7); font-weight: 700; letter-spacing: 1px; }

    /* badge legend list */
    .badge-legend { flex: 1; }
    .badge-legend-title { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 900; color: var(--text-main); margin-bottom: 20px; }
    .badge-legend-item {
        display: flex; align-items: center; gap: 14px;
        padding: 10px 0;
        border-bottom: 1px solid #f1f2f6;
        opacity: 0.4;
        transition: opacity 0.3s;
    }
    .badge-legend-item.unlocked { opacity: 1; }
    .badge-legend-item:last-child { border-bottom: none; }
    .legend-thumb { width: 36px; height: 36px; object-fit: contain; flex-shrink: 0; }
    .legend-thumb.locked { filter: grayscale(1) brightness(0.5); }
    .legend-info { flex: 1; }
    .legend-name { font-weight: 700; font-size: 0.9rem; color: var(--text-main); }
    .legend-cond { font-size: 0.78rem; color: var(--text-sub); margin-top: 2px; }
    .legend-check { font-size: 1rem; }

    /* ── Activity ── */
    .activity-section {
        background: #fff;
        border-radius: 24px;
        padding: 40px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--card-shadow);
    }
    .activity-item {
        display: flex;
        align-items: center;
        padding: 18px 0;
        border-bottom: 1px solid #f1f2f6;
        gap: 20px;
    }
    .activity-item:last-child { border-bottom: none; }
    .activity-icon {
        width: 48px; height: 48px;
        background: #f8f9fa;
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem;
        flex-shrink: 0;
    }
    .activity-details { flex: 1; }
    .activity-main { font-weight: 700; font-size: 0.95rem; color: var(--text-main); }
    .activity-sub { font-size: 0.8rem; color: var(--text-sub); margin-top: 2px; }
    .activity-time { font-size: 0.8rem; color: #b2bec3; flex-shrink: 0; }
    .status-tag { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 0.65rem; font-weight: 900; margin-left: 10px; text-transform: uppercase; }
    .status-success { background: #e6fffa; color: #27ae60; border: 1px solid #c6f6d5; }
    .status-fail { background: #fff5f5; color: #e53e3e; border: 1px solid #fed7d7; }

    .empty-state { text-align: center; padding: 50px 0; color: var(--text-sub); font-size: 0.95rem; }

    @media (max-width: 1024px) {
        .action-grid { grid-template-columns: repeat(3, 1fr); }
        .stats-grid { grid-template-columns: repeat(2, 1fr); }
        .badge-grid { grid-template-columns: repeat(4, 1fr); }
    }
    @media (max-width: 768px) {
        .profile-hero { flex-direction: column; text-align: center; padding: 36px; gap: 30px; }
        .action-grid { grid-template-columns: repeat(2, 1fr); }
        .game-section { grid-template-columns: 1fr; }
        .stats-grid { grid-template-columns: 1fr 1fr; }
        .badge-grid { grid-template-columns: repeat(4, 1fr); }
    }
    </style>
    """)


def show():
    st.set_page_config(
        page_title="마이페이지",
        page_icon="https://pokemonkorea.co.kr/img/_con.ico",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    inject_common_ui(spacer=False)

    st.markdown("""
        <style>
            .block-container { padding: 0 !important; }
            .mypage-container { padding-top: 90px !important; margin-top: 0 !important; }
        </style>
    """, unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.warning("로그인이 필요한 페이지입니다.")
        st.button("로그인 하러 가기", on_click=lambda: st.switch_page("pages/login.py"))
        return

    user = st.session_state.user
    user_id = user.get("db_id")
    username = user.get("login")

    repos    = user.get("public_repos", 0)
    commits  = user.get("total_commits", 0)
    stars    = user.get("total_stars", 0)
    followers = user.get("followers", 0)

    from concurrent.futures import ThreadPoolExecutor
    _gh_cache_key = f"_gh_{username}"

    def _maybe_fetch_github():
        if repos == 0 and commits == 0 and username:
            if _gh_cache_key in st.session_state:
                return st.session_state[_gh_cache_key]
            gh = fetch_github_details(username)
            st.session_state[_gh_cache_key] = gh
            return gh
        return None

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_gh    = ex.submit(_maybe_fetch_github)
        f_stats = ex.submit(fetch_user_stats, user_id) if user_id else None
        f_logs  = ex.submit(fetch_user_logs, user_id)  if user_id else None
        gh      = f_gh.result()
        stats   = f_stats.result() if f_stats else None
        logs    = f_logs.result()  if f_logs  else []

    if gh:
        repos     = gh["repos"]
        commits   = gh["commits"]
        stars     = gh["stars"]
        followers = gh["followers"]

    # ── Game stats ──
    s_total   = stats.get("silhouette", {}).get("total", 0)   if stats else 0
    s_correct = stats.get("silhouette", {}).get("correct", 0) if stats else 0
    m_total   = stats.get("memory", {}).get("total", 0)       if stats else 0
    m_correct = stats.get("memory", {}).get("correct", 0)     if stats else 0
    total_games   = s_total + m_total
    total_correct = s_correct + m_correct

    s_rate = int(s_correct / s_total * 100) if s_total > 0 else 0
    m_rate = int(m_correct / m_total * 100) if m_total > 0 else 0

    # ── Score & Level ──
    game_score  = total_correct * 10
    gh_score    = (repos * 100) + (followers * 20) + (commits * 10) + (stars * 50)
    total_score = game_score + gh_score
    level       = min(99, int(commits / 10) + int(total_correct / 5) + 1)
    xp_pct      = (level % 10) * 10

    # ── Tier ──
    if commits > 1000 or repos > 100: trainer_tier = "Legendary Developer"
    elif commits > 300 or repos > 30: trainer_tier = "Veteran Developer"
    elif commits > 50:                trainer_tier = "Active Developer"
    else:                             trainer_tier = "Rookie Developer"

    avatar = user.get("avatar_url", "https://cdn-icons-png.flaticon.com/512/1144/1144760.png")
    name   = user.get("name") or user.get("login", "트레이너")

    st.markdown(get_mypage_styles(), unsafe_allow_html=True)
    st.markdown('<div class="mypage-container">', unsafe_allow_html=True)

    # ════════════════════════════════
    # 1. Profile Hero
    # ════════════════════════════════
    st.markdown(f"""
    <div class="profile-hero">
        <img src="{avatar}" class="profile-avatar">
        <div class="profile-info">
            <h1>{name}</h1>
            <div class="sub">@{username} · Pokemon Trainer</div>
            <span class="tier-badge">{trainer_tier}</span>
            <div class="xp-wrap">
                <div class="xp-label">Lv.{level} &nbsp;·&nbsp; {xp_pct}/100 XP to next level</div>
                <div class="xp-track"><div class="xp-fill" style="width:{xp_pct}%"></div></div>
            </div>
            <a href="/login?do_logout=true" target="_self" class="logout-btn">🚪 로그아웃</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════
    # 3. GitHub Dev Stats
    # ════════════════════════════════
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">💻 Commits</div>
            <div class="stat-value" style="color:var(--neon-blue);">{commits:,}</div>
            <div class="stat-desc">전체 퍼블릭 기여</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">📦 Repos</div>
            <div class="stat-value" style="color:var(--neon-green);">{repos}</div>
            <div class="stat-desc">퍼블릭 레포지토리</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">⭐ Stars</div>
            <div class="stat-value" style="color:var(--neon-yellow);">{stars}</div>
            <div class="stat-desc">받은 스타 총합</div>
        </div>
        <div class="stat-card" style="background:linear-gradient(135deg,#1e293b,#0f172a);border-color:rgba(255,255,255,0.08);">
            <div class="stat-label" style="color:rgba(255,255,255,0.5);">🏆 Trainer Score</div>
            <div class="stat-value" style="color:#fff;">{total_score:,}</div>
            <div class="stat-desc" style="color:rgba(255,255,255,0.35);">Game {game_score:,} + Dev {gh_score:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════
    # 4. Game Performance
    # ════════════════════════════════
    st.markdown(f"""
    <div class="game-section">
        <div class="game-card">
            <div class="game-card-title">🔍 실루엣 퀴즈</div>
            <div class="game-big" style="color:var(--neon-blue);">{s_correct}<span style="font-size:1.2rem;font-weight:400;color:var(--text-sub);">/{s_total}</span></div>
            <div class="game-sub">정답 / 도전 횟수</div>
            <div class="acc-track">
                <div class="acc-fill" style="width:{s_rate}%;background:linear-gradient(90deg,#0984e3,#00cec9);"></div>
            </div>
            <div class="acc-label">정답률 {s_rate}%</div>
        </div>
        <div class="game-card">
            <div class="game-card-title">🧠 메모리 게임</div>
            <div class="game-big" style="color:var(--neon-green);">{m_correct}<span style="font-size:1.2rem;font-weight:400;color:var(--text-sub);">/{m_total}</span></div>
            <div class="game-sub">정답 / 도전 횟수</div>
            <div class="acc-track">
                <div class="acc-fill" style="width:{m_rate}%;background:linear-gradient(90deg,#27ae60,#00b894);"></div>
            </div>
            <div class="acc-label">정답률 {m_rate}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════
    # 5. Pokédex Progress
    # ════════════════════════════════
    TOTAL_POKEMON = 1025
    pokedex_pct   = min(100, round(s_correct / TOTAL_POKEMON * 100, 1))
    st.markdown(f"""
    <div class="pokedex-card">
        <div class="pokedex-header">
            <div>
                <div class="pokedex-title">📖 포켓덱스 진행도</div>
                <div style="font-size:0.85rem;color:rgba(255,255,255,0.4);margin-top:4px;">실루엣 퀴즈 정답 기준 · 전 세대 {TOTAL_POKEMON:,}종</div>
            </div>
            <div class="pokedex-count">{s_correct} <span style="font-size:1rem;color:rgba(255,255,255,0.4);">/ {TOTAL_POKEMON:,}</span></div>
        </div>
        <div class="pokedex-track">
            <div class="pokedex-fill" style="width:{pokedex_pct}%"></div>
        </div>
        <div class="pokedex-foot">{pokedex_pct}% 완성 · 앞으로 {TOTAL_POKEMON - s_correct}종 남음</div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════
    # 6. Gym Badge Wheel (가라르 배지)
    # ════════════════════════════════
    # 배지 정의 — 파일명, 한글명, 해제 조건 순으로 (쉬운 것부터)
    badges = [
        {"file": "풀",    "name": "풀 배지",    "desc": "첫 게임 플레이",           "unlocked": total_games >= 1},
        {"file": "물",    "name": "물 배지",    "desc": "첫 정답",                  "unlocked": total_correct >= 1},
        {"file": "불꽃",  "name": "불꽃 배지",  "desc": "10번 도전",                "unlocked": total_games >= 10},
        {"file": "페어리","name": "페어리 배지","desc": "정답률 70% 이상",           "unlocked": (s_rate >= 70 and s_total >= 5) or (m_rate >= 70 and m_total >= 5)},
        {"file": "고스트","name": "고스트 배지","desc": "50게임 돌파",              "unlocked": total_games >= 50},
        {"file": "얼음",  "name": "얼음 배지",  "desc": "GitHub 연동 (레포 보유)",  "unlocked": repos > 0},
        {"file": "악",    "name": "악 배지",    "desc": "커밋 100개 이상",          "unlocked": commits >= 100},
        {"file": "드래곤","name": "드래곤 배지","desc": "레전더리 개발자",           "unlocked": commits >= 1000 or repos >= 100},
    ]
    unlocked_count = sum(1 for b in badges if b["unlocked"])

    # 배지 이미지: 세션당 1회만 로드 (base64 캐시)
    if "_badge_imgs" not in st.session_state:
        st.session_state["_badge_imgs"] = {
            b["file"]: _b64_img(f"img/badge/{b['file']}.png") for b in badges
        }
    imgs = st.session_state["_badge_imgs"]

    # ── 휠 슬롯 HTML (이미지 8개)
    _r, _cx, _cy, _sz = 110, 160, 160, 72
    wheel_slots = ""
    for i, b in enumerate(badges):
        rad = math.radians(i * 45)
        lx  = _cx + _r * math.sin(rad) - _sz / 2
        ty  = _cy - _r * math.cos(rad) - _sz / 2
        cls = "unlocked" if b["unlocked"] else "locked"
        wheel_slots += (
            f'<div class="badge-slot {cls}" style="left:{lx:.0f}px;top:{ty:.0f}px;">'
            f'<img src="{imgs[b["file"]]}" alt="{b["name"]}"></div>'
        )

    # ── 범례: 이미지 없이 타입 컬러 원 + 텍스트 (HTML 경량화)
    TYPE_COLORS = {
        "풀": "#27ae60", "물": "#2980b9", "불꽃": "#e74c3c",
        "페어리": "#e91e8c", "고스트": "#7e57c2", "얼음": "#00bcd4",
        "악": "#37474f", "드래곤": "#1565c0",
    }
    legend_rows = ""
    for b in badges:
        cls   = "unlocked" if b["unlocked"] else ""
        check = "✅" if b["unlocked"] else "🔒"
        color = TYPE_COLORS.get(b["file"], "#aaa")
        dot_style = (
            f"width:32px;height:32px;border-radius:50%;background:{color};"
            f"flex-shrink:0;box-shadow:0 2px 8px {color}66;"
            + ("" if b["unlocked"] else "filter:grayscale(1);opacity:0.3;")
        )
        legend_rows += f"""<div class="badge-legend-item {cls}">
            <div style="{dot_style}"></div>
            <div class="legend-info">
                <div class="legend-name">{b["name"]}</div>
                <div class="legend-cond">{b["desc"]}</div>
            </div>
            <span class="legend-check">{check}</span>
        </div>"""

    # ── 휠과 범례를 별도 컬럼으로 렌더링 (한 번에 base64 × 16개 방지)
    col_w, col_l = st.columns([1, 1.3], gap="large")

    with col_w:
        st.markdown(f"""
        <div style="background:#fff;border-radius:24px;padding:32px;
                    border:1px solid #f0f0f0;box-shadow:0 10px 30px rgba(0,0,0,0.05);
                    display:flex;flex-direction:column;align-items:center;gap:16px;">
            <div class="badge-wheel" style="flex-shrink:0;">
                {wheel_slots}
                <div class="wheel-center">
                    <div class="wheel-count">{unlocked_count}</div>
                    <div class="wheel-label">/ 8</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_l:
        st.markdown(f"""
        <div style="background:#fff;border-radius:24px;padding:32px;
                    border:1px solid #f0f0f0;box-shadow:0 10px 30px rgba(0,0,0,0.05);height:100%;">
            <div class="badge-legend-title">🏅 가라르 도장 배지
                <span style="font-size:0.9rem;font-weight:400;color:#636e72;margin-left:8px;">{unlocked_count}/8 획득</span>
            </div>
            {legend_rows}
        </div>
        """, unsafe_allow_html=True)

    # ════════════════════════════════
    # 7. Recent Activity
    # ════════════════════════════════
    st.markdown('<div class="activity-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🕒 최근 활동</div>', unsafe_allow_html=True)

    if not logs:
        st.markdown('<div class="empty-state">아직 기록이 없습니다. 미니게임을 플레이해보세요! 🎮</div>', unsafe_allow_html=True)
    else:
        GAME_NAMES = {"silhouette": "실루엣 퀴즈", "memory": "메모리 게임"}
        GAME_ICONS = {"silhouette": "🔍", "memory": "🧠"}
        for log in logs:
            g_type  = log.get("game_type", "")
            g_name  = GAME_NAMES.get(g_type, g_type)
            icon    = GAME_ICONS.get(g_type, "🎮")
            correct = log.get("is_correct")
            tag_cls = "status-success" if correct else "status-fail"
            tag_txt = "정답" if correct else "오답"
            pokemon = log.get("pokemon_name", "")
            sub     = f"포켓몬: {pokemon}" if pokemon else "트레이너 포인트 획득"

            ts = log.get("created_at", "")
            time_str = ""
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    time_str = dt.strftime("%m/%d %H:%M")
                except: pass

            st.markdown(f"""
            <div class="activity-item">
                <div class="activity-icon">{icon}</div>
                <div class="activity-details">
                    <div class="activity-main">{g_name} <span class="status-tag {tag_cls}">{tag_txt}</span></div>
                    <div class="activity-sub">{sub}</div>
                </div>
                <div class="activity-time">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # activity-section
    st.markdown('</div>', unsafe_allow_html=True)  # mypage-container


if __name__ == "__main__":
    show()
