import uuid
from datetime import datetime
import streamlit as st
from utils import run_prompt, parse_json, sm2, FLASHCARD_PROMPT, MAX_CHARS


def page_flashcards(doc: dict, doc_id: str):
    st.title("Flashcards")
    st.caption("SM-2 spaced repetition — cards you struggle with come back sooner.")

    # Generate controls
    col1, col2 = st.columns([2, 1])
    with col1:
        count= st.selectbox("Cards to generate", [8, 10, 15], index=1)
    with col2:
        st.write("")
        st.write("")
        if st.button("Generate Flashcards", type="primary"):
            _generate_cards(doc, count)

    # Card display
    total = len(doc["flashcards"])
    if total== 0:
        st.info("No flashcards yet — generate some above.")
        return

    now = datetime.now().isoformat()
    due = sorted(
        [c for c in doc["flashcards"].values() if c["next_review"] <= now],
        key=lambda c: c["next_review"],
    )

    st.write(f"**{len(due)} card{'s' if len(due) != 1 else ''} due** · {total} total")

    if not due:
        st.success(f" All {total} cards reviewed! Come back later for the next round.")
        return

    _render_card(doc, due[0])


# Helpers

def _generate_cards(doc: dict, count: int):
    with st.spinner("Generating flashcards…"):
        try:
            raw= run_prompt(
                FLASHCARD_PROMPT,
                {"n": count, "text": doc["text"][:MAX_CHARS]},
                max_tokens=3000,
            )
            cards = parse_json(raw)
            now   = datetime.now().isoformat()
            for item in cards:
                cid = uuid.uuid4().hex
                doc["flashcards"][cid] = {
                    "id":          cid,
                    "front":       item.get("front", ""),
                    "back":        item.get("back", ""),
                    "topic":       item.get("topic", "General"),
                    "ease_factor": 2.5,   # SM-2 default starting ease
                    "interval":    1,
                    "repetitions": 0,
                    "next_review": now,   # all cards due immediately
                    "history":     [],
                }
            st.rerun()
        except Exception as e:
            st.error(str(e))


def _render_card(doc: dict, card: dict):
    # Front of card
    st.markdown(
        f"<div style='border:1px solid #e7e1d3;border-radius:10px;background:#fff;"
        f"padding:28px 32px;box-shadow:0 4px 12px rgba(31,36,51,.08)'>"
        f"<div style='font-size:17px;font-weight:600;color:#1f2433;"
        f"font-family:Georgia,serif'>{card['front']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # Back of card (hidden until expanded) 
    with st.expander("Reveal Answer", key=f"expander_{card['id']}"):
        st.write(card["back"])
        st.caption(f"Topic: {card['topic']}")
        st.divider()
        st.write("**How well did you recall this?**")

        cols = st.columns(4)
        ratings = [
            ("Again", 0, "#c1572a"),
            ("Hard",  3, "#a07840"),
            ("Good",  4, "#3f7d6e"),
            ("Easy",  5, "#4a7fa5"),
        ]
        for col, (label, quality, color) in zip(cols, ratings):
            with col:
                if st.button(
                    label,
                    key=f"rate_{card['id']}_{quality}",
                    use_container_width=True,
                ):
                    doc["flashcards"][card["id"]] = sm2(
                        doc["flashcards"][card["id"]], quality
                    )
                    st.rerun()