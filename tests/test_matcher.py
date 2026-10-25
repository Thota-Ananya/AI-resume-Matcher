"""Tests for src/matcher.py."""

import pytest

from src.matcher import (
    analyze_match,
    calculate_similarity,
    get_keyword_overlap,
    interpret_score,
    preprocess_text,
)
from src.skill_extractor import load_skills

RESUME = "Python developer with Pandas, scikit-learn and SQL experience building machine learning models."
RELATED_JOB = "We need a Python developer experienced with machine learning, Pandas and SQL databases."
UNRELATED_JOB = "Looking for a chef to prepare fresh pasta, manage the kitchen and order seasonal vegetables."


def test_identical_texts_score_100():
    assert calculate_similarity(RESUME, RESUME) == 100.0


def test_related_text_scores_higher_than_unrelated():
    assert calculate_similarity(RESUME, RELATED_JOB) > calculate_similarity(RESUME, UNRELATED_JOB)


def test_score_is_within_0_and_100():
    score = calculate_similarity(RESUME, RELATED_JOB)
    assert 0.0 <= score <= 100.0


def test_completely_different_vocabulary_scores_zero():
    assert calculate_similarity("alpha beta gamma delta", "zebra yacht xylophone walrus") == 0.0


def test_empty_resume_raises_value_error():
    with pytest.raises(ValueError):
        calculate_similarity("", RELATED_JOB)


def test_empty_job_description_raises_value_error():
    with pytest.raises(ValueError):
        calculate_similarity(RESUME, "")


def test_whitespace_only_input_raises_value_error():
    with pytest.raises(ValueError):
        calculate_similarity("   \n\t ", RELATED_JOB)


def test_non_string_input_raises_type_error():
    with pytest.raises(TypeError):
        calculate_similarity(None, RELATED_JOB)
    with pytest.raises(TypeError):
        calculate_similarity(RESUME, 123)


def test_only_stop_words_returns_zero_instead_of_crashing():
    assert calculate_similarity("the and of to", "is it a the") == 0.0


def test_preprocess_removes_urls_and_emails_and_lowercases():
    cleaned = preprocess_text("Contact ME at jane@example.com or https://example.com/x  NOW")
    assert cleaned == "contact me at or now"


def test_interpret_score_labels():
    assert interpret_score(45) == "Strong match"
    assert interpret_score(20) == "Good match"
    assert interpret_score(10) == "Partial match"
    assert interpret_score(2) == "Low match"


def test_keyword_overlap_splits_shared_and_job_only():
    overlap = get_keyword_overlap("python pandas", "python pandas kubernetes docker")
    shared = {term for term, _ in overlap["shared"]}
    job_only = {term for term, _ in overlap["job_only"]}
    assert {"python", "pandas"} <= shared
    assert {"kubernetes", "docker"} <= job_only


def test_analyze_match_returns_complete_result():
    result = analyze_match(RESUME, RELATED_JOB + " Docker is a plus.", load_skills())
    for key in ("score", "label", "matched", "missing", "extra", "skill_coverage", "keywords"):
        assert key in result
    assert "Python" in result["matched"]
    assert "Docker" in result["missing"]
    assert 0.0 <= result["skill_coverage"] <= 100.0
