import streamlit as st
import os
import base64
import math
import requests
from datetime import datetime
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
        except:
            pass
        return 0, 0

    def fetch_commits():
        try:
            h = {**headers, "Accept": "application/vnd.github.cloak-preview+json"}
            r = requests.get(f"https://api.github.com/search/commits?q=author:{username}", headers=h, timeout=5)
            if r.status_code == 200:
                return r.json().get("total_count", 0)
        except:
            pass
        return 0

    def fetch_stars():
        try:
            r = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers, timeout=5)
            if r.status_code == 200:
                return sum(repo.get("stargazers_count", 0) for repo in r.json())
        except:
            pass
        return 0

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_user    = ex.submit(fetch_user)
        f_commits = ex.submit(fetch_commits)
        f_stars   = ex.submit(fetch_stars)
        repos, followers = f_user.result()
        commits          = f_commits.result()
        stars            = f_stars.result()

    return {"repos": repos, "followers": followers, "commits": commits, "stars": stars}


MYPAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #000000 !important; /* 기본 배경을 검정으로 설정하여 이미지와 조화 */
}
[data-testid="stAppViewContainer"] {
    background-image: var(--bg-img) !important;
    background-size: cover !important;
    background-attachment: fixed !important;
    background-position: center top !important;
}
[data-testid="stHeader"], footer, [data-testid="stToolbar"] { display: none !important; }
.block-container { 
    padding: 0 !important; 
    margin: 0 !important; 
    max-width: 100% !important; 
}

.mp-wrap {
    padding: 20px 0 10px;
    font-family: 'Inter', sans-serif;
    color: #2d3436;
    min-height: 30vh;
}
.mp-container {
    margin: 0 auto;
    width: 75%;
    max-width: 1000px;
}

/* ── Premium Glass Card ── */
.mp-card {
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(25px) saturate(180%);
    -webkit-backdrop-filter: blur(25px) saturate(180%);
    border-radius: 28px;
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.12);
    margin: 0 auto 40px;
    width: 75%;
    max-width: 1000px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    transition: all 0.3s ease;
    overflow: hidden;
    position: relative;
    padding: 45px; /* 패딩 증가 */
}
.mp-card:hover { transform: translateY(-4px); background: rgba(255, 255, 255, 0.55); box-shadow: 0 20px 55px rgba(0,0,0,0.2); }

/* 섹션별 보더 컬러 포인트 */
.card-profile { border-top: 6px solid #FFCB05; padding: 50px; }
.card-actions { border-top: 6px solid #0984e3; }
.card-dev     { border-top: 6px solid #6c5ce7; }
.card-game    { border-top: 6px solid #ff4757; }
.card-dex     { border-top: 6px solid #27ae60; }
.card-badge   { border-top: 6px solid #fd9644; }
.card-activity { border-top: 6px solid #b2bec3; padding: 20px 40px; }

/* ── Labels / Badges ── */
.mp-pill {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 50px;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    background: rgba(241, 242, 246, 0.8);
    color: #2d3436;
    margin-bottom: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.mp-pill-yellow { background: #FFCB05; color: #000; box-shadow: 0 0 15px rgba(255, 203, 5, 0.4); }

/* ── Section Title (Minigame Style) ── */
.mp-section-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 1.6rem;
    color: #ffffff;
    letter-spacing: -0.5px;
    margin: 0 auto 25px;
    width: 75%;
    max-width: 1000px;
    display: flex;
    align-items: center;
    gap: 10px;
    text-shadow: 0 2px 15px rgba(0,0,0,0.5), 0 0 10px rgba(255, 203, 5, 0.3);
}
.mp-section-title::before {
    content: ''; width: 8px; height: 24px; background: #FFCB05; border-radius: 4px;
    box-shadow: 0 0 10px #FFCB05;
}

/* ── Profile Hero ── */
.mp-hero {
    padding: 40px 50px;
    display: flex;
    align-items: center;
    gap: 40px;
}
.mp-avatar {
    width: 130px; height: 130px;
    border-radius: 50%;
    border: 4px solid #FFCB05;
    object-fit: cover;
    animation: mpfloat 6s ease-in-out infinite;
    flex-shrink: 0;
    box-shadow: 0 10px 30px rgba(255, 203, 5, 0.3);
}
@keyframes mpfloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.mp-name {
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 3rem;
    color: #2d3436;
    letter-spacing: -1px;
    margin: 0;
    text-shadow: 0 0 20px rgba(255,255,255,0.8);
}
.mp-handle { font-size: 1rem; color: #2d3436; margin-bottom: 15px; font-weight: 600; }

/* ── Hero Creature & Friends Animation ── */
.mp-hero-creature-wrap {
    display: flex;
    align-items: flex-end;
    gap: 15px;
    flex-shrink: 0;
    margin-right: 20px;
}
.mp-hero-friends {
    position: relative;
    width: 100px;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.mp-hero-friends img {
    height: 80px;
    object-fit: contain;
    animation: mpfloat 5s ease-in-out infinite;
    animation-delay: -1.5s;
    opacity: 0.85;
}
.mp-hero-creature {
    position: relative;
    width: 200px;
    height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.mp-hero-creature img {
    height: 160px;
    object-fit: contain;
    z-index: 2;
    animation: mpfloat 4s ease-in-out infinite;
    filter: drop-shadow(0 10px 25px rgba(0,0,0,0.15));
}
.mp-creature-glow {
    position: absolute;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(255, 203, 5, 0.3) 0%, rgba(255, 203, 5, 0) 70%);
    z-index: 1;
    border-radius: 50%;
    animation: mpglow 4s ease-in-out infinite;
}
@keyframes mpglow {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.2); opacity: 0.8; }
}
@media (max-width: 1100px) {
    .mp-hero-friends { display: none; }
}
@media (max-width: 900px) {
    .mp-hero-creature-wrap { display: none; }
}

/* ── Stats Box (Minigame Style) ── */
.mp-stat-value {
    font-family: 'Outfit', sans-serif;
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
    color: #2d3436;
    text-shadow: 0 0 15px rgba(255,255,255,0.8), 0 2px 5px rgba(0,0,0,0.1);
}
.mp-stat-label {
    font-size: 0.75rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #2d3436;
    margin-bottom: 8px;
    opacity: 0.8;
}

/* ── Activity Log (Premium Light) ── */
.mp-log-item {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 22px;
    border-bottom: 1px solid rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.mp-log-item:hover { background: rgba(255,255,255,0.3); }
.mp-log-icon {
    width: 50px; height: 50px;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 15px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; color: #2d3436; font-size: 0.85rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
.mp-log-main { 
    font-weight: 800; font-size: 1.05rem; color: #2d3436;
    text-shadow: 0 0 10px rgba(255,255,255,0.5);
}
.mp-log-sub { font-size: 0.9rem; color: #636e72; font-weight: 500; }
.mp-tag {
    padding: 4px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: 900; text-transform: uppercase;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.mp-tag-ok { background: #e6fffa; color: #27ae60; border: 1px solid rgba(39, 174, 96, 0.2); }
.mp-tag-fail { background: #fff5f5; color: #e53e3e; border: 1px solid rgba(229, 62, 62, 0.2); }

/* ── Progress Bar ── */
.mp-xp-track { background: #f1f2f6; border-radius: 99px; height: 8px; overflow: hidden; }
.mp-xp-fill { height: 100%; background: linear-gradient(90deg, #FFCB05, #fd9644); border-radius: 99px; }

.mp-logout {
    padding: 8px 20px; border-radius: 100px; font-size: 0.8rem; font-weight: 700;
    color: #b2bec3 !important; text-decoration: none !important;
    border: 1px solid #f1f2f6; transition: 0.2s;
}
.mp-logout:hover { background: #f1f2f6; color: #2d3436 !important; }

@media (max-width: 768px) {
    .mp-hero { flex-direction: column; text-align: center; padding: 30px; }
}
</style>
"""


def show():
    st.set_page_config(
        page_title="마이페이지",
        page_icon="https://pokemonkorea.co.kr/img/_con.ico",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 배경 이미지 로드 및 CSS 주입 (최상단 배치로 레이아웃 밀림 방지)
    bg_b64 = _b64_img("img/mypage.png")
    st.markdown(f"""
    <style>
    :root {{
        --bg-img: url('{bg_b64}');
    }}
    /* 상단 공백 강제 제거 */
    [data-testid="stAppViewBlockContainer"] {{ padding-top: 0 !important; }}
    [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(MYPAGE_CSS, unsafe_allow_html=True)

    inject_common_ui(spacer=False)

    if "user" not in st.session_state:
        st.warning("로그인이 필요한 페이지입니다.")
        st.button("로그인 하러 가기", on_click=lambda: st.switch_page("pages/login.py"))
        return

    user     = st.session_state.user
    user_id  = user.get("db_id")
    username = user.get("login")

    repos     = user.get("public_repos", 0)
    commits   = user.get("total_commits", 0)
    stars     = user.get("total_stars", 0)
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

    s_total   = stats.get("silhouette", {}).get("total", 0)   if stats else 0
    s_correct = stats.get("silhouette", {}).get("correct", 0) if stats else 0
    m_total   = stats.get("memory", {}).get("total", 0)       if stats else 0
    m_correct = stats.get("memory", {}).get("correct", 0)     if stats else 0
    total_games   = s_total + m_total
    total_correct = s_correct + m_correct

    s_rate = int(s_correct / s_total * 100) if s_total > 0 else 0
    m_rate = int(m_correct / m_total * 100) if m_total > 0 else 0

    game_score  = total_correct * 10
    gh_score    = (repos * 100) + (followers * 20) + (commits * 10) + (stars * 50)
    total_score = game_score + gh_score
    level       = min(99, int(commits / 10) + int(total_correct / 5) + 1)
    xp_pct      = (level % 10) * 10

    if   commits > 1000 or repos > 100: trainer_tier = "Legendary Developer"
    elif commits > 300  or repos > 30:  trainer_tier = "Veteran Developer"
    elif commits > 50:                  trainer_tier = "Active Developer"
    else:                               trainer_tier = "Rookie Developer"

    # 등급별 대표 포켓몬 매핑 (애니메이션 GIF)
    TIER_POKEMON = {
        "Legendary Developer": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/150.gif", # 뮤츠
        "Veteran Developer":  "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/6.gif",   # 리자몽
        "Active Developer":   "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/25.gif",  # 피카츄
        "Rookie Developer":   "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/1.gif",   # 이상해씨
    }
    # 등급별 친구 포켓몬들 매핑
    TIER_FRIENDS = {
        "Legendary Developer": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/151.gif", # 뮤
        "Veteran Developer":  "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/4.gif",   # 파이리
        "Active Developer":   "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/172.gif", # 피츄
        "Rookie Developer":   "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/7.gif",   # 꼬부기
    }
    hero_pkmn    = TIER_POKEMON.get(trainer_tier, TIER_POKEMON["Rookie Developer"])
    hero_friends = TIER_FRIENDS.get(trainer_tier, TIER_FRIENDS["Rookie Developer"])

    avatar = user.get("avatar_url", "https://cdn-icons-png.flaticon.com/512/1144/1144760.png")
    name   = user.get("name") or user.get("login", "트레이너")

    st.markdown('<div class="mp-wrap">', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # 1. Profile Hero (Yellow Border)
    # ══════════════════════════════════════════
    st.markdown(f"""
    <div class="mp-card card-profile mp-hero">
        <div style="display: flex; align-items: center; gap: 40px; flex: 1;">
            <img src="{avatar}" class="mp-avatar">
            <div class="mp-hero-info">
                <div class="mp-pill mp-pill-yellow">{trainer_tier}</div>
                <h1 class="mp-name">{name}</h1>
                <div class="mp-handle">@{username} &nbsp;·&nbsp; Pokemon Trainer</div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div class="mp-logout">Lv.{level} Master</div>
                    <a href="/login?do_logout=true" target="_self" class="mp-logout">로그아웃</a>
                </div>
            </div>
        </div>
        <div class="mp-hero-creature-wrap">
            <div class="mp-hero-friends">
                <img src="{hero_friends}" alt="friend-pokemon">
            </div>
            <div class="mp-hero-creature">
                <img src="{hero_pkmn}" alt="tier-pokemon">
                <div class="mp-creature-glow"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # 3. Stats Grid & 4. Recent Activity (Inside Container)
    # ══════════════════════════════════════════
    st.markdown('<div class="mp-container">', unsafe_allow_html=True)
    
    # Developer Stats
    st.markdown('<div class="mp-section-title">Developer Stats</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="mp-card card-dev">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
            <div>
                <div class="mp-stat-label">Commits</div>
                <div class="mp-stat-value" style="color:#6c5ce7; font-size: 2.2rem;">{commits:,}</div>
            </div>
            <div>
                <div class="mp-stat-label">Repos</div>
                <div class="mp-stat-value" style="color:#2ecc71; font-size: 2.2rem;">{repos}</div>
            </div>
            <div>
                <div class="mp-stat-label">Stars</div>
                <div class="mp-stat-value" style="color:#f1c40f; font-size: 2.2rem;">{stars}</div>
            </div>
            <div>
                <div class="mp-stat-label">Followers</div>
                <div class="mp-stat-value" style="color:#0984e3; font-size: 2.2rem;">{followers}</div>
            </div>
        </div>
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(0,0,0,0.05);">
            <div class="mp-stat-label">Overall Rank</div>
            <div style="font-weight: 900; font-size: 1.2rem; color: #6c5ce7;">{trainer_tier}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Game Performance
    st.markdown('<div class="mp-section-title">Game Performance</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="mp-card card-game">
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
            <div>
                <div class="mp-stat-label">Quiz Accuracy</div>
                <div class="mp-stat-value" style="color:#ff4757;">{s_rate}%</div>
            </div>
            <div>
                <div class="mp-stat-label">Memory Record</div>
                <div class="mp-stat-value" style="color:#e67e22;">{m_rate}%</div>
            </div>
        </div>
        <div style="margin-top: 30px;">
            <div class="mp-stat-label">Trainer Score</div>
            <div class="mp-stat-value" style="font-size: 2.2rem;">{total_score:,} PTS</div>
        </div>
        <div style="margin-top: 20px;">
            <div class="mp-xp-track"><div class="mp-xp-fill" style="width:{xp_pct}%"></div></div>
            <div style="font-size: 0.75rem; color: #2d3436; margin-top: 5px; font-weight:600;">Progress to Next Level: {xp_pct}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # 4. My Pokemon Collection (Pokedex)
    # ══════════════════════════════════════════
    # 획득한 포켓몬 ID 추출 (is_correct=True인 로그에서)
    collected_ids = sorted(list(set([log.get("pokemon_id") for log in logs if log.get("is_correct") and log.get("pokemon_id")])))
    
    st.markdown('<div class="mp-section-title">My Pokemon Collection</div>', unsafe_allow_html=True)
    
    if not collected_ids:
        st.markdown(f"""<div class="mp-card card-dex" style="text-align:center; padding: 60px;"><div style="font-size: 3rem; margin-bottom: 20px;">🥚</div><div style="font-weight: 800; color: #2d3436; font-size: 1.2rem;">아직 획득한 포켓몬이 없습니다.</div><div style="color: #636e72; margin-top: 10px;">퀴즈를 맞추고 도감을 채워보세요!</div></div>""", unsafe_allow_html=True)
    else:
        # 도감 그리드 생성 (공백 제거하여 코드 블록 오인 방지)
        dex_items = []
        for pid in collected_ids:
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png"
            dex_items.append(f'<div style="text-align:center; background: rgba(255,255,255,0.4); border-radius: 15px; padding: 10px; border: 1px solid rgba(255,255,255,0.6);"><img src="{img_url}" style="width: 100%; height: auto; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));"><div style="font-size: 0.65rem; font-weight: 800; color: #2d3436; margin-top: 5px;">No.{pid}</div></div>')
        
        dex_grid = "".join(dex_items)
        st.markdown(f"""
<div class="mp-card card-dex">
<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 15px;">
{dex_grid}
</div>
<div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid rgba(0,0,0,0.05); text-align: right;">
<span style="font-weight: 900; color: #27ae60; font-size: 1.1rem;">Total Collected: {len(collected_ids)} POKEMON</span>
</div>
</div>
""", unsafe_allow_html=True)

    # 5. Recent Activity (Now inside Container)
    st.markdown('<div class="mp-section-title">Recent Activity Log</div>', unsafe_allow_html=True)
    
    activity_items = []
    if not logs:
        activity_items.append('<div style="text-align:center; padding: 50px; color:#2d3436; font-weight:600;">No recent activity found.</div>')
    else:
        for log in logs:
            g_type = log.get("game_type", "")
            g_name = "실루엣 퀴즈" if g_type == "silhouette" else "메모리 게임"
            is_correct = log.get("is_correct")
            tag_cls = "mp-tag-ok" if is_correct else "mp-tag-fail"
            tag_txt = "SUCCESS" if is_correct else "FAILED"
            # 포켓몬 이름 결정 (이름이 없으면 ID로 표시하여 Unknown 방지)
            p_name = log.get("pokemon_name")
            if not p_name:
                p_id = log.get("pokemon_id")
                p_name = f"No. {p_id}" if p_id else "Unknown"
            
            g_icon = "QUIZ" if g_type == "silhouette" else "MEM"
            
            ts = log.get("created_at", "")
            time_str = ""
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    time_str = dt.strftime("%m/%d %H:%M")
                except: pass

            item_html = (
                f'<div class="mp-log-item">'
                f'<div class="mp-log-icon">{g_icon}</div>'
                f'<div style="flex: 1;">'
                f'<div class="mp-log-main">{g_name} <span class="mp-tag {tag_cls}">{tag_txt}</span></div>'
                f'<div class="mp-log-sub">대상 포켓몬: {p_name}</div>'
                f'</div>'
                f'<div style="font-size: 0.8rem; color: #636e72; font-weight:600;">{time_str}</div>'
                f'</div>'
            )
            activity_items.append(item_html)

    activity_content = "".join(activity_items)
    st.markdown(f'<div class="mp-card card-activity">{activity_content}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # mp-wrap

if __name__ == "__main__":
    show()
