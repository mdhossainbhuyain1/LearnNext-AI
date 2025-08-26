import streamlit as st
from core.utils import inject_css, record_event
from modules.qa import academic_qa
from core.sidebar import render_sidebar
render_sidebar("Academic Q&A")

st.set_page_config(page_title="Academic Q&A", page_icon="📚", layout="wide")
inject_css()

# --------------------------------------------
# Stylish header
# --------------------------------------------
st.markdown("""
<div class="card pop" style="padding:22px;
  background: linear-gradient(135deg, rgba(15,26,48,.95) 0%, rgba(11,18,32,.95) 60%, rgba(0,194,209,.18) 120%);
  border:1px solid rgba(0,194,209,.35);">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;">
    <div>
      <div class="app-title" style="margin-bottom:6px;">Academic Q&A</div>
      <div class="subtle">Ask clear questions. Get concise, concept-focused answers.</div>
    </div>
    <div style="min-width:240px;height:88px;border-radius:16px;
                background: radial-gradient(70px 70px at 80% 40%, rgba(0,194,209,.55), transparent 60%),
                            linear-gradient(135deg,#0b1220 0%,#0f1a30 60%,rgba(0,194,209,.65) 135%);
                box-shadow:0 10px 28px rgba(0,0,0,.35);">
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------
# Domain + presets
# --------------------------------------------
PRESETS = {
    "general": [
        "Summarize the key differences between correlation and causation with examples.",
        "How do I structure a strong literature review chapter?",
        "Explain Bloom’s taxonomy and how to apply it while studying."
    ],
    "math": [
        "Explain backpropagation in simple terms with a tiny numeric example.",
        "What’s the difference between eigenvalues and singular values?",
        "How does gradient descent differ from Newton’s method?"
    ],
    "cs": [
        "Explain time complexity vs space complexity with examples.",
        "What is normalization in databases? Show a quick example.",
        "How do hash tables handle collisions? Compare methods."
    ],
    "biology": [
        "Explain CRISPR-Cas9 editing in simple steps.",
        "Innate vs adaptive immunity—compare with examples.",
        "How do vaccines generate immunological memory?"
    ],
    "economics": [
        "Explain price elasticity of demand with a quick example.",
        "Key differences between monetary and fiscal policy?",
        "What is comparative advantage? Give a simple scenario."
    ],
    "history": [
        "What were the core causes of World War I in brief?",
        "Compare Enlightenment thinkers: Locke vs Rousseau.",
        "How did the Industrial Revolution change labor?"
    ],
}

st.markdown("#### Pick a domain")
domain = st.segmented_control(
    "Choose a subject area", list(PRESETS.keys()), selection_mode="single", default="general", key="qna_domain"
)

st.markdown("#### Quick questions (click to run)")
presets = PRESETS.get(domain, [])
cols = st.columns(3)
clicked = None
for i, qtext in enumerate(presets):
    if cols[i % 3].button(qtext, key=f"preset_{domain}_{i}", use_container_width=True):
        clicked = qtext

# --------------------------------------------
# Answer logic for preset click
# --------------------------------------------
if clicked:
    with st.spinner("Thinking..."):
        ans = academic_qa(clicked.strip(), domain)
    st.session_state["qna_last_q"] = clicked.strip()
    st.session_state["qna_last_domain"] = domain
    st.session_state["qna_last_ans"] = ans
    record_event("qna", {"question": clicked[:120], "domain": domain})

# --------------------------------------------
# Manual question form (kept for freeform queries)
# --------------------------------------------
st.markdown("---")
st.markdown("#### Or ask your own question")

# UI controls below the textarea to enrich prompts without changing your backend module
colx, coly = st.columns([3, 1.2])
with colx:
    q = st.text_area(
        "Your question",
        key="qna_input",
        height=160,
        placeholder="e.g., Explain backpropagation in simple terms.",
    )
with coly:
    depth = st.selectbox("Answer length", ["Concise", "Standard", "Detailed"], index=1)
    focus = st.selectbox("Focus", ["Key points", "Step-by-step", "Examples first"], index=0)

go = st.button("Get Answer", type="primary", use_container_width=True)

if go:
    if not q.strip():
        st.warning("Please enter a question.")
    else:
        # Light-touch prompt shaping without changing your backend
        extra = {
            "Concise": "Keep the answer within 6-9 sentences.",
            "Standard": "Aim for clear depth with bullet points where useful.",
            "Detailed": "Include step-by-step reasoning and relevant examples.",
        }[depth]
        extra2 = {
            "Key points": "Prioritize key points and definitions.",
            "Step-by-step": "Present the reasoning as steps.",
            "Examples first": "Start with 1-2 short examples, then explain theory.",
        }[focus]

        prompt = f"{q.strip()}\n\nGuidance: {extra} {extra2}"
        with st.spinner("Thinking..."):
            ans = academic_qa(prompt, domain)
        st.session_state["qna_last_q"] = q.strip()
        st.session_state["qna_last_domain"] = domain
        st.session_state["qna_last_ans"] = ans
        record_event("qna", {"question": q[:120], "domain": domain})

# --------------------------------------------
# Display answer (if any)
# --------------------------------------------
if "qna_last_ans" in st.session_state:
    st.markdown("---")
    st.markdown("### Answer")
    st.markdown(f"""
    <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
      <div class="subtle" style="margin-bottom:6px">
        Asked: <b>{st.session_state.get("qna_last_q","")}</b> · Domain: <b>{st.session_state.get("qna_last_domain","")}</b>
      </div>
      <div style="line-height:1.6">{st.session_state["qna_last_ans"]}</div>
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        "Download answer (.txt)",
        data=st.session_state["qna_last_ans"],
        file_name="learnnext_qna_answer.txt",
        mime="text/plain",
        use_container_width=True
    )

# --------------------------------------------
# Minimal history (last 5)
# --------------------------------------------
if "qna_history" not in st.session_state:
    st.session_state["qna_history"] = []

if "qna_last_q" in st.session_state and "qna_last_ans" in st.session_state:
    pair = (st.session_state["qna_last_q"], st.session_state["qna_last_domain"], st.session_state["qna_last_ans"])
    if not st.session_state["qna_history"] or st.session_state["qna_history"][-1][0] != pair[0]:
        st.session_state["qna_history"].append(pair)
        st.session_state["qna_history"] = st.session_state["qna_history"][-5:]  # keep last 5

if st.session_state["qna_history"]:
    st.markdown("---")
    st.markdown("#### Recent questions")
    for i, (qq, dd, aa) in enumerate(reversed(st.session_state["qna_history"]), 1):
        with st.expander(f"{i}. {qq}  ·  ({dd})"):
            st.write(aa)

# --------------------------------------------
# Tiny tip
# --------------------------------------------
st.caption("Tip: Click a suggested question for a 1-click answer, or craft your own with the options above.")
