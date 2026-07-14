import re
from io import BytesIO

import streamlit as st
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _store():
    return st.session_state.setdefault("pdf_chunks", [])


def _split(text, size=900, overlap=160):
    text = re.sub(r"\s+", " ", text).strip()
    for start in range(0, len(text), size - overlap):
        yield text[start:start + size]


def add_pdf(upload):
    try:
        reader = PdfReader(BytesIO(upload.getvalue()))
        entries = []
        for page_number, page in enumerate(reader.pages, start=1):
            for chunk in _split(page.extract_text() or ""):
                if len(chunk) > 50:
                    entries.append({"text": chunk, "source": upload.name, "page": page_number})
        if not entries:
            return False, "No readable text was found. This may be a scanned PDF."
        _store().extend(entries)
        return True, f"Indexed {len(entries)} excerpts."
    except Exception as exc:
        return False, f"Couldn't read PDF: {exc}"


def retrieve_context(question, limit=4):
    entries = _store()
    if not entries:
        return "", []
    matrix = TfidfVectorizer(stop_words="english").fit_transform([item["text"] for item in entries] + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    selected = [entries[i] for i in scores.argsort()[-limit:][::-1] if scores[i] > .02]
    context = "\n\n".join(f"[{item['source']}, p. {item['page']}] {item['text']}" for item in selected)
    return context, [f"{item['source']} p. {item['page']}" for item in selected]


def get_document_names():
    return sorted({item["source"] for item in _store()})


def clear_documents():
    st.session_state["pdf_chunks"] = []
