import streamlit as st
import pandas as pd
import plotly.express as px
from core.sidebar import render_sidebar
render_sidebar("Wellness")

from core.utils import inject_css, record_event
from modules.wellness import wellness_analysis, DISCLAIMER

st.set_page_config(page_title="Wellness", page_icon="💙", layout="wide")
inject_css()

# ------------------------- Header -------------------------
st.markdown("""
<div class="card pop" style="padding:22px;
  background: linear-gradient(135deg, rgba(15,26,48,.95) 0%, rgba(11,18,32,.95) 60%, rgba(0,194,209,.18) 120%);
  border:1px solid rgba(0,194,209,.35);">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;">
    <div>
      <div class="app-title" style="margin-bottom:6px;">Student Wellness</div>
      <div class="subtle">Quick emotional check-in with supportive, practical tips.</div>
    </div>
    <div style="min-width:240px;height:88px;border-radius:16px;
                background: radial-gradient(70px 70px at 80% 40%, rgba(0,194,209,.55), transparent 60%),
                            linear-gradient(135deg,#0b1220 0%,#0f1a30 60%,rgba(0,194,209,.65) 135%);
                box-shadow:0 10px 28px rgba(0,0,0,.35);">
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.caption(DISCLAIMER)

# ------------------------- Presets -------------------------
PRESETS = [
    "I'm anxious about upcoming exams and can't focus.",
    "Feeling low and unmotivated after a tough week.",
    "Overwhelmed with workload and deadlines.",
    "Frustrated by coding bugs that I can't fix.",
    "I'm okay—just want to stay consistent and positive.",
]
st.markdown("#### One-tap feelings (click to analyze)")
cols = st.columns(5)
preset_clicked = None
for i, text in enumerate(PRESETS):
    if cols[i].button(text, key=f"w_preset_{i}", use_container_width=True):
        preset_clicked = text

st.markdown("---")

# Keep last text in session so presets fill the textarea
if "well_text" not in st.session_state:
    st.session_state.well_text = ""

st.session_state.well_text = preset_clicked or st.session_state.well_text

# ------------------------- Input -------------------------
st.markdown("#### Tell me how you feel")
text = st.text_area(
    "Describe in 2–3 sentences",
    value=st.session_state.well_text,
    height=140,
    placeholder="e.g., I'm stressed about exams and worried I'll forget everything during the test…"
)

# ------------------------- Analyze -------------------------
run_analysis = st.button("Analyze", type="primary", use_container_width=True) or (preset_clicked is not None)

def pill(label: str):
    st.markdown(f"""<span class="pill" style="margin:4px 8px 0 0;display:inline-block">{label}</span>""",
                unsafe_allow_html=True)

if run_analysis:
    if not (preset_clicked or text.strip()):
        st.warning("Please share a brief note or tap a preset above.")
    else:
        use_text = preset_clicked or text.strip()
        with st.spinner("Analyzing…"):
            out = wellness_analysis(use_text)

        # Save the text for next time
        st.session_state.well_text = use_text

        # ---------------- Summary chips ----------------
        st.markdown("### Snapshot")
        c1, c2, c3 = st.columns(3)
        # Top sentiment
        sent = out.get("sentiment", {})
        if sent:
            top_sent, top_score = max(sent.items(), key=lambda kv: kv[1])
            with c1:
                pill(f"Sentiment: {top_sent.title()} ({top_score:.2f})")
        # Top emotion
        emo = out.get("emotions", {})
        if emo:
            top_emo, top_emo_score = max(emo.items(), key=lambda kv: kv[1])
            with c2:
                pill(f"Top emotion: {top_emo.title()} ({top_emo_score:.2f})")
        with c3:
            pill(f"Text length: {len(use_text.split())} words")

        # ---------------- Emotions chart ----------------
        st.markdown("### Emotions")
        if emo:
            df = pd.DataFrame(sorted(emo.items(), key=lambda kv: kv[1], reverse=True)[:10],
                              columns=["emotion", "score"])
            fig = px.bar(df, x="emotion", y="score", text="score", range_y=[0, 1])
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No emotions detected. Try writing 2–3 sentences with a bit more detail.")

        # ---------------- Sentiment raw (optional) ----------------
        with st.expander("View raw sentiment scores"):
            st.json(sent)

        # ---------------- Tips ----------------
        st.markdown("### Micro-actions for the next hour")
        tips = out.get("tips", [])
        if tips:
            for t in tips:
                st.markdown(f"- {t}")
        else:
            st.caption("No tips available for this input.")

        # ---------------- Download mini-report ----------------
        st.markdown("---")
        report = []
        if sent:
            report.append(f"Sentiment: {top_sent} ({top_score:.2f})")
        if emo:
            report.append(f"Top emotion: {top_emo} ({top_emo_score:.2f})")
            topk = ", ".join([f"{k}:{v:.2f}" for k, v in sorted(emo.items(), key=lambda kv: kv[1], reverse=True)[:5]])
            report.append(f"Emotions (top 5): {topk}")
        if tips:
            report.append("Tips:")
            for t in tips:
                report.append(f" - {t}")
        report_text = f"Input:\n{use_text}\n\n" + "\n".join(report) + "\n"
        st.download_button("Download wellness report (.txt)", report_text, file_name="wellness_report.txt",
                           mime="text/plain", use_container_width=True)

        record_event("wellness", {"len": len(use_text)})
        st.balloons()

# ---------------- Tiny Coach (optional guidance) ----------------
with st.expander("What this page does"):
    st.markdown("""
- Detects **sentiment** and **emotions** from your note (Hugging Face Inference API).
- Shows a simple **emotions chart** and gives **micro-actions** you can try now.
- Nothing is stored permanently by default; the metric counters you see in the app are session-level analytics for your dashboard.
""")
