import os
import requests
import streamlit as st
from urllib.parse import urlencode

BACKEND_URL = os.environ.get("BACKEND_URL") or os.environ.get("BACKEND_API_URL") or "http://localhost:8000"

def get_secret(key, default=None):
    val = os.getenv(key)
    if val: return val
    try:
        if key in st.secrets: return st.secrets[key]
    except: pass
    return default

CLIENT_ID     = get_secret("GITHUB_CLIENT_ID", "")
CLIENT_SECRET = get_secret("GITHUB_CLIENT_SECRET", "")
REDIRECT_URI  = get_secret("GITHUB_REDIRECT_URI", "http://localhost:8501/login")

def get_github_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "user:email",
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

def get_access_token(code):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        if resp.status_code == 200:
            res_data = resp.json()
            if "error" in res_data:
                st.error(f"GitHub 인증 오류: {res_data.get('error_description')}")
                return None
            return res_data.get("access_token")
    except Exception as e:
        st.error(f"네트워크 오류: {str(e)}")
    return None

def get_user_info(token):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"사용자 정보 요청 오류: {str(e)}")
    return None

def fetch_lifetime_stats(user_info):
    from concurrent.futures import ThreadPoolExecutor
    username = user_info.get("login")
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Pokemon-Trainer-App"}

    def fetch_commits():
        try:
            h = {**headers, "Accept": "application/vnd.github.cloak-preview+json"}
            r = requests.get(f"https://api.github.com/search/commits?q=author:{username}", headers=h, timeout=4)
            if r.status_code == 200:
                return r.json().get("total_count", 0)
        except: pass
        return 0

    def fetch_stars():
        try:
            r = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers, timeout=4)
            if r.status_code == 200:
                return sum(repo.get("stargazers_count", 0) for repo in r.json())
        except: pass
        return 0

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_commits = ex.submit(fetch_commits)
        f_stars = ex.submit(fetch_stars)
        total_commits = f_commits.result()
        total_stars = f_stars.result()

    return {
        "public_repos": user_info.get("public_repos", 0),
        "total_commits": total_commits,
        "total_stars": total_stars,
        "followers": user_info.get("followers", 0),
    }

def sync_user_to_db(user_info, gh_stats):
    url = f"{BACKEND_URL}/api/v1/users/"
    payload = {
        "github_id": user_info.get("id"),
        "login": user_info.get("login"),
        "name": user_info.get("name"),
        "avatar_url": user_info.get("avatar_url"),
        "email": user_info.get("email"),
        "public_repos": gh_stats.get("public_repos", 0),
        "total_commits": gh_stats.get("total_commits", 0),
        "total_stars": gh_stats.get("total_stars", 0)
    }
    try:
        resp = requests.post(url, json=payload, timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None
