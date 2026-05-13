import streamlit as st
import os
import base64
import math
import requests
import json
from datetime import datetime
from utils.ui import inject_common_ui
from mypage.styles import inject_mypage_styles

_FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT_DIR = os.path.dirname(_FRONTEND_DIR)

@st.cache_data
def get_pokemon_names():
    try:
        path = os.path.join(_ROOT_DIR, "database", "common", "data", "processed", "pokemon.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {str(p["id"]): p["name"] for p in data}
    except:
        pass
    return {}

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




def show():
    st.set_page_config(
        page_title="마이페이지",
        page_icon="https://pokemonkorea.co.kr/img/_con.ico",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 배경 이미지 로드 및 CSS 주입 (최상단 배치로 레이아웃 밀림 방지)
    bg_b64 = _b64_img("img/mypage.png")
    inject_mypage_styles(bg_b64)

    inject_common_ui(spacer=False)

    if "user" not in st.session_state:
        st.warning("로그인이 필요한 페이지입니다.")
        st.button("로그인 하러 가기", on_click=lambda: st.switch_page("pages/login.py"))
        return

    user     = st.session_state.user
    user_id  = user.get("db_id")
    username = user.get("login")
    pkmn_names = get_pokemon_names()

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
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 5px;">
                    <div class="mp-pill mp-pill-yellow">{trainer_tier}</div>
                </div>
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
    
    # ══════════════════════════════════════════
    # 3. Stats Grid & Badge Medallion
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

    # ── Kanto Badge Case ──
    # collected_ids 미리 계산 (배지 미션 체크용)
    if stats and "collected_pokemon_ids" in stats:
        _collected_ids = stats["collected_pokemon_ids"]
    else:
        _collected_ids = sorted(list(set([
            log.get("pokemon_id") for log in logs
            if log.get("is_correct") and log.get("pokemon_id")
        ])))

    KANTO_BADGES = [
        {
            "file": "회색배지.png",   "name": "볼더 배지",
            "gym": "회색시티 · 브록",
            "mission": "트레이너 등록",  "desc": "마이페이지 방문",
            "glow": "#a0aec0",           "unlocked": True,
        },
        {
            "file": "블루배지.png",   "name": "캐스케이드 배지",
            "gym": "하늘색시티 · 미스티",
            "mission": "퀴즈 첫 도전",   "desc": f"실루엣 퀴즈 1회+  ({s_total}회)",
            "glow": "#63b3ed",           "unlocked": s_total >= 1,
        },
        {
            "file": "골드배지.png",   "name": "썬더 배지",
            "gym": "연분홍시티 · 덴류",
            "mission": "번개 개발자",    "desc": f"GitHub 커밋 50+  ({commits}개)",
            "glow": "#f6e05e",           "unlocked": commits >= 50,
        },
        {
            "file": "무지개배지.png", "name": "레인보우 배지",
            "gym": "무지개시티 · 마티스",
            "mission": "도감 컬렉터",    "desc": f"포켓몬 10마리 수집  ({len(_collected_ids)}마리)",
            "glow": "#f687b3",           "unlocked": len(_collected_ids) >= 10,
        },
        {
            "file": "핑크배지.png",   "name": "소울 배지",
            "gym": "셀라돈시티 · 강연",
            "mission": "메모리 마스터",  "desc": f"메모리 게임 5회+  ({m_total}회)",
            "glow": "#ed64a6",           "unlocked": m_total >= 5,
        },
        {
            "file": "진홍색배지.png", "name": "볼케이노 배지",
            "gym": "홍련섬 · 강석",
            "mission": "불꽃 정신",      "desc": f"퀴즈 정답률 70%+  ({s_rate}%)",
            "glow": "#fc8181",           "unlocked": s_rate >= 70,
        },
        {
            "file": "오렌지배지.png", "name": "마쉬 배지",
            "gym": "상록시티 · 사빈나",
            "mission": "레포 빌더",      "desc": f"GitHub 레포 10+  ({repos}개)",
            "glow": "#ed8936",           "unlocked": repos >= 10,
        },
        {
            "file": "그린배지.png",   "name": "어스 배지",
            "gym": "크리스탈 · 라이벌",
            "mission": "챔피언 도전자",  "desc": f"트레이너 Lv.10+  (Lv.{level})",
            "glow": "#68d391",           "unlocked": level >= 10,
        },
    ]

    badge_count = sum(1 for b in KANTO_BADGES if b["unlocked"])
    is_all = badge_count == 8

    slot_parts = []
    for b in KANTO_BADGES:
        b64  = _b64_img(f"img/badge/event/{b['file']}")
        glow = b["glow"]
        if b["unlocked"]:
            slot_parts.append(f'<div class="badge-slot"><div class="badge-circle unlocked" style="box-shadow:0 0 18px {glow}55,0 0 40px {glow}22,inset 0 2px 8px rgba(0,0,0,0.3);border-color:{glow}88;" title="{b["gym"]}"><img src="{b64}" class="badge-img-unlock" alt="{b["name"]}"></div><div class="badge-slot-name done">{b["name"]}</div><div class="badge-slot-mission done">✓ {b["mission"]}</div></div>')
        else:
            slot_parts.append(f'<div class="badge-slot"><div class="badge-circle locked" title="{b["gym"]}"><img src="{b64}" class="badge-img-lock" alt="{b["name"]}"></div><div class="badge-slot-name">{b["name"]}</div><div class="badge-slot-mission">🔒 {b["desc"]}</div></div>')

    slots_html = "".join(slot_parts)
    footer_msg = "🏆 관동 챔피언! 모든 배지를 획득했습니다!" if is_all else f"{badge_count} / 8 배지 획득"

    st.markdown('<div class="mp-section-title">Kanto Badge Case</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="mp-card card-badge" style="padding:0 !important; overflow:hidden; border-radius: 28px; border:none;">
<div class="badge-case" style="border:none; border-radius:0; padding: 40px;">
<div class="badge-case-title">KANTO REGION · BADGE CASE</div>
<div class="badge-case-grid">
{slots_html}
</div>
<div class="badge-case-footer" style="margin-top:30px;">{footer_msg}</div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── Gym Leader Badges (New Section) ──
    gym_badges_owned = stats.get("gym_badges", []) if stats else []
    
    GYM_LEADERS = [
        {"id": "웅이", "glow": "#a0aec0"},
        {"id": "이슬이", "glow": "#63b3ed"},
        {"id": "아이리스", "glow": "#9f7aea"},
        {"id": "민화", "glow": "#68d391"},
        {"id": "풍란", "glow": "#4fd1c5"},
        {"id": "채두", "glow": "#f6ad55"},
        {"id": "순무", "glow": "#fc8181"},
        {"id": "지우", "glow": "#FFCB05"},
    ]

    gym_slot_parts = []
    for g in GYM_LEADERS:
        img_path = f"img/badge/battle/{g['id']}_뱃지.png"
        b64 = _b64_img(img_path)
        glow = g["glow"]
        unlocked = g["id"] in gym_badges_owned
        
        if unlocked:
            html = f'<div class="badge-slot"><div class="badge-circle unlocked" style="box-shadow:0 0 18px {glow}55, 0 0 40px {glow}22; border-color:{glow}88;"><img src="{b64}" class="badge-img-unlock" alt="{g["id"]}"></div><div class="badge-slot-name done">{g["id"]}</div><div class="badge-slot-mission done">CLEARED</div></div>'
        else:
            html = f'<div class="badge-slot"><div class="badge-circle locked" style="opacity: 0.6;"><img src="{b64}" class="badge-img-lock" alt="{g["id"]}"></div><div class="badge-slot-name">{g["id"]}</div><div class="badge-slot-mission">LOCKED</div></div>'
        gym_slot_parts.append(html)

    gym_slots_html = "".join(gym_slot_parts)
    gym_footer = f"🏅 {len(gym_badges_owned)} / {len(GYM_LEADERS)} 관장 제패"

    st.markdown('<div class="mp-section-title">Gym Leader Medals</div>', unsafe_allow_html=True)
    
    final_gym_html = (
        '<div class="mp-card card-badge" style="padding:0 !important; overflow:hidden; border-radius: 28px; border-top: 6px solid #FFCB05;">'
        '<div class="badge-case" style="background: linear-gradient(160deg, #2d3436 0%, #000000 100%); border:none; border-radius:0; padding: 40px;">'
        '<div class="badge-case-title" style="color: #FFCB05;">LEAGUE CHAMPION · GYM BADGES</div>'
        '<div class="badge-case-grid" style="grid-template-columns: repeat(4, 1fr); gap: 30px 10px;">'
        f'{gym_slots_html}'
        '</div>'
        f'<div class="badge-case-footer" style="color: #FFCB05 !important; border-color: #FFCB05; margin-top:30px; background: rgba(255,203,5,0.1);">{gym_footer}</div>'
        '</div></div>'
    )
    st.markdown(final_gym_html, unsafe_allow_html=True)


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
    # 획득한 포켓몬 ID 추출 (stats에서 전체 목록 가져오거나, 없으면 최근 로그에서 추출)
    if stats and "collected_pokemon_ids" in stats:
        collected_ids = stats["collected_pokemon_ids"]
    else:
        collected_ids = sorted(list(set([log.get("pokemon_id") for log in logs if log.get("is_correct") and log.get("pokemon_id")])))
    
    st.markdown('<div class="mp-section-title">My Pokemon Collection</div>', unsafe_allow_html=True)
    
    if not collected_ids:
        st.markdown(f"""<div class="mp-card card-dex" style="text-align:center; padding: 60px;"><div style="font-size: 3rem; margin-bottom: 20px;">🥚</div><div style="font-weight: 800; color: #2d3436; font-size: 1.2rem;">아직 획득한 포켓몬이 없습니다.</div><div style="color: #636e72; margin-top: 10px;">퀴즈를 맞추고 도감을 채워보세요!</div></div>""", unsafe_allow_html=True)
    else:
        # 도감 그리드 생성 (공백 제거하여 코드 블록 오인 방지)
        dex_items = []
        for pid in collected_ids:
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png"
            p_name_k = pkmn_names.get(str(pid), f"No.{pid}")
            dex_items.append(f'<div style="text-align:center; background: rgba(255,255,255,0.4); border-radius: 15px; padding: 10px; border: 1px solid rgba(255,255,255,0.6);"><img src="{img_url}" style="width: 100%; height: auto; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));"><div style="font-size: 0.65rem; font-weight: 800; color: #2d3436; margin-top: 5px;">{p_name_k}</div></div>')
        
        dex_grid = "".join(dex_items)
        
        # 포획률 계산 (전체 1025마리 기준)
        total_pkmn_count = 1025
        collected_count = len(collected_ids)
        capture_rate = (collected_count / total_pkmn_count) * 100
        
        st.markdown(f"""
<div class="mp-card card-dex">
<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 15px;">
{dex_grid}
</div>
<!-- 포획률 정보 섹션 -->
<div style="margin-top: 35px; padding-top: 25px; border-top: 1px solid rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 12px;">
<div>
<div style="font-size: 0.8rem; font-weight: 800; color: #2d3436; opacity: 0.7; margin-bottom: 4px;">COLLECTION RATE</div>
<div style="font-size: 1.8rem; font-weight: 900; color: #27ae60;">{collected_count} <span style="font-size: 1rem; color: #636e72;">/ {total_pkmn_count}</span></div>
</div>
<div style="text-align: right;">
<div style="font-size: 1.8rem; font-weight: 900; color: #27ae60;">{capture_rate:.1f}%</div>
<div style="font-size: 0.75rem; font-weight: 700; color: #636e72;">{total_pkmn_count - collected_count} Left to Complete</div>
</div>
</div>
<div class="mp-xp-track" style="height: 12px; background: rgba(0,0,0,0.05);">
<div class="mp-xp-fill" style="width: {capture_rate}%; background: linear-gradient(90deg, #2ecc71, #27ae60); box-shadow: 0 0 15px rgba(39, 174, 96, 0.4);"></div>
</div>
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
            # 포켓몬 이름 결정 (매핑 데이터 우선 사용)
            p_id = log.get("pokemon_id")
            p_name = pkmn_names.get(str(p_id)) if p_id else log.get("pokemon_name")
            if not p_name:
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
