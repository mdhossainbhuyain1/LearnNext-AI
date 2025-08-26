import streamlit as st
from core.utils import inject_css, record_event, parse_json_maybe
from modules.personalization import study_plan, flashcards as make_flashcards
from core.sidebar import render_sidebar
render_sidebar("Personalized Learning")

st.set_page_config(page_title="Personalized Learning", page_icon="🎯", layout="wide")
inject_css()

# ------------------------- Header -------------------------
st.markdown("""
<div class="card pop" style="padding:22px;
  background: linear-gradient(135deg, rgba(15,26,48,.95) 0%, rgba(11,18,32,.95) 60%, rgba(0,194,209,.18) 120%);
  border:1px solid rgba(0,194,209,.35);">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;">
    <div>
      <div class="app-title" style="margin-bottom:6px;">Personalized Learning</div>
      <div class="subtle">Get a focused 4-week plan, micro-habits, and free resources — crafted to your goals.</div>
    </div>
    <div style="min-width:240px;height:88px;border-radius:16px;
                background: radial-gradient(70px 70px at 80% 40%, rgba(0,194,209,.55), transparent 60%),
                            linear-gradient(135deg,#0b1220 0%,#0f1a30 60%,rgba(0,194,209,.65) 135%);
                box-shadow:0 10px 28px rgba(0,0,0,.35);">
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Keep state for last plan
if "pl_last" not in st.session_state:
    st.session_state.pl_last = None

# ------------------------- Quick presets -------------------------
st.markdown("#### One-click presets")
PRESETS = [
    {
        "name": "Student",
        "course": "Calculus I",
        "grade": "Beginner",
        "goals": "Master limits, derivatives, and basic integrals; build problem-solving speed; aim for an A.",
        "hours": 6
    },
    {
        "name": "Student",
        "course": "Data Structures",
        "grade": "Intermediate",
        "goals": "Solidify arrays, stacks, queues, linked lists, trees; practice complexity analysis and coding patterns.",
        "hours": 8
    },
    {
        "name": "Student",
        "course": "Machine Learning Basics",
        "grade": "Beginner",
        "goals": "Understand train/test splits, linear/logistic regression, overfitting/regularization; implement in scikit-learn.",
        "hours": 7
    },
]
cols = st.columns(3)
preset_clicked = None
for i, p in enumerate(PRESETS):
    if cols[i].button(p["course"], key=f"pl_preset_{i}", use_container_width=True):
        preset_clicked = p

if preset_clicked:
    with st.spinner("Designing your study plan…"):
        plan = study_plan(
            preset_clicked["name"],
            preset_clicked["course"],
            preset_clicked["grade"],
            preset_clicked["goals"],
            preset_clicked["hours"]
        )
    st.session_state.pl_last = {
        "title": f"{preset_clicked['course']} · {preset_clicked['grade']}",
        "plan": plan,
        "meta": preset_clicked
    }
    record_event("qna", {"feature":"personalized_plan","course":preset_clicked["course"]})

# ------------------------- Custom plan form -------------------------
st.markdown("---")
st.markdown("#### Or create your own")

with st.form("plan_form", clear_on_submit=False):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        name = st.text_input("Your name", value="Student")
        course = st.text_input("Course/Subject", placeholder="e.g., Calculus I")
        grade = st.selectbox("Current level/grade", ["Beginner","Intermediate","Advanced","Graduate"], index=0)
        hours = st.slider("Hours per week", 2, 20, 6)
    with c2:
        goals = st.text_area("Your goals", placeholder="e.g., Pass with A; build strong basics; daily practice…", height=120)
        focus = st.segmented_control("Focus", options=["Balanced","Concepts","Problem-solving","Exam Prep"], default="Balanced")
        prefs = st.multiselect("Study preferences (used to shape your plan)", 
                               ["Videos", "Textbook notes", "Practice problems", "Flashcards", "Group study"],
                               default=["Practice problems","Flashcards"])
        constraints = st.text_input("Constraints (optional)", placeholder="e.g., weekends only; slow internet;")

    submitted = st.form_submit_button("Generate study plan")

if submitted:
    if not course.strip() or not goals.strip():
        st.warning("Please fill in both **Course/Subject** and **Your goals**.")
    else:
        # Soft prompt shaping via goals (keeps backend unchanged)
        extra = f"\nPreferences: {', '.join(prefs) or 'none'}; Focus: {focus}; Constraints: {constraints or 'none'}."
        with st.spinner("Designing your study plan…"):
            plan = study_plan(name.strip(), course.strip(), grade.strip(), goals.strip() + extra, hours)
        st.session_state.pl_last = {
            "title": f"{course.strip()} · {grade.strip()}",
            "plan": plan,
            "meta": {"name": name, "course": course, "grade": grade, "goals": goals, "hours": hours,
                     "focus": focus, "prefs": prefs, "constraints": constraints}
        }
        record_event("qna", {"feature":"personalized_plan","course":course})

# ------------------------- Show plan (if available) -------------------------
if st.session_state.pl_last:
    st.markdown("---")
    st.markdown(f"### 📋 4-week Plan — {st.session_state.pl_last['title']}")
    st.markdown(f"""
    <div class="card pop" style="border-left: 4px solid rgba(0,194,209,.65);">
      <div style="line-height:1.6;white-space:pre-wrap">{st.session_state.pl_last['plan']}</div>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        "Download plan (.txt)",
        data=st.session_state.pl_last["plan"],
        file_name="study_plan.txt",
        mime="text/plain",
        use_container_width=True
    )

# ========================= Flashcards =========================
st.markdown("---")
st.markdown("### 🗂️ Flashcards")

fc_c1, fc_c2, fc_c3 = st.columns([1.6, 0.9, 1.1])
topic = fc_c1.text_input("Flashcards topic", placeholder="e.g., Derivatives")
num = fc_c2.slider("Number of cards", 4, 20, 10)
gen_fc = fc_c3.button("Generate", type="primary", use_container_width=True)

if "pl_fc" not in st.session_state:
    st.session_state.pl_fc = None

if gen_fc:
    if not topic.strip():
        st.warning("Please enter a topic for flashcards.")
    else:
        with st.spinner("Generating flashcards…"):
            out = make_flashcards(topic.strip(), num)
        obj = parse_json_maybe(out) or {}
        cards = obj.get("cards", [])
        if not cards:
            st.error("Could not parse flashcards. Please try again.")
        else:
            st.session_state.pl_fc = {"topic": obj.get("topic", topic), "cards": cards}
            st.success(f"Flashcards ready for **{obj.get('topic', topic)}**.")
            record_event("qna", {"feature":"flashcards","topic":topic})

if st.session_state.pl_fc:
    fc = st.session_state.pl_fc
    st.markdown(f"**Topic:** {fc['topic']}  ·  **Cards:** {len(fc['cards'])}")
    st.markdown("---")

    # Practice mode (flip to reveal)
    st.markdown("#### Practice (flip the card)")
    for i, c in enumerate(fc["cards"], 1):
        with st.expander(f"Card {i}: {c.get('front','')}", expanded=False):
            if st.button(f"Reveal answer {i}", key=f"pl_rev_{i}"):
                st.write(c.get("back",""))

    # Compact view + download
    with st.expander("View all (compact)"):
        for i, c in enumerate(fc["cards"], 1):
            st.markdown(f"- **{i}. {c.get('front','')}** → {c.get('back','')}")
    lines = [f"Flashcards — {fc['topic']}", ""]
    for i, c in enumerate(fc["cards"], 1):
        lines.append(f"{i}. {c.get('front','')}")
        lines.append(f"   {c.get('back','')}")
    st.download_button(
        "Download flashcards (.txt)",
        "\n".join(lines),
        file_name="flashcards.txt",
        mime="text/plain",
        use_container_width=True
    )

# Tiny tip
st.caption("Tip: Use presets for a quick start, then fine-tune with preferences. Everything here is generated live — no dummy data.")
