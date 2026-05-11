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
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;600;700&display=swap');
    
    .mypage-container {
        padding: 120px 40px 60px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        min-height: 100vh;
    }
    
    /* Profile Section */
    .profile-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 24px;
        padding: 40px;
        display: flex;
        align-items: center;
        gap: 30px;
        margin-bottom: 40px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.05);
    }
    
    .profile-avatar {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 4px solid #fff;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        object-fit: cover;
    }
    
    .profile-info h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        margin: 0;
        font-size: 2.5rem;
        color: #1a1a1a;
    }
    
    .profile-info p {
        margin: 5px 0 0;
        color: #666;
        font-size: 1.1rem;
    }
    
    .trainer-badge {
        display: inline-block;
        padding: 6px 16px;
        background: #ffcb05;
        color: #2a75bb;
        border-radius: 50px;
        font-weight: 800;
        font-size: 0.8rem;
        margin-top: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 25px;
        margin-bottom: 40px;
    }
    
    .stat-card {
        background: white;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.03);
        transition: transform 0.3s ease;
        border: 1px solid #f0f0f0;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #888;
        font-weight: 600;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .stat-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2rem;
        font-weight: 900;
        color: #1a1a1a;
    }
    
    .stat-desc {
        font-size: 0.85rem;
        color: #aaa;
        margin-top: 5px;
    }
    
    /* Activity List */
    .activity-section {
        background: white;
        border-radius: 24px;
        padding: 35px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.03);
    }
    
    .section-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.5rem;
        margin-bottom: 25px;
        color: #1a1a1a;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .activity-item {
        display: flex;
        align-items: center;
        padding: 15px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    
    .activity-item:last-child {
        border-bottom: none;
    }
    
    .activity-icon {
        width: 45px;
        height: 45px;
        background: #f8f9fa;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
    }
    
    .activity-details {
        flex: 1;
    }
    
    .activity-main {
        font-weight: 700;
        color: #333;
        font-size: 1rem;
    }
    
    .activity-sub {
        font-size: 0.85rem;
        color: #888;
    }
    
    .activity-time {
        font-size: 0.85rem;
        color: #bbb;
    }
    
    .status-tag {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-left: 10px;
    }
    
    .status-success { background: #e6fffa; color: #38b2ac; }
    .status-fail { background: #fff5f5; color: #e53e3e; }
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
    
    # Fetch data
    stats = fetch_user_stats(user_id) if user_id else None
    logs = fetch_user_logs(user_id) if user_id else []
    gh = fetch_github_details(username) if username else None
    
    st.markdown(get_mypage_styles(), unsafe_allow_html=True)
    
    # Layout Start
    st.markdown('<div class="mypage-container">', unsafe_allow_html=True)
    
    # 1. Profile Section
    avatar = user.get("avatar_url", "https://cdn-icons-png.flaticon.com/512/1144/1144760.png")
    name = user.get("name") or user.get("login", "트레이너")
    
    # GitHub 기반 등급 결정 (전체 커밋과 레포 기준)
    repos = gh["repos"]
    commits = gh["commits"]
    if commits > 1000 or repos > 100: trainer_tier = "Legendary Developer"
    elif commits > 300 or repos > 30: trainer_tier = "Veteran Developer"
    elif commits > 50: trainer_tier = "Active Developer"
    else: trainer_tier = "Rookie Developer"
        
    st.markdown(f"""
    <div class="profile-card">
        <img src="{avatar}" class="profile-avatar">
        <div class="profile-info">
            <h1>{name}</h1>
            <p>@{username} · {trainer_tier}</p>
            <div class="trainer-badge" style="background:#4ade80; color:#064e3b;">Lv.{min(99, int(commits/10) + 1)} Developer</div>
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
    gh_score = (repos * 100) + (gh['followers'] * 20) + (commits * 10) + (gh['stars'] * 50)
    total_score = game_score + gh_score
    
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card" style="border-top: 5px solid #2a75bb;">
            <div class="stat-label">💻 전체 커밋 수</div>
            <div class="stat-value">{commits:,}</div>
            <div class="stat-desc">Lifetime Public Commits</div>
        </div>
        <div class="stat-card" style="border-top: 5px solid #ffcb05;">
            <div class="stat-label">⭐ 획득한 스타</div>
            <div class="stat-value">{gh['stars']}</div>
            <div class="stat-desc">Reputation from Repositories</div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white;">
            <div class="stat-label" style="color: rgba(255,255,255,0.8);">🏆 평생 통합 점수</div>
            <div class="stat-value" style="color: white; font-size: 2.5rem;">{total_score:,}</div>
            <div class="stat-desc" style="color: rgba(255,255,255,0.6);">Dev {gh_score:,} + Game {game_score:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Activity Timeline
    st.markdown('<div class="activity-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🕒 최근 활동 내역</div>', unsafe_allow_html=True)
    
    if not logs:
        st.markdown('<p style="color: #888; text-align: center; padding: 40px 0;">아직 활동 기록이 없습니다. 미니게임을 플레이해보세요!</p>', unsafe_allow_html=True)
    else:
        for log in logs:
            g_type = "실루엣 퀴즈" if log.get("game_type") == "silhouette" else "메모리 게임"
            is_correct = log.get("is_correct")
            status_text = "SUCCESS" if is_correct else "FAIL"
            status_class = "status-success" if is_correct else "status-fail"
            
            # Format time
            ts = log.get("created_at")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    time_str = dt.strftime("%m/%d %H:%M")
                except:
                    time_str = ""
            else:
                time_str = ""
                
            icon = "❓" if log.get("game_type") == "silhouette" else "🧠"
            
            st.markdown(f"""
            <div class="activity-item">
                <div class="activity-icon">{icon}</div>
                <div class="activity-details">
                    <div class="activity-main">
                        {g_type} 플레이
                        <span class="status-tag {status_class}">{status_text}</span>
                    </div>
                    <div class="activity-sub">활동 점수 획득</div>
                </div>
                <div class="activity-time">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True) # End Activity Section
    st.markdown('</div>', unsafe_allow_html=True) # End Container

if __name__ == "__main__":
    show()
