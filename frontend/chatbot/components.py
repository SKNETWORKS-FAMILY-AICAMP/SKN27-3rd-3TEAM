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
        f'<div style="display:flex;justify-content:flex-end;align-items:flex-end;'
        f'gap:12px;padding:4px 8px;margin-bottom:16px;">'
        f'<div style="background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%);'
        f'color:#ffffff;padding:14px 20px;border-radius:24px 24px 4px 24px;'
        f'font-size:15px;line-height:1.6;font-family:\'Pretendard\', \'Inter\', sans-serif;'
        f'box-shadow:0 4px 15px rgba(255, 65, 108, 0.25);word-break:break-word;'
        f'white-space:pre-wrap;max-width:75%;font-weight:500;">{escaped}</div>'
        f'<img src="{avatar_url}" style="width:40px;height:40px;border-radius:50%;'
        f'flex-shrink:0;object-fit:cover;border:2px solid #ffffff;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.1);"></div>',
        unsafe_allow_html=True,
    )


def render_assistant_bubble(content: str, avatar_url: str, used_tools: list = None) -> None:
    tool_html = ""
    if used_tools:
        from chatbot.constants import _TOOL_LABELS
        
        ref_items = []
        for t in used_tools:
            label = _TOOL_LABELS.get(t, t)
            # Modern Badge UI for References
            ref_items.append(
                f'<span style="display:inline-flex;align-items:center;background:#f1f5f9;'
                f'color:#475569;border:1px solid #e2e8f0;border-radius:16px;'
                f'padding:4px 10px;font-size:11.5px;font-weight:600;margin-right:6px;'
                f'margin-bottom:6px;"><span style="margin-right:4px;">🔍</span>{label}</span>'
            )
            
        tool_html = (
            f'<div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid #e2e8f0;">'
            f'<div style="font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing:0.5px;'
            f'margin-bottom: 8px; text-transform:uppercase;">References</div>'
            f'<div style="display:flex;flex-wrap:wrap;">{"".join(ref_items)}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="display:flex;justify-content:flex-start;align-items:flex-end;'
        f'gap:12px;padding:4px 8px;margin-bottom:24px;overflow:visible;">'
        f'<div style="position:relative;">'
        f'<div style="position:absolute;inset:0;background:linear-gradient(to bottom, #e2e8f0, #cbd5e1);'
        f'border-radius:50%;transform:translateY(2px);z-index:0;filter:blur(2px);"></div>'
        f'<img src="{avatar_url}" style="width:44px;height:44px;border-radius:50%;'
        f'flex-shrink:0;object-fit:contain;border:2px solid #ffffff;background:#ffffff;'
        f'position:relative;z-index:1;box-shadow:0 2px 6px rgba(0,0,0,0.06);">'
        f'</div>'
        f'<div style="flex:1;max-width:85%;">'
        f'<div style="background:#ffffff;color:#334155;padding:16px 24px;'
        f'border-radius:24px 24px 24px 4px;font-size:15px;line-height:1.7;'
        f'font-family:\'Pretendard\', \'Inter\', sans-serif;border:1px solid rgba(226, 232, 240, 0.8);'
        f'box-shadow:0 4px 20px rgba(0,0,0,0.04);">{content}{tool_html}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
