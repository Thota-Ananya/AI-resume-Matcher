"""Resume <-> job description matching with TF-IDF and cosine similarity.

How it works (no trained model, no external AI service):
1. Both texts are lower-cased and cleaned.
2. A TF-IDF vectoriser turns each text into a vector of weighted word and
   two-word-phrase counts.
3. Cosine similarity measures the angle between the two vectors
   (0 = no shared vocabulary, 1 = identical wording).
"""

from __future__ import annotations

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.skill_extractor import compare_skills, extract_skills

# Keeps tokens such as "c++", "c#" and "node.js" intact.
TOKEN_PATTERN = r"(?u)[a-z][a-z0-9+#]*(?:\.[a-z0-9]+)*"


def preprocess_text(text: str) -> str:
    """Lower-case text, drop URLs and e-mail addresses, collapse whitespace."""
    if not isinstance(text, str):
        raise TypeError("Text must be a string.")
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+\.\S+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _prepare_pair(resume_text: str, job_text: str) -> tuple[str, str]:
    """Validate and preprocess the two inputs."""
    for name, value in (("Resume", resume_text), ("Job description", job_text)):
        if not isinstance(value, str):
            raise TypeError(f"{name} text must be a string.")
        if not value.strip():
            raise ValueError(f"{name} text is empty.")
    return preprocess_text(resume_text), preprocess_text(job_text)


def calculate_similarity(resume_text: str, job_text: str) -> float:
    """Return the TF-IDF cosine similarity of two texts as a 0-100 percentage."""
    resume, job = _prepare_pair(resume_text, job_text)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
        token_pattern=TOKEN_PATTERN,
    )
    try:
        matrix = vectorizer.fit_transform([resume, job])
    except ValueError:  # "empty vocabulary": e.g. only stop words or numbers
        return 0.0
    score = float(cosine_similarity(matrix[0], matrix[1])[0, 0])
    return round(min(max(score, 0.0), 1.0) * 100.0, 2)


def interpret_score(score: float) -> str:
    """Human-readable label for a similarity percentage.

    Raw TF-IDF similarity between a resume and a job post is usually low even for
    a good fit (typically 5-35%), so these thresholds are deliberately modest.
    They are rough guides chosen by testing on the bundled sample data.
    """
    if score >= 30:
        return "Strong match"
    if score >= 15:
        return "Good match"
    if score >= 7:
        return "Partial match"
    return "Low match"


def get_keyword_overlap(resume_text: str, job_text: str, top_n: int = 12) -> dict:
    """Find the most heavily weighted job-description words.

    Returns ``{"shared": [(word, weight), ...], "job_only": [(word, weight), ...]}``
    where "shared" words also appear in the resume and "job_only" words do not.
    """
    resume, job = _prepare_pair(resume_text, job_text)
    vectorizer = TfidfVectorizer(stop_words="english", token_pattern=TOKEN_PATTERN)
    try:
        matrix = vectorizer.fit_transform([resume, job])
    except ValueError:
        return {"shared": [], "job_only": []}

    terms = vectorizer.get_feature_names_out()
    resume_weights = matrix[0].toarray().ravel()
    job_weights = matrix[1].toarray().ravel()

    shared, job_only = [], []
    for term, r_w, j_w in zip(terms, resume_weights, job_weights):
        if j_w <= 0:
            continue
        (shared if r_w > 0 else job_only).append((str(term), round(float(j_w), 4)))
    shared.sort(key=lambda item: item[1], reverse=True)
    job_only.sort(key=lambda item: item[1], reverse=True)
    return {"shared": shared[:top_n], "job_only": job_only[:top_n]}


def analyze_match(resume_text: str, job_text: str, skills_db: dict) -> dict:
    """Run the complete analysis and return a dictionary of results."""
    score = calculate_similarity(resume_text, job_text)
    resume_skills = extract_skills(resume_text, skills_db)
    job_skills = extract_skills(job_text, skills_db)
    comparison = compare_skills(resume_skills, job_skills)
    return {
        "score": score,
        "label": interpret_score(score),
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "matched": comparison["matched"],
        "missing": comparison["missing"],
        "extra": comparison["extra"],
        "skill_coverage": comparison["coverage"],
        "keywords": get_keyword_overlap(resume_text, job_text),
    }
