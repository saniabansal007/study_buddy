import os, re, json
import pypdf
from pptx import Presentation

import streamlit as st
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from datetime import datetime, timedelta

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


SUMMARIZE_PROMPT= ChatPromptTemplate.from_messages([
    ("human",
     "Summarize the material below in {instr}. Use short headings and bullet points.\n\n"
     "MATERIAL:\n{text}")
])

def parse_json(raw: str):
    #Strip markdown fences the LLM wraps around JSON, then parse it.
    #Falls back to regex extraction if direct parsing fails.

    cleaned= re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        for pat in [r"\[[\s\S]*\]", r"\{[\s\S]*\}"]:
            m = re.search(pat, cleaned)
            if m:
                try:
                    return json.loads(m.group(0))
                except:
                    pass
        raise


QUIZ_PROMPT= ChatPromptTemplate.from_messages([
    ("human",
     "Create {n} multiple-choice questions at {difficulty} difficulty.\n\n"
     "Return ONLY valid JSON:\n"
     '[{{"question":"...","topic":"...","options":["A","B","C","D"],"correct_index":0,"explanation":"..."}}]\n\n'
     "MATERIAL:\n{text}")
])


def sm2(card: dict, q: int) -> dict:
    """
    SM-2 spaced repetition algorithm.
    q = quality of recall:
        0 = Again (complete blank)
        3 = Hard  (correct but difficult)
        4 = Good  (correct with some effort)
        5 = Easy  (perfect recall)
    """
    q = max(0, min(5, q))          # clamp to valid range
    if q >= 3:                     # correct answer
        rep = card["repetitions"]
        if   rep == 0: iv = 1      # first time correct: review tomorrow
        elif rep == 1: iv = 6      # second time: review in 6 days
        else:          iv = round(card["interval"] * card["ease_factor"])
        card["repetitions"] += 1
    else:                          # wrong answer: reset
        card["repetitions"] = 0
        iv = 1
    ef= card["ease_factor"] + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    card["ease_factor"] = round(max(1.3, ef), 3)   # never drop below 1.3
    card["interval"]    = iv
    card["next_review"] = (datetime.now() + timedelta(days=iv)).isoformat()
    card["history"].append({
        "quality":  q,
        "correct":  q >= 3,
        "interval": iv,
        "ts":       datetime.now().isoformat(),
    })
    return card


FLASHCARD_PROMPT= ChatPromptTemplate.from_messages([
    ("human",
     "Create {n} flashcard Q&A pairs from the material.\n\n"
     "Return ONLY valid JSON:\n"
     '[{{"front":"question","back":"detailed answer","topic":"topic name"}}]\n\n'
     "MATERIAL:\n{text}")
])