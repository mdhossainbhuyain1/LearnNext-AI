import streamlit as st
from core.utils import inject_css, record_event
from modules.coding import code_review, debug_help, concept_explain
from core.sidebar import render_sidebar
render_sidebar("Coding Mentor")

st.set_page_config(page_title="Coding Mentor", page_icon="🧑‍💻", layout="wide")
inject_css()

# ------------------------- Header -------------------------
st.markdown("""
<div class="card pop" style="padding:22px;
  background: linear-gradient(135deg, rgba(15,26,48,.95) 0%, rgba(11,18,32,.95) 60%, rgba(0,194,209,.18) 120%);
  border:1px solid rgba(0,194,209,.35);">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;">
    <div>
      <div class="app-title" style="margin-bottom:6px;">Coding Mentor</div>
      <div class="subtle">Code reviews, debugging guidance, and crisp concept explainers — in a clean blue·frozi UI.</div>
    </div>
    <div style="min-width:240px;height:88px;border-radius:16px;
                background: radial-gradient(70px 70px at 80% 40%, rgba(0,194,209,.55), transparent 60%),
                            linear-gradient(135deg,#0b1220 0%,#0f1a30 60%,rgba(0,194,209,.65) 135%);
                box-shadow:0 10px 28px rgba(0,0,0,.35);">
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🧹 Code review", "🛠️ Debug help", "📘 Explain concept"])

# =========================================================
# Tab 1: Code Review
# =========================================================
with tab1:
    st.markdown("#### Quick review modes (click to run on your code)")
    REVIEW_PRESETS = [
        ("Clean code & readability", "Focus on clarity, naming, comments, and structure."),
        ("Performance & complexity", "Identify hotspots and reduce time/space complexity."),
        ("Security & edge cases", "Spot injection risks, unsafe eval, and missing checks."),
        ("Refactor with functions/classes", "Propose modularization with functions/classes."),
        ("Docstrings & type hints", "Add concise docstrings and Python type hints."),
    ]
    cols = st.columns(5)
    review_click = None
    for i, (title, _) in enumerate(REVIEW_PRESETS):
        if cols[i].button(title, key=f"rv_{i}", use_container_width=True):
            review_click = i

    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        lang = st.selectbox("Language", ["python","javascript","java","c++","c","go","rust"], index=0)
    with c2:
        tone = st.selectbox("Tone", ["Pragmatic", "Strict", "Friendly"], index=0,
                            help="Affects how the review is worded.")

    code = st.text_area("Paste your code", height=240, placeholder="Drop your function/class/module here…")

    # Run preset review if clicked
    if review_click is not None:
        if not code.strip():
            st.info("Paste your code above, then click the review preset again.")
        else:
            focus_msg = REVIEW_PRESETS[review_click][1]
            prompt = f"{code}\n\nReviewer focus: {focus_msg}\nTone: {tone}."
            with st.spinner("Reviewing code…"):
                out = code_review(prompt, lang)
            st.markdown("### Review")
            st.markdown(f"""
            <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
              <div style="line-height:1.6;white-space:pre-wrap">{out}</div>
            </div>
            """, unsafe_allow_html=True)
            record_event("coding", {"type":"review","lang":lang,"focus":REVIEW_PRESETS[review_click][0]})

    # Manual review button
    if st.button("Run full review", type="primary", use_container_width=True):
        if not code.strip():
            st.warning("Please paste some code.")
        else:
            with st.spinner("Reviewing code…"):
                out = code_review(code, lang)
            st.markdown("### Review")
            st.markdown(f"""
            <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
              <div style="line-height:1.6;white-space:pre-wrap">{out}</div>
            </div>
            """, unsafe_allow_html=True)
            record_event("coding", {"type":"review","lang":lang})

# =========================================================
# Tab 2: Debug Help
# =========================================================
with tab2:
    st.markdown("#### Common issues (1-click diagnose)")
    DEBUG_PRESETS = [
        ("NoneType is not subscriptable (Python)", "TypeError: 'NoneType' object is not subscriptable"),
        ("List index out of range (Python)", "IndexError: list index out of range"),
        ("CORS error (Web/JS)", "Access to fetch at '…' from origin '…' has been blocked by CORS policy"),
        ("Module not found (Node/Python)", "ModuleNotFoundError / Cannot find module 'x'"),
        ("NullPointerException (Java)", "java.lang.NullPointerException"),
    ]
    cols = st.columns(5)
    dbg_click = None
    for i, (label, errtxt) in enumerate(DEBUG_PRESETS):
        if cols[i].button(label, key=f"dbg_{i}", use_container_width=True):
            dbg_click = i

    st.markdown("---")
    lang2 = st.selectbox("Language ", ["python","javascript","java","c++","c","go","rust"], key="dbg_lang")
    err = st.text_area("Paste error message/stacktrace", height=140, placeholder="Exact error output helps a ton.")
    snip = st.text_area("Optional: related code snippet", height=140, placeholder="The few lines around the error…")

    # If a preset was clicked, run instantly (uses current snippet if provided)
    if dbg_click is not None:
        err_to_run = DEBUG_PRESETS[dbg_click][1]
        with st.spinner("Diagnosing…"):
            out = debug_help(err_to_run if not err.strip() else err, snip, lang2)
        st.markdown("### Diagnosis & Fix")
        st.markdown(f"""
        <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
          <div style="line-height:1.6;white-space:pre-wrap">{out}</div>
        </div>
        """, unsafe_allow_html=True)
        record_event("coding", {"type":"debug","lang":lang2,"preset":DEBUG_PRESETS[dbg_click][0]})

    if st.button("Diagnose error", use_container_width=True):
        if not err.strip() and not snip.strip():
            st.warning("Please paste an error or snippet (or click a preset above).")
        else:
            with st.spinner("Diagnosing…"):
                out = debug_help(err, snip, lang2)
            st.markdown("### Diagnosis & Fix")
            st.markdown(f"""
            <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
              <div style="line-height:1.6;white-space:pre-wrap">{out}</div>
            </div>
            """, unsafe_allow_html=True)
            record_event("coding", {"type":"debug","lang":lang2})

# =========================================================
# Tab 3: Concept Explain
# =========================================================
with tab3:
    st.markdown("#### Quick topics (click to run)")
    CONCEPT_PRESETS = [
        "Big-O notation with simple examples",
        "Async vs threading (Python/JS)",
        "REST vs GraphQL: when to choose which?",
        "SQL joins (inner/left/right/full) with small tables",
        "OOP: encapsulation, inheritance, polymorphism",
        "Dependency injection: what and why?",
    ]
    cols = st.columns(3)
    concept_click = None
    for i, label in enumerate(CONCEPT_PRESETS):
        if cols[i % 3].button(label, key=f"cpt_{i}", use_container_width=True):
            concept_click = i

    st.markdown("---")
    topic = st.text_input("Concept to explain", placeholder="e.g., async/await")
    lang3 = st.selectbox("Language  ", ["python","javascript","java","c++","c","go","rust"], key="exp")

    if concept_click is not None:
        prompt = f"{CONCEPT_PRESETS[concept_click]} — provide a brief explanation with a tiny example."
        with st.spinner("Explaining…"):
            out = concept_explain(prompt, lang3)
        st.markdown("### Explanation")
        st.markdown(f"""
        <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
          <div style="line-height:1.6;white-space:pre-wrap">{out}</div>
        </div>
        """, unsafe_allow_html=True)
        record_event("coding", {"type":"concept","lang":lang3,"preset":CONCEPT_PRESETS[concept_click]})

    if st.button("Explain", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a concept or click a preset above.")
        else:
            with st.spinner("Explaining…"):
                out = concept_explain(topic, lang3)
            st.markdown("### Explanation")
            st.markdown(f"""
            <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
              <div style="line-height:1.6;white-space:pre-wrap">{out}</div>
            </div>
            """, unsafe_allow_html=True)
            record_event("coding", {"type":"concept","lang":lang3})
