"""Build the downloadable CSV report."""

from __future__ import annotations

import pandas as pd

from src.skill_extractor import group_by_category

REPORT_COLUMNS = ["Section", "Item", "Details"]


def _safe_cell(value: object) -> str:
    """Neutralise spreadsheet formulas (CSV injection) in text cells."""
    text = str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


def build_report_dataframe(
    analysis: dict,
    recommendations: list[dict],
    skills_db: dict,
    job_title: str = "",
) -> pd.DataFrame:
    """Return a long-format table: summary, skill analysis and recommendations."""
    rows: list[tuple[str, str, str]] = [
        ("Summary", "Job title", job_title or "Not provided"),
        ("Summary", "Match score (TF-IDF cosine similarity, %)", f"{analysis['score']:.2f}"),
        ("Summary", "Match label", analysis["label"]),
        ("Summary", "Skill coverage (% of job skills found in resume)", f"{analysis['skill_coverage']:.1f}"),
        ("Summary", "Matched skills", str(len(analysis["matched"]))),
        ("Summary", "Missing skills", str(len(analysis["missing"]))),
    ]
    for status, key in (("Matched", "matched"), ("Missing", "missing"), ("Extra (resume only)", "extra")):
        for category, skills in group_by_category(analysis[key], skills_db).items():
            for skill in skills:
                rows.append((f"Skills - {status}", skill, category))
    for rec in recommendations:
        rows.append((f"Suggestion ({rec['priority']}, rule-based)", rec["area"], rec["suggestion"]))

    return pd.DataFrame(
        [(_safe_cell(a), _safe_cell(b), _safe_cell(c)) for a, b, c in rows],
        columns=REPORT_COLUMNS,
    )


def report_to_csv_bytes(report: pd.DataFrame) -> bytes:
    """Encode as UTF-8 with BOM so Excel on Windows opens it correctly."""
    return report.to_csv(index=False).encode("utf-8-sig")
