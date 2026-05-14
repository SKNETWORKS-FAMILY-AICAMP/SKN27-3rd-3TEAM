import os
import base64
import json
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor

_FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROOT_DIR = os.path.dirname(_FRONTEND_DIR)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@st.cache_data
def get_pokemon_names():
    try:
        path = os.path.join(_ROOT_DIR, "database", "common", "data", "processed", "pokemon.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {str(p["id"]): p["name"] for p in data}
    except Exception:
        pass
    return {}


def _b64_img(rel_path: str) -> str:
    full = os.path.join(_FRONTEND_DIR, rel_path)
    if os.path.exists(full):
        with open(full, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""


def fetch_user_stats(user_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user_id}/stats", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def fetch_user_logs(user_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/users/{user_id}/logs?limit=8", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def fetch_team_history(user_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/team-builder/history/{user_id}?limit=6", timeout=8)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def fetch_chatbot_sessions(user_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/chatbot/sessions?user_id={user_id}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def fetch_github_details(username):
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "Pokemon-Trainer-App"}

    def fetch_user():
        try:
            r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=5)
            if r.status_code == 200:
                d = r.json()
                return d.get("public_repos", 0), d.get("followers", 0)
        except Exception:
            pass
        return 0, 0

    def fetch_commits():
        try:
            h = {**headers, "Accept": "application/vnd.github.cloak-preview+json"}
            r = requests.get(f"https://api.github.com/search/commits?q=author:{username}", headers=h, timeout=5)
            if r.status_code == 200:
                return r.json().get("total_count", 0)
        except Exception:
            pass
        return 0

    def fetch_stars():
        try:
            r = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100", headers=headers, timeout=5)
            if r.status_code == 200:
                return sum(repo.get("stargazers_count", 0) for repo in r.json())
        except Exception:
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
