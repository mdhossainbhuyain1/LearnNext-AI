# core/sidebar.py
import streamlit as st
from streamlit_option_menu import option_menu
from .utils import get_usage_counts

# Fallback: hide Streamlit's default sidebar page list (inject_css() should do this earlier)
HIDE_DEFAULT_SIDEBAR = """
<style>
  [data-testid="stSidebarNav"] { display: none !important; }
  section[data-testid="stSidebar"] > div { padding-top: 0.5rem; }
</style>
"""

# Central definition so labels, icons, and targets stay in sync
MENU = [
    {"label": "Home",                    "icon": "house",            "target": "app.py"},
    {"label": "Personalized Learning",   "icon": "bullseye",         "target": "pages/2_🎯_Personalized_Learning.py"},
    {"label": "Academic Q&A",            "icon": "book",             "target": "pages/3_📚_Academic_Q&A.py"},
    {"label": "Lectures & Summarizers",  "icon": "headphones",       "target": "pages/4_🎧_Transcription.py"},
    {"label": "Coding Mentor",           "icon": "laptop",           "target": "pages/5_💻_Coding_Mentor.py"},
    {"label": "Wellness",                "icon": "heart",            "target": "pages/6_💙_Wellness.py"},
    {"label": "Quiz & Flashcards",       "icon": "question-circle",  "target": "pages/7_🧪_Quiz_and_Flashcards.py"},
    {"label": "About",                   "icon": "info-circle",      "target": "pages/8_ℹ️_About.py"},
]

LABELS = [m["label"] for m in MENU]
ICONS  = [m["icon"]  for m in MENU]
TARGET = {m["label"]: m["target"] for m in MENU}

# Pretty sidebar header
HEADER_HTML = """
<div style="
  display:flex;align-items:center;gap:10px;
  padding:10px 6px 12px 6px;
  background: linear-gradient(135deg, rgba(15,26,48,.9) 0%, rgba(11,18,32,.9) 65%, rgba(0,194,209,.18) 130%);
  border-radius: 12px;
  border: 1px solid rgba(0,194,209,.35);
  box-shadow: 0 6px 16px rgba(0,0,0,.2);
">
  <div style="font-weight:800;font-size:1.05rem;">LearnNext AI</div>
  <div style="margin-left:auto;font-size:.85rem;opacity:.8">Study copilot</div>
</div>
"""

def render_sidebar(active: str = "Home"):
    """
    Renders a custom sidebar with consistent highlighting and robust switching.
    Pass the exact label for the current page, e.g., render_sidebar("Coding Mentor").
    """
    # Backup hide (primary hide is done early in inject_css())
    st.markdown(HIDE_DEFAULT_SIDEBAR, unsafe_allow_html=True)

    # Guard: ensure valid label
    if active not in LABELS:
        active = "Home"

    # Restore last selection if present (prevents flicker on reruns)
    current = st.session_state.get("_nav_active", active)

    with st.sidebar:
        st.markdown(HEADER_HTML, unsafe_allow_html=True)

        # Tiny live metric (real usage)
        stats, total = get_usage_counts()
        st.caption(f"Total actions: {total}")

        # Default index based on the 'current' (persisted) or 'active' (declared)
        default_index = LABELS.index(current if current in LABELS else active)

        # Stable key avoids rerun resets; styles keep your look
        choice = option_menu(
            menu_title=None,
            options=LABELS,
            icons=ICONS,
            default_index=default_index,
            key="lnx_nav_menu",
            styles={
                "container": {"background-color": "transparent", "padding": "4px 0 0 0"},
                "icon": {"font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "padding": "8px 12px",
                    "border-radius": "10px",
                    "margin": "4px 0",
                },
                "nav-link-selected": {
                    "background-color": "rgba(0,194,209,.20)",
                    "font-weight": "700",
                    "border": "1px solid rgba(0,194,209,.35)"
                },
            }
        )

        # Persist selection
        st.session_state["_nav_active"] = choice

        # Navigate only if changed
        if choice != active:
            target = TARGET.get(choice)
            if target:
                # Streamlit 1.31+ has st.switch_page; older versions may not
                try:
                    st.switch_page(target)
                except Exception:
                    # Fallback: show a link (for very old Streamlit or local dev)
                    st.markdown(f"**Open page:** `{target}`")
