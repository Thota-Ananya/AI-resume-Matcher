"""Tests for src/recommendations.py and src/report.py."""

import io

import pandas as pd

from src.matcher import analyze_match
from src.recommendations import RULE_BASED_NOTE, generate_recommendations
from src.report import build_report_dataframe, report_to_csv_bytes
from src.skill_extractor import load_skills

SKILLS = load_skills()
JOB = "Python developer needed with Docker, AWS and Kubernetes experience for cloud services work."
SHORT_RESUME = "I know Python."


def test_missing_skills_produce_high_priority_suggestion():
    analysis = analyze_match(SHORT_RESUME, JOB, SKILLS)
    recs = generate_recommendations(analysis, SHORT_RESUME, SKILLS)
    assert recs[0]["priority"] == "High"
    text = " ".join(r["suggestion"] for r in recs)
    assert "Docker" in text and "AWS" in text


def test_short_resume_gets_length_suggestion():
    analysis = analyze_match(SHORT_RESUME, JOB, SKILLS)
    areas = [r["area"] for r in generate_recommendations(analysis, SHORT_RESUME, SKILLS)]
    assert "Length" in areas


def test_every_recommendation_has_required_fields():
    analysis = analyze_match(SHORT_RESUME, JOB, SKILLS)
    for rec in generate_recommendations(analysis, SHORT_RESUME, SKILLS):
        assert rec["priority"] in {"High", "Medium", "Low"}
        assert rec["area"] and rec["suggestion"]


def test_rule_based_note_is_honest():
    assert "rule-based" in RULE_BASED_NOTE.lower()
    assert "not by an ai model" in RULE_BASED_NOTE.lower()


def test_report_contains_summary_and_skills_and_round_trips_as_csv():
    analysis = analyze_match(SHORT_RESUME, JOB, SKILLS)
    recs = generate_recommendations(analysis, SHORT_RESUME, SKILLS)
    report = build_report_dataframe(analysis, recs, SKILLS, "Cloud Dev")
    assert list(report.columns) == ["Section", "Item", "Details"]
    assert "Skills - Missing" in set(report["Section"])
    reloaded = pd.read_csv(io.BytesIO(report_to_csv_bytes(report)), encoding="utf-8-sig")
    assert len(reloaded) == len(report)


def test_report_neutralises_spreadsheet_formulas():
    analysis = analyze_match(SHORT_RESUME, JOB, SKILLS)
    report = build_report_dataframe(analysis, [], SKILLS, "=HYPERLINK(\"http://evil\")")
    job_title_row = report[report["Item"] == "Job title"].iloc[0]
    assert job_title_row["Details"].startswith("'=")
