import os
import time
import chromadb
from sentence_transformers import SentenceTransformer

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ===== اختار: "groq" أو "openrouter" أو "gemini" أو "ollama" أو "claude" =====
PROVIDER = "groq"

# اسم الموديل لـ groq / openrouter (شوف الخطوة تحت عشان تجيب الاسم)
OPENAI_COMPAT = {
        "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "openai/gpt-oss-120b",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model": "ضع-اسم-الموديل-هنا",
    },
}

GEMINI_MODEL = "gemini-3.8-flash"
OLLAMA_MODEL = "qwen2.5:3b"
CLAUDE_MODEL = "claude-sonnet-5-5"

DB_DIR = "chroma_db"
COLLECTION = "courses"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_embedder = SentenceTransformer(EMBED_MODEL)
_col = chromadb.PersistentClient(path=DB_DIR).get_collection(COLLECTION)

SYSTEM_PROMPT = (
    "You are a course assistant. Answer the student's question ONLY using the "
    "provided context passages. If the answer is not in the context, say exactly: "
    "'I could not find this in the course materials.' "
    "Cite passages like [1], [2]. Reply in the same language as the question."
)


def list_courses():
    metas = _col.get(include=["metadatas"])["metadatas"]
    return sorted({m["course"] for m in metas})


def retrieve(question: str, course: str | None = None, k: int = 4):
    emb = _embedder.encode([question], normalize_embeddings=True).tolist()
    where = {"course": course} if course and course != "All" else None
    res = _col.query(query_embeddings=emb, n_results=k, where=where)
    return [
        {"text": t, "meta": m, "distance": d}
        for t, m, d in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def call_llm(user_prompt: str) -> str:
    if PROVIDER in OPENAI_COMPAT:                       # groq / openrouter
        from openai import OpenAI
        cfg = OPENAI_COMPAT[PROVIDER]
        if "ضع" in cfg["model"]:
            raise ValueError("حط اسم الموديل الحقيقي في OPENAI_COMPAT")
        client = OpenAI(base_url=cfg["base_url"], api_key=os.environ[cfg["key_env"]])
        last_err = None
        for attempt in range(3):
            try:
                r = client.chat.completions.create(
                    model=cfg["model"],
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": user_prompt}],
                    temperature=0.2,
                )
                return r.choices[0].message.content
            except Exception as e:
                last_err = e
                time.sleep(2 ** attempt)
        raise last_err

    if PROVIDER == "gemini":
        from google import genai
        from google.genai import types
        from google.genai.errors import ServerError
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        last_err = None
        for attempt in range(4):
            try:
                r = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                )
                return r.text
            except ServerError as e:
                last_err = e
                time.sleep(2 ** attempt)
        raise last_err

    if PROVIDER == "ollama":
        import ollama
        r = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": user_prompt}],
        )
        return r["message"]["content"]

    if PROVIDER == "claude":
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text

    raise ValueError(f"Unknown PROVIDER: {PROVIDER}")


def answer(question: str, course: str | None = None, k: int = 4):
    chunks = retrieve(question, course, k)
    if not chunks:
        return "I could not find this in the course materials.", []

    context = "\n\n".join(
        f"[{i+1}] (Course: {c['meta']['course']}, File: {c['meta']['file']}, "
        f"Page: {c['meta']['page'] or '-'})\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    text = call_llm(f"Context:\n{context}\n\nQuestion: {question}")
    return text, chunks