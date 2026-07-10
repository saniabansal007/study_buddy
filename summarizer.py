import streamlit as st
from utils import run_prompt, SUMMARIZE_PROMPT, MAX_CHARS


def page_summarizer(doc: dict, doc_id: str):
    st.title("Notes Summarizer")
    st.caption("Generate a clean, organised summary of your uploaded notes.")

    length= st.radio( "Summary length",["short", "medium", "detailed"],
        index=1, horizontal=True,)

    if st.button("Generate Summary", type="primary"):
        instr= {"short": "150-200 words",
                 "medium": "350-450 words",
                 "detailed": "thorough study notes"}[length]
        with st.spinner("Summarising…"):
            try:
                doc["last_summary"] = run_prompt( SUMMARIZE_PROMPT,
                    {"instr": instr, "text": doc["text"][:MAX_CHARS]}, )
            except Exception as e:
                st.error(str(e))

    if doc["last_summary"]:
        st.markdown(doc["last_summary"])
    else:
        st.info("Choose a length and click Generate Summary.")