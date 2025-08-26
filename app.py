# app.py — LearnNext AI (Landing + Integrated Dashboard)

import json
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from core.config import PALETTE
from core.utils import inject_css, get_usage_counts

# 👉 IMPORTANT: set page + inject CSS BEFORE rendering your custom sidebar
st.set_page_config(page_title="LearnNext AI", page_icon="🎓", layout="wide")
inject_css()

from core.sidebar import render_sidebar
render_sidebar("Home")

# ---------- HERO ----------
st.markdown(
    f"""
<div class="card pop" style="
  padding:28px;
  border-radius:20px;
  background:
    linear-gradient(135deg, rgba(12,19,33,.96) 0%, rgba(12,19,33,.92) 55%, {PALETTE['accent']}1a 100%),
    radial-gradient(220px 120px at 90% 10%, {PALETTE['accent']}33, transparent 60%);
  border:1px solid {PALETTE['accent']}33;">
  <div style="display:flex;gap:22px;align-items:center;justify-content:space-between;flex-wrap:wrap">
    <div style="min-width:280px;flex:1">
      <div class="app-title" style="margin-bottom:8px;">LearnNext AI</div>
      <div class="subtle" style="opacity:.9">AI-Powered Personalized Learning and Coding Assistance Platform</div>
      <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">
        <span class="pill">Personalized Learning</span>
        <span class="pill">Academic Q&amp;A</span>
        <span class="pill">Lecture Summaries</span>
        <span class="pill">Coding Mentor</span>
        <span class="pill">Wellness</span>
        <span class="pill">Quizzes</span>
      </div>
    </div>
    <div style="
      min-width:260px;height:120px;border-radius:18px;flex:0 0 260px;
      background:linear-gradient(180deg, {PALETTE['accent']}55, transparent 70%) ,
                 radial-gradient(80% 140% at 100% -20%, {PALETTE['accent']}44, #0c1321 40%);
      box-shadow:0 14px 34px rgba(0,0,0,.35);">
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- METRICS ----------
stats, total = get_usage_counts()
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Academic Q&A", stats.get("qna", 0))
k2.metric("Summaries", stats.get("summaries", 0))
k3.metric("Transcripts", stats.get("transcripts", 0))
k4.metric("Coding Mentor", stats.get("coding", 0))
k5.metric("Wellness Checks", stats.get("wellness", 0))
k6.metric("Quizzes Taken", stats.get("quiz", 0))

st.markdown("---")

# ---------- CHARTS ----------
usage_df = pd.DataFrame(
    [
        {"feature": "Academic Q&A", "count": stats.get("qna", 0)},
        {"feature": "Summaries", "count": stats.get("summaries", 0)},
        {"feature": "Transcripts", "count": stats.get("transcripts", 0)},
        {"feature": "Coding", "count": stats.get("coding", 0)},
        {"feature": "Wellness", "count": stats.get("wellness", 0)},
        {"feature": "Quiz", "count": stats.get("quiz", 0)},
    ]
)

def _load_events():
    p = Path("data/analytics.json")
    if not p.exists():
        return []
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = []
    for ts, rec in obj.items():
        try:
            # allow raw unix ts or already-formatted strings
            ts_int = int(ts)
            t = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts_int))
        except Exception:
            t = str(ts)
        rows.append(
            {
                "time": t,
                "event": rec.get("event"),
                "payload": rec.get("payload", {}) or {},
            }
        )
    # sort by parsed datetime fallback to string
    def _key(r):
        try:
            return pd.to_datetime(r["time"])
        except Exception:
            return r["time"]
    return sorted(rows, key=_key)

events = _load_events()
timeline_df = pd.DataFrame(events)

c1, c2 = st.columns([1.3, 1])
with c1:
    st.subheader("Usage by feature")
    fig_bar = px.bar(usage_df, x="feature", y="count", text="count", title=None)
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=None,
        yaxis_title=None,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader("Activity over time")
    if not timeline_df.empty:
        # group by minute; if your app logs faster, adjust here
        agg = (
            timeline_df.assign(dt=pd.to_datetime(timeline_df["time"], errors="coerce"))
            .dropna(subset=["dt"])
            .groupby(pd.Grouper(key="dt", freq="1min"))
            .size()
            .reset_index(name="events")
        )
        if not agg.empty:
            fig_area = px.area(agg, x="dt", y="events", title=None)
            fig_area.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title=None,
                yaxis_title=None,
            )
            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.caption("No timestamped events yet — interact with features to populate this chart.")
    else:
        st.caption("No activity yet — start using features and charts will populate.")

st.markdown("---")

# ---------- FEATURE SHOWCASE ----------
st.subheader("Explore features")

def feature_card(title: str, desc: str, emoji: str):
    st.markdown(
        f"""
    <div class="card pop" style="min-height:164px;transition:transform .2s ease, box-shadow .2s ease;"
         onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 12px 28px rgba(0,0,0,.35)';"
         onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 24px rgba(0,0,0,.25)';">
      <div style="display:flex;align-items:flex-start;gap:10px">
        <div style="font-size:1.6rem;line-height:1">{emoji}</div>
        <div>
          <div style="font-weight:700;font-size:1.05rem;margin-bottom:6px">{title}</div>
          <div class="subtle" style="margin-bottom:6px">{desc}</div>
        </div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# first row
fc1, fc2, fc3 = st.columns(3)
with fc1:
    feature_card(
        "Personalized Learning",
        "4-week plans, micro-habits, and free resources tailored to your goals.",
        "🎯",
    )
with fc2:
    feature_card(
        "Academic Q&A",
        "Ask any course question. Clear, concise, concept-focused answers.",
        "📚",
    )
with fc3:
    feature_card(
        "Lectures & Summarizers",
        "YouTube transcript + fast doc/long-text summarizers on one page.",
        "🎧",
    )

st.markdown("<div style='margin:18px 0'></div>", unsafe_allow_html=True)

# second row
fc4, fc5, fc6 = st.columns(3)
with fc4:
    feature_card(
        "Coding Mentor",
        "Code reviews, debugging tips, and crisp concept explainers.",
        "🧑‍💻",
    )
with fc5:
    feature_card(
        "Wellness",
        "Sentiment & emotions with supportive micro-tips for students.",
        "💙",
    )
with fc6:
    feature_card(
        "Quiz & Flashcards",
        "MCQ quiz with animated feedback and quick flashcards.",
        "🧪",
    )

st.markdown("---")

# ---------- RECENT ACTIVITY TIMELINE ----------
st.subheader("Recent activity")
if not events:
    st.caption("No activity yet — your interactions will appear here in real time.")
else:
    for e in list(reversed(events))[:12]:
        pretty = (
            json.dumps(e.get("payload") or {}, ensure_ascii=False, indent=2)
            if e.get("payload") is not None
            else "{}"
        )
        st.markdown(
            f"""
        <div class="card" style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><b>{e.get('event','event')}</b></div>
            <div class="subtle">{e.get('time','')}</div>
          </div>
          <pre style="
            margin-top:8px;
            background:rgba(255,255,255,0.03);
            border:1px solid {PALETTE['accent']}22;
            border-radius:10px;
            padding:10px;
            overflow:auto;
            white-space:pre-wrap;">{pretty}</pre>
        </div>
        """,
            unsafe_allow_html=True,
        )
