from datetime import datetime
import streamlit as st
from utils import run_prompt, parse_json, QUIZ_PROMPT, MAX_CHARS


def page_quiz(doc: dict, doc_id: str):
    st.title("Quiz Generator")

    # State 2: Taking the quiz 
    if st.session_state.quiz_taking and doc.get("current_quiz"):
        _render_quiz_form(doc)
        return

    # State 3: Showing results
    if doc.get("last_quiz_results"):
        _render_results(doc)
        return

    # State 1: Generate form
    _render_generate_form(doc)


# State 1

def _render_generate_form(doc: dict):
    col1, col2= st.columns(2)
    with col1:
        num= st.selectbox("Questions", [3, 5, 8, 10], index=1)
    with col2:
        difficulty= st.radio("Difficulty", ["easy", "medium", "hard"],
                              index=1, horizontal=True)

    if st.button("Generate Quiz", type="primary"):
        with st.spinner("Generating questions…"):
            try:
                raw = run_prompt(
                    QUIZ_PROMPT,
                    {"n": num, "difficulty": difficulty, "text": doc["text"][:MAX_CHARS]},
                    max_tokens=3000,
                )
                doc["current_quiz"]  = parse_json(raw)
                doc["last_quiz_results"]= None
                st.session_state.quiz_taking= True
                st.session_state.quiz_answers= {}
                st.rerun()
            except Exception as e:
                st.error(str(e))
    else:
        st.info("Set your options above and click Generate Quiz.")


# State 2

def _render_quiz_form(doc: dict):
    qs = doc["current_quiz"]
    st.subheader("Answer every question, then click Submit.")

    with st.form("quiz_form"):
        answers = {}
        for i, q in enumerate(qs):
            st.markdown(f"**{i+1}. {q['question']}**")
            answers[i] = st.radio(
                f"q{i}",
                options=list(range(len(q["options"]))),
                format_func=lambda j, q=q: q["options"][j],
                key=f"quiz_radio_{i}",
                label_visibility="collapsed",
                index=None,
            )
            st.write("")

        unanswered= [i for i, a in answers.items() if a is None]
        submitted = st.form_submit_button("Submit Answers", type="primary")

        if submitted and unanswered:
            st.warning(f"Please answer question(s): {', '.join(str(i+1) for i in unanswered)}")
            submitted = False
    if submitted:
        _grade_quiz(doc, qs, answers)


def _grade_quiz(doc: dict, qs: list, answers: dict):
    results, correct = [], 0
    for i, q in enumerate(qs):
        sel      = answers.get(i)
        is_right = sel is not None and sel == q["correct_index"]
        if is_right:
            correct += 1
        results.append({
            "question":      q["question"],
            "topic":         q.get("topic", "General"),
            "options":       q["options"],
            "correct_index": q["correct_index"],
            "selected":      sel,
            "correct":       is_right,
            "explanation":   q.get("explanation", ""),
        })
        doc["quiz_history"].append({
            "question": q["question"],
            "topic":    q.get("topic", "General"),
            "correct":  is_right,
            "ts":       datetime.now().isoformat(),
        })
    doc["last_quiz_results"]      = {"results": results, "score": correct, "total": len(qs)}
    st.session_state.quiz_taking  = False
    st.session_state.quiz_answers = {}
    st.rerun()


# State 3

def _render_results(doc: dict):
    r = doc["last_quiz_results"]
    st.markdown(
        f"<div style='background:#1f2433;color:#fff;border-radius:10px;"
        f"padding:16px 22px;display:flex;align-items:center;"
        f"justify-content:space-between;margin-bottom:18px'>"
        f"<span style='font-size:15px'>You scored</span>"
        f"<strong style='font-size:28px;color:#d9a441'>{r['score']} / {r['total']}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    for res in r["results"]:
        border = "#3f7d6e" if res["correct"] else "#c1572a"
        st.markdown(
            f"<div style='border-left:3px solid {border};background:#fff;"
            f"border-radius:10px;padding:14px 18px;margin-bottom:4px;"
            f"border:1px solid #e7e1d3;color:#1f2433'><strong>{res['question']}</strong></div>",
            unsafe_allow_html=True,
        )
        for j, opt in enumerate(res["options"]):
            if j == res["correct_index"]:
                st.success(f"✓ {opt}")
            elif j == res["selected"] and not res["correct"]:
                st.error(f"✗ {opt}")
            else:
                st.write(f"{opt}")
        if res["explanation"]:
            st.caption(res["explanation"])
        st.write("")

    col1, col2= st.columns(2)
    with col1:
        if st.button("New Quiz", type="primary"):
            doc["last_quiz_results"] = None
            doc["current_quiz"]      = None
            st.rerun()
    with col2:
        if st.button("View Analytics"):
            st.session_state.page = "analytics"
            st.rerun()