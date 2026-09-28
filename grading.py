"""
Similarity / grading algorithms.

Each function takes two plain-text strings (reference answer, student
answer) and returns a similarity score between 0.0 and 1.0. Nothing in
here talks to the database - that orchestration lives in
grading_service.py.
"""

import re

import numpy as np
from gensim.models import Word2Vec
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _tokenize(text):
    """Very small, dependency-free tokenizer: lowercase words only."""
    if not text:
        return []
    return re.findall(r"[a-zA-Z]+", text.lower())


# ---------------------------------------------------------------------------
# 1. Jaccard similarity - overlap of unique words
# ---------------------------------------------------------------------------
def jaccard_similarity(reference_text, student_text):
    ref_words = set(_tokenize(reference_text))
    stu_words = set(_tokenize(student_text))

    if not stu_words:
        return 0.0

    union = ref_words | stu_words
    if not union:
        return 0.0

    intersection = ref_words & stu_words
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# 2. TF-IDF + cosine similarity
# ---------------------------------------------------------------------------
def tfidf_similarity(reference_text, student_text):
    if not student_text or not student_text.strip():
        return 0.0

    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([reference_text, student_text])
    except ValueError:
        # Happens if both texts end up empty after tokenizing (e.g. only
        # numbers/punctuation).
        return 0.0

    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return float(score)


# ---------------------------------------------------------------------------
# 3. Word2Vec similarity
#
# A production system would use a huge pretrained model (e.g. Google
# News, 1.6GB+). That's impractical to download for a college project,
# so instead we TRAIN A SMALL WORD2VEC MODEL ON THE FLY from the text
# you give it (the reference answer plus every student answer for that
# question). This is a well-known, accepted approach for small/local
# corpora and needs no download at all.
# ---------------------------------------------------------------------------
def _average_vector(tokens, model):
    vectors = [model.wv[t] for t in tokens if t in model.wv]
    if not vectors:
        return np.zeros(model.vector_size)
    return np.mean(vectors, axis=0)


def word2vec_similarity(reference_text, student_text, corpus_texts=None):
    """
    corpus_texts: extra sentences (e.g. every other student's answer to
    the same question) used only to give the on-the-fly model a bit more
    vocabulary to learn from. reference_text and student_text are always
    included automatically.
    """
    if not student_text or not student_text.strip():
        return 0.0

    sentences = [_tokenize(reference_text), _tokenize(student_text)]
    if corpus_texts:
        sentences += [_tokenize(t) for t in corpus_texts if t]

    sentences = [s for s in sentences if s]  # drop empty ones
    if len(sentences) < 2:
        return 0.0

    model = Word2Vec(
        sentences=sentences,
        vector_size=50,
        window=5,
        min_count=1,
        workers=1,
        epochs=50,
    )

    ref_vec = _average_vector(_tokenize(reference_text), model)
    stu_vec = _average_vector(_tokenize(student_text), model)

    if np.linalg.norm(ref_vec) == 0 or np.linalg.norm(stu_vec) == 0:
        return 0.0

    score = cosine_similarity([ref_vec], [stu_vec])[0][0]
    return float(max(0.0, score))


# ---------------------------------------------------------------------------
# 4. SBERT similarity (Sentence-BERT) - best semantic accuracy, but the
# heaviest dependency (downloads a ~90MB pretrained model the first
# time it runs).
# ---------------------------------------------------------------------------
_sbert_model = None


def _get_sbert_model():
    """Load the SBERT model once per server run and reuse it - loading
    it fresh on every request would be very slow."""
    global _sbert_model
    if _sbert_model is None:
        from sentence_transformers import SentenceTransformer

        _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sbert_model


def sbert_similarity(reference_text, student_text):
    if not student_text or not student_text.strip():
        return 0.0

    model = _get_sbert_model()
    embeddings = model.encode([reference_text, student_text])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(score)
