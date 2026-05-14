import os
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080")


def _get(path, params=None):
    return requests.get(f"{BACKEND_URL}{path}", params=params, timeout=10)


def _post(path, **kwargs):
    return requests.post(f"{BACKEND_URL}{path}", timeout=180, **kwargs)


def _delete(path):
    return requests.delete(f"{BACKEND_URL}{path}", timeout=10)


def _patch(path, **kwargs):
    return requests.patch(f"{BACKEND_URL}{path}", timeout=10, **kwargs)


@st.cache_data(ttl=60)
def fetch_models():
    try:
        data = _get("/api/v1/chatbot/models").json()
        return data["models"], data["default"]
    except Exception:
        return ["gpt-4o-mini"], "gpt-4o-mini"


def api_chat(query, history, model, session_id=None, user_id=None):
    r = _post("/api/v1/chatbot/chat", json={
        "query": query, "history": history,
        "model": model, "session_id": session_id,
        "user_id": user_id,
    })
    r.raise_for_status()
    return r.json()


def api_sessions(user_id=None):
    try:
        params = {"user_id": user_id} if user_id else {}
        return _get("/api/v1/chatbot/sessions", params=params).json()
    except Exception:
        return []


def api_messages(session_id):
    try:
        return _get(f"/api/v1/chatbot/sessions/{session_id}/messages").json()
    except Exception:
        return []


def api_delete_session(session_id):
    try:
        _delete(f"/api/v1/chatbot/sessions/{session_id}")
    except Exception:
        pass


def api_rename_session(session_id, title):
    try:
        _patch(f"/api/v1/chatbot/sessions/{session_id}", params={"title": title})
    except Exception:
        pass
