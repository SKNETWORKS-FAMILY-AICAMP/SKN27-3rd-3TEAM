import streamlit as st
import os
import requests
from datetime import datetime
import textwrap
from utils.ui import inject_common_ui

# --- Configuration ---
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
        resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user_id}/logs?limit=5", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

def get_mypage_styles():
    return textwrap.dedent("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Inter:wght@300;400;600;700&display=swap');
    
    :root {
        --neon-blue: #00d2ff;
        --neon-yellow: #ffcb05;
        --neon-green: #4ade80;
        --glass-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    .stApp { background-color: #050505 !important; }
    
    .mypage-container {
        padding: 100px 5% 60px;
        background: #050505;
        min-height: 100vh;
        position: relative;
        overflow: hidden;
    }

    /* Pokedex Scanline & Grid Effect */
    .mypage-container::after {
        content: ''; position: absolute; inset: 0;
        background: 
            linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%),
            linear-gradient(90deg, rgba(255, 0, 0, 0.02), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.02));
        background-size: 100% 4px, 3px 100%;
        pointer-events: none;
        z-index: 1;
    }
    
    /* Profile Section */
    .profile-hero {
        position: relative;
        z-index: 10;
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 40px;
        padding: 60px;
        margin-bottom: 50px;
        display: flex;
        align-items: center;
        gap: 50px;
        box-shadow: 0 40px 100px rgba(0,0,0,0.5);
    }
    
    .profile-avatar-wrap {
        position: relative;
    }

    .profile-avatar {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        border: 4px solid var(--neon-blue);
        box-shadow: 0 0 30px rgba(0, 210, 255, 0.3);
        object-fit: cover;
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float { 
        0%, 100% { transform: translateY(0); } 
        50% { transform: translateY(-20px); } 
    }

    .profile-info h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        margin: 0;
        font-size: clamp(2rem, 5vw, 3.5rem);
        color: #fff;
        letter-spacing: -2px;
        text-shadow: 0 0 20px rgba(255,255,255,0.2);
    }
    
    .profile-info p {
        margin: 10px 0 0;
        color: rgba(255,255,255,0.5);
        font-size: 1.2rem;
        font-weight: 300;
    }
    
    .tier-badge {
        display: inline-block;
        padding: 8px 24px;
        background: var(--neon-yellow);
        color: #000;
        border-radius: 50px;
        font-weight: 900;
        font-size: 0.9rem;
        margin-top: 25px;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 10px 25px rgba(255, 203, 5, 0.3);
    }
    
    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
        margin-bottom: 50px;
        position: relative;
        z-index: 10;
    }
    
    .stat-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        padding: 40px;
        border: 1px solid var(--glass-border);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .stat-card:hover {
        transform: translateY(-10px) scale(1.02);
        background: rgba(255,255,255,0.06);
        border-color: var(--neon-blue);
        box-shadow: 0 20px 50px rgba(0,0,0,0.5), 0 0 20px rgba(0, 210, 255, 0.1);
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.4);
        font-weight: 700;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .stat-value {
        font-family: 'Outfit', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        color: #fff;
        line-height: 1;
    }
    
    .stat-desc {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.3);
        margin-top: 10px;
    }
    
    /* Activity List */
    .activity-section {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border-radius: 40px;
        padding: 50px;
        border: 1px solid var(--glass-border);
        position: relative;
        z-index: 10;
    }
    
    .section-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        font-size: 2rem;
        margin-bottom: 40px;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    .activity-item {
        display: flex;
        align-items: center;
        padding: 25px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }
    
    .activity-item:hover {
        background: rgba(255,255,255,0.02);
        padding-left: 15px;
        padding-right: 15px;
    }
    
    .activity-icon {
        width: 54px;
        height: 54px;
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 25px;
        font-size: 1.5rem;
    }
    
    .activity-main {
        font-weight: 700;
        color: #fff;
        font-size: 1.1rem;
    }
    
    .activity-sub {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.4);
    }
    
    .activity-time {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.2);
    }
    
    .status-tag {
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: 900;
        margin-left: 15px;
        text-transform: uppercase;
    }
    
    .status-success { background: rgba(74, 222, 128, 0.1); color: var(--neon-green); border: 1px solid rgba(74, 222, 128, 0.2); }
    .status-fail { background: rgba(248, 113, 113, 0.1); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.2); }

    @media (max-width: 768px) {
        .profile-hero { flex-direction: column; text-align: center; padding: 40px; }
        .profile-avatar { width: 140px; height: 140px; }
    }
    </style>
    """)

def fetch_github_details(username):
    stats = {"repos": 0, "followers": 0, "commits": 0, "stars": 0}
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Pokemon-Trainer-App"
    }
    try:
        # 1. 기본 정보 (Repos, Followers)
        user_resp = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=5)
        if user_resp.status_code == 200:
            data = user_resp.json()
            stats["repos"] = data.get("public_repos", 0)
            stats["followers"] = data.get("followers", 0)
            
        # 2. 전체 커밋 수 (Search API 사용)
        # Search API는 별도의 preview header가 필요할 수 있음
        search_headers = headers.copy()
        search_headers["Accept"] = "application/vnd.github.cloak-preview+json"
        search_url = f"https://api.github.com/search/commits?q=author:{username}"
        search_resp = requests.get(search_url, headers=search_headers, timeout=5)
        if search_resp.status_code == 200:
            stats["commits"] = search_resp.json().get("total_count", 0)
            
        # 3. 전체 받은 스타(Stars) 수 계산
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
        repos_resp = requests.get(repos_url, headers=headers, timeout=5)
        if repos_resp.status_code == 200:
            repos_data = repos_resp.json()
            stats["stars"] = sum(r.get("stargazers_count", 0) for r in repos_data)
            
    except:
        pass
    return stats

def show():
    inject_common_ui(spacer=False)
    
    if "user" not in st.session_state:
        st.warning("로그인이 필요한 페이지입니다.")
        st.button("로그인 하러 가기", on_click=lambda: st.switch_page("pages/login.py"))
        return

    user = st.session_state.user
    user_id = user.get("id") or user.get("db_id")
    username = user.get("login")
    
    # 1. 세션에 이미 스탯이 있는지 확인 (우선순위 1)
    repos = user.get("public_repos", 0)
    commits = user.get("total_commits", 0)
    stars = user.get("total_stars", 0)
    followers = user.get("followers", 0)
    
    # 2. 데이터가 부족하면 API 호출 (우선순위 2)
    gh = None
    if repos == 0 and commits == 0:
        gh = fetch_github_details(username) if username else None
        if gh:
            repos = gh["repos"]
            commits = gh["commits"]
            stars = gh["stars"]
            followers = gh["followers"]
    
    # Fetch data (Pokemon Game Stats)
    stats = fetch_user_stats(user_id) if user_id else None
    logs = fetch_user_logs(user_id) if user_id else []
    
    st.markdown(get_mypage_styles(), unsafe_allow_html=True)
    
    # Layout Start
    st.markdown('<div class="mypage-container">', unsafe_allow_html=True)
    
    # 1. Profile Hero Section
    avatar = user.get("avatar_url", "https://cdn-icons-png.flaticon.com/512/1144/1144760.png")
    name = user.get("name") or user.get("login", "트레이너")
    
    # GitHub 기반 등급 결정 (전체 커밋과 레포 기준)
    if commits > 1000 or repos > 100: trainer_tier = "Legendary Developer"
    elif commits > 300 or repos > 30: trainer_tier = "Veteran Developer"
    elif commits > 50: trainer_tier = "Active Developer"
    else: trainer_tier = "Rookie Developer"
        
    st.markdown(f"""
    <div class="profile-hero">
        <div class="profile-avatar-wrap">
            <img src="{avatar}" class="profile-avatar">
        </div>
        <div class="profile-info">
            <h1>{name}</h1>
            <p>@{username} · Professional Pokemon Trainer</p>
            <div class="tier-badge">{trainer_tier}</div>
            <div style="margin-top: 15px; color: var(--neon-blue); font-weight: 900; font-family: 'Outfit';">Lv.{min(99, int(commits/10) + 1)} Master</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Stats Grid
    s_total = 0
    s_correct = 0
    m_total = 0
    m_correct = 0
    
    if stats:
        s_total = stats.get("silhouette", {}).get("total", 0)
        s_correct = stats.get("silhouette", {}).get("correct", 0)
        m_total = stats.get("memory", {}).get("total", 0)
        m_correct = stats.get("memory", {}).get("correct", 0)
        
    s_rate = int((s_correct / s_total * 100)) if s_total > 0 else 0
    m_rate = int((m_correct / m_total * 100)) if m_total > 0 else 0
    
    # 통합 점수 계산 (게임 점수 + 깃허브 전체 점수)
    game_score = (s_correct + m_correct) * 10
    # GitHub 전체 점수: Repo(100) + Followers(20) + Total Commits(10) + Total Stars(50)
    gh_score = (repos * 100) + (followers * 20) + (commits * 10) + (stars * 50)
    total_score = game_score + gh_score
    
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">💻 Lifetime Commits</div>
            <div class="stat-value" style="color: var(--neon-blue);">{commits:,}</div>
            <div class="stat-desc">Total public contributions</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">⭐ Reputation</div>
            <div class="stat-value" style="color: var(--neon-yellow);">{stars}</div>
            <div class="stat-desc">Total stars from {repos} repos</div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-color: rgba(255,255,255,0.2);">
            <div class="stat-label" style="color: rgba(255,255,255,0.6);">🏆 Total Trainer Score</div>
            <div class="stat-value" style="color: #fff; text-shadow: 0 0 20px rgba(255,255,255,0.3);">{total_score:,}</div>
            <div class="stat-desc" style="color: rgba(255,255,255,0.4);">Game {game_score:,} + Dev {gh_score:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Activity Timeline
    st.markdown('<div class="activity-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🕒 Recent Activities</div>', unsafe_allow_html=True)
    
    if not logs:
        st.markdown('<p style="color: rgba(255,255,255,0.2); text-align: center; padding: 40px 0;">No activities recorded yet. Play a mini-game!</p>', unsafe_allow_html=True)
    else:
        for log in logs:
            g_type = "Silhouette Quiz" if log.get("game_type") == "silhouette" else "Memory Game"
            is_correct = log.get("is_correct")
            status_text = "SUCCESS" if is_correct else "FAIL"
            status_class = "status-success" if is_correct else "status-fail"
            
            # Format time
            ts = log.get("created_at")
            time_str = ""
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    time_str = dt.strftime("%m/%d %H:%M")
                except: pass
                
            icon = "🔍" if log.get("game_type") == "silhouette" else "🧠"
            
            st.markdown(f"""
            <div class="activity-item">
                <div class="activity-icon">{icon}</div>
                <div class="activity-details">
                    <div class="activity-main">
                        Played {g_type}
                        <span class="status-tag {status_class}">{status_text}</span>
                    </div>
                    <div class="activity-sub">Gained trainer points</div>
                </div>
                <div class="activity-time">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True) # End Activity Section
    st.markdown('</div>', unsafe_allow_html=True) # End Container

if __name__ == "__main__":
    show()
