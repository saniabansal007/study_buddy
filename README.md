# Study Buddy

  Study Buddy turns any `PDF`, `PPTX`, or `TXT` file into summaries, quizzes, flashcards, a **RAG**-powered Q&A chat, Socratic tutor, a concept dependency graph, and learning analytics. 
  Everything runs through your own `Hugging Face` token. Your notes never leave your machine.

---

## Features

- Notes Summarizer \
  Generate short, medium, or detailed summaries of your uploaded notes instantly.

- Quiz Generator \
  Create mcq's at easy, medium, or hard difficulty. Pick how many questions, take the quiz interactively, and get instant results.

- Q&A Chat \
  Ask questions from your notes. Powered by RAG (Retrieval-Augmented Generation): it gives answers based on the actual content of your document, no hallucination. 

- Socratic Tutor \
  The tutor doesn't give answers, instead it asks you questions from your notes. 

- Flashcards with SM-2 \
  Generate flashcards and review them with the SM-2 spaced repetition algorithm. Cards you struggle with come back sooner. Easy cards are pushed further out. Intervals grow automatically with each correct review.

- Concept Dependency Graph \
  Extract 8-12 key concepts from your notes and render them as an interactive graph showing their relationships. Foundational concepts are highlighted in gold.

- Learning Analytics \
  Track exam readiness, quiz accuracy by topic, weak topics (under 60%), and flashcard interval growth rendered as SVG charts.

---

## Folder structure

```
study_buddy/
├── app.py            # Entry point: page config, session state, sidebar, routing
├── utils.py          # All shared logic:
│                     #   LLM (load_llm, run_prompt, llm_invoke)
│                     #   RAG (load_embeddings, _ensure_indexed, retrieve, rag_answer)
│                     #   File reading (read_file, ok_file, chunk)
│                     #   Prompts (SUMMARIZE, QUIZ, FLASHCARD, GRAPH, SOCRATIC)
│                     #   SM-2 algorithm
│                     #   SVG chart helpers
├── summarizer.py     # Notes Summarizer page
├── quiz.py           # Quiz Generator (generate quiz -> take quiz -> results state machine)
├── chat.py           # Q&A Chat + Socratic Tutor
├── flashcards.py     # Flashcards with SM-2 spaced repetition
├── analytics.py      # Concept Graph + Learning Analytics
├── uploads/          # Temp folder: files deleted immediately after reading
└── chroma_db/        # Persisted Chroma vector store (auto-created)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | Qwen/Qwen2.5-7B-Instruct via Hugging Face Inference API |
| LLM Framework | LangChain (ChatHuggingFace, ChatPromptTemplate) |
| Embeddings | all-MiniLM-L6-v2 via sentence-transformers |
| Vector Store | Chroma (persisted locally) |
| PDF Reading | pypdf | 
| PPTX Reading | python-pptx |
| Graph Layout | networkx (spring layout + betweenness centrality) |
| Charts | SVG (zero charting dependencies) |
| Spaced Repetition | SM-2 algorithm (implemented from scratch) |

---

## User instructions

### 1. Clone the repo
```bash
git clone https://github.com/saniabansal007/study_buddy.git
cd study_buddy
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Hugging Face token
Create a `.env` file in the project root:
```
HF_TOKEN=hf_your_token_here
```
Get your token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). The model used is `Qwen/Qwen2.5-7B-Instruct` : make sure **Inference API** access is enabled on your account.

### 5. Run
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

---
