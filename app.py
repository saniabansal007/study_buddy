import os, uuid
import streamlit as st
from utils import ok_file, read_file, chunk, MAX_BYTES, UPLOAD_DIR

# initialise session state variables
# Without session_state, these values would reset every time Streamlit reruns the script.
def init_state():
    if "documents" not in st.session_state: st.session_state.documents= {}
    if "doc_id" not in st.session_state: st.session_state.doc_id= None
    if "page" not in st.session_state: st.session_state.page= "summarizer"
    if "quiz_taking" not in st.session_state: st.session_state.quiz_taking= False
    if "quiz_answers" not in st.session_state: st.session_state.quiz_answers= {}
    if "_last_uploaded" not in st.session_state: st.session_state._last_uploaded= None


def get_doc():
    doc_id= st.session_state.get("doc_id")
    if not doc_id:
        return None
    return st.session_state.get("documents", {}).get(doc_id)


def _handle_upload(uploaded):
    name= uploaded.name
    if not ok_file(name):
        st.error("Unsupported file type. Please upload PDF, PPTX, or TXT.")
        return
    if uploaded.size> MAX_BYTES:
        st.error("File too large- maximum is 20 MB.")
        return

    ext= name.rsplit(".", 1)[1].lower()
    did= uuid.uuid4().hex #a unique id is created, so 2 files with same name won't collide
    path= os.path.join(UPLOAD_DIR, f"{did}_{name}")

    with open(path, "wb") as f:
        f.write(uploaded.getvalue())

    try:
        text = read_file(path, ext)
        #read_file returns all the text as a string 
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return
    finally:
        if os.path.exists(path):
            os.remove(path)

    if not text:
        st.error("No readable text found in that file.")
        return

    st.session_state.documents[did] = {
        "filename": name, "text": text, "chunks": chunk(text),
        "last_summary": None, "current_quiz": None,
        "last_quiz_results": None, "qna_history": [],
        "socratic_history": [], "flashcards": {},
        "concept_graph_svg": None, "quiz_history": [],
    }
    st.session_state.doc_id = did
    st.session_state.page = "summarizer"
    st.session_state.quiz_taking= False
    st.session_state.quiz_answers = {}
    st.success(f"Uploaded {name}")
    st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("## Study Buddy")

        doc= get_doc()
        if doc:
            st.caption(f"{doc['filename'][:28]}{'…' if len(doc['filename']) > 28 else ''}")

        uploaded = st.file_uploader(
            "Upload file",
            type=["pdf", "pptx", "txt"],
            label_visibility="collapsed",
        )
        if uploaded:
            last = st.session_state._last_uploaded
            if last != (uploaded.name, uploaded.size):
                st.session_state._last_uploaded = (uploaded.name, uploaded.size)
                _handle_upload(uploaded)

        st.divider()
        pages = [
            ("summarizer", " Summarizer"),
            ("quiz",       "Quiz Generator"),
            ("qna",        "Q&A Chat"),
            ("socratic",   "Socratic Tutor"),
            ("flashcards", "Flashcards"),
            ("graph",      "Concept Graph"),
            ("analytics",  "Analytics"),
        ]
        for key, label in pages:
            if st.button(label, key=f"nav_{key}",use_container_width=True,
                         type="primary" if st.session_state.page == key else "secondary"):
                st.session_state.page = key
                st.rerun()


def main():
    st.set_page_config(
        page_title="Study Buddy",
        page_icon="!",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    render_sidebar()
    doc    = get_doc()
    doc_id = st.session_state.get("doc_id")

    if not doc:
        st.title("Welcome to Study Buddy")
        st.write("Upload your notes — PDF, PPTX, or TXT — using the sidebar to get started.")
        return

    st.title("File loaded!")


if __name__ == "__main__":
    main()