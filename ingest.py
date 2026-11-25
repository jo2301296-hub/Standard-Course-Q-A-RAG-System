import os
import re
import pandas as pd
from pypdf import PdfReader
from docx import Document
import chromadb
from sentence_transformers import SentenceTransformer

DATA_DIR = "data"
DB_DIR = "chroma_db"
COLLECTION = "courses"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 800
OVERLAP = 150


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)        # مسافات زيادة
    text = re.sub(r"\n\s*\n+", "\n\n", text)   # أسطر فاضية زيادة
    return text.strip()


def extract(path: str):
    """بترجع list من (text, page) - الصفحة None لو الملف مفيهوش صفحات"""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(path)
        return [(p.extract_text() or "", i + 1) for i, p in enumerate(reader.pages)]
    if ext == ".docx":
        doc = Document(path)
        return [("\n".join(p.text for p in doc.paragraphs), None)]
    if ext == ".txt":
        with open(path, encoding="utf-8", errors="ignore") as f:
            return [(f.read(), None)]
    if ext == ".csv":
        df = pd.read_csv(path)
        rows = ["; ".join(f"{c}: {row[c]}" for c in df.columns) for _, row in df.iterrows()]
        return [("\n".join(rows), None)]
    return []


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP):
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):                       # حاول تقطع عند مسافة مش في نص كلمة
            cut = text.rfind(" ", start + size // 2, end)
            if cut != -1:
                end = cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def main():
    docs, metas, ids = [], [], []

    for course in sorted(os.listdir(DATA_DIR)):
        course_dir = os.path.join(DATA_DIR, course)
        if not os.path.isdir(course_dir):
            continue
        for fname in sorted(os.listdir(course_dir)):
            path = os.path.join(course_dir, fname)
            for text, page in extract(path):
                text = clean_text(text)
                for i, chunk in enumerate(chunk_text(text)):
                    docs.append(chunk)
                    metas.append({"course": course, "file": fname, "page": page or 0})
                    ids.append(f"{course}-{fname}-{page or 0}-{i}")
            print(f"OK: {course}/{fname}")

    print(f"Total chunks: {len(docs)}")

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(docs, normalize_embeddings=True, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection(COLLECTION)      # إعادة بناء من الصفر
    except Exception:
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    B = 500                                       # إضافة على دفعات
    for i in range(0, len(docs), B):
        col.add(ids=ids[i:i+B], documents=docs[i:i+B],
                metadatas=metas[i:i+B], embeddings=embeddings[i:i+B])
    print("Done.")


if __name__ == "__main__":
    main()