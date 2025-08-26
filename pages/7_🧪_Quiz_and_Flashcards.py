import time
import streamlit as st
from core.utils import inject_css, record_event, parse_json_maybe
from core.models_groq import generate_quiz
from core.evaluation import quiz_score
from modules.personalization import flashcards as make_flashcards  # uses Groq; returns JSON string
from core.sidebar import render_sidebar

# Page config FIRST
st.set_page_config(page_title="Quiz + Flashcards", page_icon="🧪", layout="wide")
inject_css()
render_sidebar("Quiz & Flashcards")

# ------------------------------ Header ------------------------------
st.markdown("""
<div class="card pop" style="padding:22px;
  background: linear-gradient(135deg, rgba(15,26,48,.95) 0%, rgba(11,18,32,.95) 60%, rgba(0,194,209,.18) 120%);
  border:1px solid rgba(0,194,209,.35);">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;">
    <div>
      <div class="app-title" style="margin-bottom:6px;">MCQ Quiz & Flashcards</div>
      <div class="subtle">Generate quizzes and study with flip-style flashcards — blue·frozi style, no dummy data.</div>
    </div>
    <div style="min-width:240px;height:88px;border-radius:16px;
                background: radial-gradient(70px 70px at 80% 40%, rgba(0,194,209,.55), transparent 60%),
                            linear-gradient(135deg,#0b1220 0%,#0f1a30 60%,rgba(0,194,209,.65) 135%);
                box-shadow:0 10px 28px rgba(0,0,0,.35);">
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

tab_quiz, tab_cards = st.tabs(["🧪 Quiz", "🗂️ Flashcards"])

# Keep some state
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "quiz_started_at" not in st.session_state:
    st.session_state.quiz_started_at = None
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "fc_json" not in st.session_state:
    st.session_state.fc_json = None

# ====================================================================
# QUIZ TAB
# ====================================================================
with tab_quiz:
    # ---------------- Preset topics ----------------
    st.markdown("#### One-click topics")
    PRESETS = [
        "Data Structures (Arrays/Stacks/Queues)",
        "Time Complexity & Big-O",
        "SQL Basics & Joins",
        "OOP Principles",
        "Networking: OSI vs TCP/IP",
        "Linear Algebra (Vectors/Matrices)",
    ]
    cols = st.columns(3)
    preset_clicked = None
    for i, label in enumerate(PRESETS):
        if cols[i % 3].button(label, key=f"pz_{i}", use_container_width=True):
            preset_clicked = label

    st.markdown("---")

    # ---------------- Controls ----------------
    c1, c2, c3 = st.columns([1.6, 0.9, 1.1])
    topic = c1.text_input("Quiz topic", value=(preset_clicked or ""), placeholder="e.g., Data Structures")
    nq = c2.slider("Questions", 3, 15, 5)
    difficulty = c3.segmented_control("Difficulty", options=["easy","medium","hard"], default="medium")

    # Generate actions
    gen_col1, gen_col2 = st.columns([1,1])
    generate_now = gen_col1.button("Generate quiz", type="primary", use_container_width=True)
    clear_quiz = gen_col2.button("Clear current quiz", use_container_width=True)

    if clear_quiz:
        if st.session_state.quiz:
            for i in range(1, len(st.session_state.quiz.get("questions", [])) + 1):
                st.session_state.pop(f"q_{i}", None)
        st.session_state.quiz = None
        st.session_state.last_results = None
        st.session_state.quiz_started_at = None
        st.success("Cleared.")

    if preset_clicked and not topic:
        topic = preset_clicked

    if generate_now or (preset_clicked and topic):
        if not topic.strip():
            st.warning("Please enter a topic or click a preset above.")
        else:
            with st.spinner("Generating quiz…"):
                raw = generate_quiz(topic.strip(), nq, difficulty)
            obj = parse_json_maybe(raw)
            if not obj or "questions" not in obj:
                st.error("Quiz generation failed. Please try again.")
            else:
                # Reset previous selections
                for i in range(1, len(obj["questions"]) + 1):
                    st.session_state.pop(f"q_{i}", None)
                st.session_state.quiz = obj
                st.session_state.last_results = None
                st.session_state.quiz_started_at = time.time()
                st.success(f"Quiz ready on **{obj.get('topic', topic)}**. Good luck!")

    # ---------------- Render quiz ----------------
    if st.session_state.quiz:
        qz = st.session_state.quiz
        st.markdown(f"**Topic:** {qz.get('topic', topic)}  ·  **Difficulty:** {difficulty}  ·  **Questions:** {len(qz['questions'])}")

        # PROGRESS: count only answered (not sentinel)
        answered_count = 0
        total_q = len(qz["questions"])
        letters = ["A", "B", "C", "D"]

        answers_tmp = []   # may include -1 sentinel
        correct_indices = []

        for i, q in enumerate(qz["questions"], 1):
            st.markdown(f"**Q{i}. {q['q']}**")

            # Options with a sentinel first so nothing is selected by default
            opts = [-1, 0, 1, 2, 3]
            fmt = lambda k: "— Select an answer —" if k == -1 else f"{letters[k]}. {q['choices'][k]}"

            # Ensure previous value is respected; default to sentinel
            current = st.session_state.get(f"q_{i}", -1)
            idx = st.radio(
                "Select an answer",
                options=opts,
                format_func=fmt,
                key=f"q_{i}",
                horizontal=False,
                # If Streamlit version supports it, you could pass index=None; we rely on sentinel instead.
            )
            if idx != -1:
                answered_count += 1

            answers_tmp.append(idx)
            correct_indices.append(q["answer_index"])
            st.markdown("---")

        st.progress(answered_count / total_q if total_q else 0)
        st.caption(f"Answered {answered_count}/{total_q}")

        # SUBMIT
        if st.button("Submit answers", type="primary", use_container_width=True):
            # Block submit unless all answered (no sentinel)
            if any(st.session_state.get(f"q_{i}", -1) == -1 for i in range(1, total_q + 1)):
                st.warning("Please answer all questions.")
            else:
                # Build final answers (0-3 only)
                answers = [st.session_state[f"q_{i}"] for i in range(1, total_q + 1)]
                res = quiz_score(answers, correct_indices)
                elapsed = 0
                if st.session_state.quiz_started_at:
                    elapsed = int(time.time() - st.session_state.quiz_started_at)
                st.session_state.last_results = {"res": res, "elapsed": elapsed}

                score_line = f"Score: {res['correct']}/{res['total']}  •  Accuracy: {int(res['accuracy']*100)}%  •  Time: {elapsed}s"
                if res['accuracy'] >= 0.8:
                    st.success(score_line)
                    st.balloons()
                elif res['accuracy'] >= 0.6:
                    st.info(score_line)
                else:
                    st.warning(score_line)
                    st.snow()

                st.subheader("Review")
                wrong_idx = []
                for i, q in enumerate(qz["questions"], 1):
                    your = answers[i-1]
                    correct = q["answer_index"]
                    cls = "correct" if your == correct else "incorrect"
                    if your != correct:
                        wrong_idx.append(i-1)
                    st.markdown(f"""
                    <div class="card {cls}">
                      <b>Q{i}.</b> {q['q']}<br>
                      <b>Your:</b> {letters[your]} • <b>Correct:</b> {letters[correct]}
                      <div class="subtle">Why: {q['explanation']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                cdl, cretry = st.columns([1,1])
                lines = [f"Topic: {qz.get('topic', topic)}",
                         f"Questions: {len(qz['questions'])}",
                         f"Score: {res['correct']}/{res['total']}  ({int(res['accuracy']*100)}%)",
                         f"Time: {elapsed}s", "", "Details:"]
                for i, q in enumerate(qz["questions"], 1):
                    lines.append(f"Q{i}: {q['q']}")
                    lines.append(f"  Your: {letters[answers[i-1]]} | Correct: {letters[q['answer_index']]}")
                    lines.append(f"  Why: {q['explanation']}")

                cdl.download_button(
                    "Download results (.txt)",
                    "\n".join(lines),
                    file_name="quiz_results.txt",
                    mime="text/plain",
                    use_container_width=True
                )

                if wrong_idx:
                    if cretry.button("Retake incorrect only", use_container_width=True):
                        new_qs = [qz["questions"][k] for k in wrong_idx]
                        st.session_state.quiz = {"topic": qz.get("topic", topic) + " (Retry)", "questions": new_qs}
                        for i in range(1, len(new_qs) + 1):
                            st.session_state.pop(f"q_{i}", None)
                        st.session_state.quiz_started_at = time.time()
                        st.rerun()

                record_event("quiz", {"topic": qz.get("topic", topic), "n": len(qz["questions"]), "acc": float(res["accuracy"])})

# ====================================================================
# FLASHCARDS TAB
# ====================================================================
with tab_cards:
    st.markdown("#### Create flashcards from a topic")
    fc_c1, fc_c2, fc_c3 = st.columns([1.6, 0.9, 1.1])
    fc_topic = fc_c1.text_input("Flashcards topic", placeholder="e.g., Binary Trees")
    fc_n = fc_c2.slider("Cards", 4, 25, 10)
    fc_gen = fc_c3.button("Generate", type="primary", use_container_width=True)

    if fc_gen:
        if not fc_topic.strip():
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Generating flashcards…"):
                raw = make_flashcards(fc_topic.strip(), fc_n)
            obj = parse_json_maybe(raw)
            if not obj or "cards" not in obj:
                st.error("Could not parse flashcards. Please retry.")
            else:
                st.session_state.fc_json = obj
                # Reset any expander/reveal states from previous deck
                for k in list(st.session_state.keys()):
                    if str(k).startswith("fc_open_") or str(k).startswith("fc_show_"):
                        st.session_state.pop(k, None)
                st.success(f"Flashcards ready for **{obj.get('topic', fc_topic)}**.")
                record_event("qna", {"feature": "flashcards", "topic": obj.get("topic", fc_topic)})

    if st.session_state.fc_json:
        fc = st.session_state.fc_json
        st.markdown(f"**Topic:** {fc.get('topic', fc_topic)}  ·  **Cards:** {len(fc.get('cards', []))}")
        st.markdown("---")

        st.markdown("#### Practice (flip the card)")
        for i, c in enumerate(fc.get("cards", []), 1):
            open_key = f"fc_open_{i}"
            show_key = f"fc_show_{i}"
            open_state = st.session_state.get(open_key, False)
            show_state = st.session_state.get(show_key, False)

            with st.expander(f"Card {i}: {c.get('front', '')}", expanded=open_state):
                if st.button(f"Reveal answer {i}", key=f"rev_{i}"):
                    st.session_state[show_key] = True
                    st.session_state[open_key] = True
                    st.rerun()

                if st.session_state.get(show_key, False):
                    st.write(c.get("back", ""))

        with st.expander("View all (compact)"):
            for i, c in enumerate(fc.get("cards", []), 1):
                st.markdown(f"- **{i}. {c.get('front','')}** → {c.get('back','')}")

        lines = [f"Flashcards — {fc.get('topic', fc_topic)}", ""]
        for i, c in enumerate(fc.get("cards", []), 1):
            lines.append(f"{i}. {c.get('front','')}")
            lines.append(f"   {c.get('back','')}")
        st.download_button(
            "Download flashcards (.txt)",
            "\n".join(lines),
            file_name="flashcards.txt",
            mime="text/plain",
            use_container_width=True
        )
