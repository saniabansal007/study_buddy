import streamlit as st
from utils import llm_invoke, rag_answer, retrieve, SOCRATIC_SYSTEM, _chroma_stores


def page_qna(doc: dict, doc_id: str):
    st.title("Q&A Chat")
    st.caption("Ask questions- answers are grounded in your uploaded notes via RAG.")

    # warn user that first question triggers indexing
    if not doc["qna_history"] and doc_id not in _chroma_stores:
        st.info(" Your first question will index your notes for search- this takes a few seconds once.")

    # Chat history 
    for msg in doc["qna_history"]:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander(f" {len(msg['sources'])} source(s)"):
                    for src in msg["sources"]:
                        st.markdown(
                            f"<blockquote style='border-left:2px solid #e7e1d3;"
                            f"padding:6px 10px;font-size:12px;color:#756f5e'>"
                            f"{src[:300]}{'…' if len(src) > 300 else ''}</blockquote>",
                            unsafe_allow_html=True,
                        )

    # Input 
    question = st.chat_input("Ask something about your notes…")
    if question:
        doc["qna_history"].append({"role": "user", "content": question})
        with st.spinner("Searching notes…"):
            try:
                st.write("step 1: calling rag_answer")
                answer, sources = rag_answer(doc_id, question, doc["text"])
                st.write("step 2: got answer", answer)
                doc["qna_history"].append({
                    "role":    "ai",
                    "content": answer,
                    "sources": sources,
                })
                st.write("step 3: appended to history")
            except Exception as e:
                import traceback
                st.error(f"FULL ERROR: {traceback.format_exc()}")
        st.rerun()


def page_socratic(doc: dict, doc_id: str):
    st.title("Socratic Tutor")
    st.caption("The tutor guides you with questions — it won't give direct answers.")

    # Chat history
    for msg in doc["socratic_history"]:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(msg["content"])

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("↺ New Session"):
            doc["socratic_history"] = []
            st.rerun()

    # Input
    message = st.chat_input("Tell the tutor what you're working on…")
    if message:
        ctx      = retrieve(doc_id, message) or [doc["text"][:3000]]
        context  = "\n\n".join(ctx)
        messages = [{"role": "system",
                     "content": SOCRATIC_SYSTEM.format(context=context)}]
        messages.extend(doc["socratic_history"][-6:])
        messages.append({"role": "user", "content": message})
        with st.spinner("Tutor is thinking…"):
            try:
                resp = llm_invoke(messages, max_tokens=500)
                doc["socratic_history"] += [
                    {"role": "user",      "content": message},
                    {"role": "assistant", "content": resp},
                ]
            except Exception as e:
                st.error(str(e))
        st.rerun()