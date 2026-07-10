from utils import load_llm

llm = load_llm()
print(type(llm))

from utils import run_prompt, SUMMARIZE_PROMPT

text = """
Machine learning is a field of AI.
It allows computers to learn from data.
"""

response = run_prompt(SUMMARIZE_PROMPT,{ "instr": "3 bullet points", "text": text })
print(response)