import os
import pypdf
from pptx import Presentation

import streamlit as st
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Constants
BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CHUNK_SZ= 400
OVERLAP= 80
MAX_BYTES = 20 * 1024 * 1024   # 20 MB
MAX_CHARS = 10_000
HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"
HF_TOKEN = os.environ.get("HF_TOKEN")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Returns true if the file has a supported extension
def ok_file(name: str)->bool:
    return "." in name and name.rsplit(".", 1)[1].lower() in {"pdf","pptx","txt"}


# File reading
def read_file(path: str, ext: str)->str:
    if ext== "pdf":
        reader= pypdf.PdfReader(path) 
        #reads all the pages and reader.pages returns [page1, page2, ...]

        return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    
    elif ext== "pptx":
        prs= Presentation(path)
        parts= []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    parts.append(shape.text_frame.text)
        return "\n\n".join(parts).strip()
    
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()


# Chunking 
def chunk(text: str)->list[str]:
    chunks, start= [], 0
    while start<len(text):
        end= start+ CHUNK_SZ
        chunks.append(text[start:end])
        start+= CHUNK_SZ- OVERLAP

    #using c.strip() discards the empty strings 
    return [c for c in chunks if c.strip()]

@st.cache_resource
def load_llm():
    try:
        endpoint = HuggingFaceEndpoint(
            repo_id=HF_MODEL,
            huggingfacehub_api_token=HF_TOKEN,
            max_new_tokens=1500,
            temperature=0.3,
        )
        llm = ChatHuggingFace(llm=endpoint)
        return llm
    except Exception as e:
        return None


def run_prompt(prompt_template: ChatPromptTemplate, variables: dict, max_tokens: int = 1500) -> str:
    chat_llm = load_llm()
    if chat_llm is None:
        raise RuntimeError("HF_TOKEN not set or LLM failed to initialise.")
    messages = prompt_template.format_messages(**variables)
    lc_msgs  = []
    for m in messages:
        if m.type == "system":
            lc_msgs.append(SystemMessage(content=m.content))
        else:
            lc_msgs.append(HumanMessage(content=m.content))
    return chat_llm.invoke(lc_msgs).content


SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("human",
     "Summarize the material below in {instr}. Use short headings and bullet points.\n\n"
     "MATERIAL:\n{text}")
])