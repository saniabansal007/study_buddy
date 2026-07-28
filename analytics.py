from collections import defaultdict
import streamlit as st
from utils import (run_prompt, parse_json, GRAPH_PROMPT, MAX_CHARS,
                   svg_bar_chart, svg_line_chart, svg_concept_graph)


def page_graph(doc: dict, doc_id: str):
    st.title("Concept Dependency Graph")
    st.caption("Key concepts from your notes and how they depend on each other.")

    regen = st.button(
        "Regenerate Graph" if doc.get("concept_graph_svg") else "Generate Graph",
        type="primary",
    )
    if regen:
        doc["concept_graph_svg"] = None

    if not doc.get("concept_graph_svg"):
        with st.spinner("Extracting concepts…"):
            try:
                raw  = run_prompt(
                    GRAPH_PROMPT,
                    {"text": doc["text"][:MAX_CHARS]},
                    max_tokens=2000,
                )
                data     = parse_json(raw)
                concepts = [{"id": c.get("name", c.get("id", "?")),
                             "description": c.get("description", "")}
                            for c in data.get("concepts", [])]
                doc["concept_graph_svg"] = svg_concept_graph(
                    concepts, data.get("edges", [])
                )
            except Exception as e:
                st.error(str(e))

    if doc.get("concept_graph_svg"):
        st.components.v1.html(doc["concept_graph_svg"], height=650, scrolling=False)
    else:
        st.info("Click Generate Graph to extract concepts from your notes.")


def page_analytics(doc: dict, doc_id: str):
    st.title("Learning Analytics")
    st.caption("Track your progress across quizzes and flashcard reviews.")

    # Build topic stats from quiz history 
    ts: dict = defaultdict(lambda: {"correct": 0, "total": 0})
    for h in doc["quiz_history"]:
        t = h.get("topic", "General")
        ts[t]["total"]   += 1
        ts[t]["correct"] += int(bool(h.get("correct")))

    topics     = list(ts.keys())
    accuracies = [round(ts[t]["correct"] / ts[t]["total"] * 100, 1)
                  if ts[t]["total"] else 0 for t in topics]
    colors     = ["#3f7d6e" if a >= 60 else "#c1572a" for a in accuracies]
    weak       = [t for t, a in zip(topics, accuracies) if a < 60]

    # Build flashcard interval series
    fc_series = [
        {"topic":     c.get("topic", "General"),
         "intervals": [h["interval"] for h in c["history"]]}
        for c in doc["flashcards"].values() if c["history"]
    ]

    # Readiness score 
    qt = len(doc["quiz_history"])
    qc = sum(1 for h in doc["quiz_history"] if h.get("correct"))
    qs = (qc / qt * 100) if qt else 0

    ft = sum(len(c["history"]) for c in doc["flashcards"].values())
    fc = sum(sum(1 for h in c["history"] if h.get("correct"))
             for c in doc["flashcards"].values())
    fs = (fc / ft * 100) if ft else 0

    readiness = round(
        (qs * 0.5 + fs * 0.5) if qt and ft else qs if qt else fs, 1
    )

    # Metrics row 
    col1, col2, col3 = st.columns(3)
    col1.metric("Exam Readiness", f"{readiness}%", help="overall score")
    col2.metric("Quiz Attempts",  qt,               help="questions answered")
    col3.metric("Card Reviews",   ft,               help="flashcard sessions")

    if weak:
        st.warning("⚠ Weak Topics (< 60% accuracy): " + ", ".join(weak))

    # Charts 
    st.subheader("Topic Accuracy")
    st.components.v1.html(svg_bar_chart(topics, accuracies, colors), height=320)

    st.subheader("Flashcard Interval Growth")
    st.components.v1.html(svg_line_chart(fc_series), height=280)