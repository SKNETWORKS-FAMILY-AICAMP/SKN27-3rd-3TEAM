import os
import base64
import html as _html
import streamlit as st

from chatbot.constants import _TOOL_COLORS, _TOOL_LABELS


def get_base64_img(file_name: str) -> str:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_path, "img", "chatbot", file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""


def render_tool_badges(tools: list) -> None:
    if not tools:
        return
    badges = []
    for t in tools:
        color, bg = _TOOL_COLORS.get(t, ("#64748b", "rgba(100,116,139,0.15)"))
        label = _TOOL_LABELS.get(t, t)
        badges.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'background:{bg};color:{color};border:1px solid {color}55;'
            f'border-radius:20px;padding:3px 10px;font-size:11px;font-weight:700;'
            f'letter-spacing:0.3px;margin-right:4px;">⚙ {label}</span>'
        )
    st.markdown(
        '<div style="margin-top:8px;line-height:2.2;">' + "".join(badges) + "</div>",
        unsafe_allow_html=True,
    )


def render_user_bubble(content: str, avatar_url: str) -> None:
    escaped = _html.escape(content)
    st.markdown(
        f'<div style="display:flex;justify-content:flex-end;align-items:flex-start;'
        f'gap:12px;padding:8px 16px;margin-bottom:8px;">'
        f'<div style="background:linear-gradient(135deg,#EE1515 0%,#c0392b 100%);'
        f'color:#fff;padding:12px 16px;border-radius:18px 4px 18px 18px;'
        f'font-size:14.5px;line-height:1.75;font-family:Inter,sans-serif;'
        f'box-shadow:0 4px 14px rgba(238,21,21,0.22);word-break:break-word;'
        f'white-space:pre-wrap;max-width:80%;">{escaped}</div>'
        f'<img src="{avatar_url}" style="width:48px;height:48px;border-radius:50%;'
        f'flex-shrink:0;object-fit:cover;border:2px solid #e2e8f0;"></div>',
        unsafe_allow_html=True,
    )


def render_assistant_bubble(content: str, avatar_url: str, used_tools: list = None) -> None:
    tool_html = ""
    if used_tools:
        from chatbot.constants import _TOOL_LABELS
        
        ref_items = []
        for t in used_tools:
            label = _TOOL_LABELS.get(t, t)
            # Make it look like a reference block
            ref_items.append(f'<div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">▪️ {label} ({t})</div>')
            
        tool_html = (
            f'<div style="margin-top: 16px; padding-top: 12px; border-top: 1px dashed #cbd5e1;">'
            f'<div style="font-size: 12px; font-weight: 800; color: #94a3b8; margin-bottom: 8px;">REFERENCES</div>'
            f'{"".join(ref_items)}'
            f'</div>'
        )

    st.markdown(
        f'<div style="display:flex;justify-content:flex-start;align-items:flex-start;'
        f'gap:12px;padding:12px 16px;margin-bottom:24px;overflow:visible;">'
        f'<img src="{avatar_url}" style="width:48px;height:48px;border-radius:50%;'
        f'flex-shrink:0;object-fit:contain;border:2px solid #e2e8f0;background:#fff;">'
        f'<div style="flex:1;max-width:85%;">'
        f'<div style="background:#f8fafc;color:#1e293b;padding:16px 20px;'
        f'border-radius:4px 22px 22px 22px;font-size:14.5px;line-height:1.6;'
        f'font-family:Inter,sans-serif;border:1px solid #e2e8f0;'
        f'box-shadow:0 2px 10px rgba(0,0,0,0.03);">{content}{tool_html}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
