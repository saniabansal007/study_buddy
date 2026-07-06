import os
import pypdf
from pptx import Presentation

# Constants
BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CHUNK_SIZE= 400
OVERLAP= 80
MAX_BYTES = 20 * 1024 * 1024   # 20 MB
MAX_CHARS = 10_000
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
        end= start+ CHUNK_SIZE
        chunks.append(text[start:end])
        start+= CHUNK_SIZE- OVERLAP

    #using c.strip() discards the empty strings 
    return [c for c in chunks if c.strip()]