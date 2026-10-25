"""Dictionary-based skill extraction and skill-gap analysis.

Skills are looked up in a configurable JSON file (``data/skills.json``) with the
structure ``{category: {skill_name: [aliases, ...]}}``. This is plain keyword
matching, not machine learning.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_SKILLS_PATH = Path(__file__).resolve().parent.parent / "data" / "skills.json"


class SkillDatabaseError(ValueError):
    """Raised when the skills JSON file is missing or has the wrong structure."""


def validate_skills_db(skills_db: object) -> dict[str, dict[str, list[str]]]:
    """Check the structure of a skills dictionary and return it."""
    if not isinstance(skills_db, dict) or not skills_db:
        raise SkillDatabaseError("The skills database must be a non-empty JSON object.")
    for category, skills in skills_db.items():
        if not isinstance(skills, dict):
            raise SkillDatabaseError(f"Category '{category}' must map skill names to alias lists.")
        for skill, aliases in skills.items():
            if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
                raise SkillDatabaseError(f"Skill '{skill}' must have a list of string aliases.")
    return skills_db


def load_skills(path: str | Path | None = None) -> dict[str, dict[str, list[str]]]:
    """Load and validate the skills dictionary from JSON."""
    file_path = Path(path) if path else DEFAULT_SKILLS_PATH
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise SkillDatabaseError(f"Skills file not found: {file_path.name}") from exc
    except json.JSONDecodeError as exc:
        raise SkillDatabaseError(f"Skills file is not valid JSON: {exc}") from exc
    return validate_skills_db(data)


def _alias_pattern(alias: str) -> re.Pattern:
    """Whole-word, case-insensitive pattern.

    The lookarounds treat letters, digits, '+' and '#' as part of a word, so
    'java' does not match inside 'javascript' and 'sql' does not match inside
    'postgresql', while 'c++' and 'c#' still work.
    """
    return re.compile(
        r"(?<![A-Za-z0-9+#])" + re.escape(alias.strip()) + r"(?![A-Za-z0-9+#])",
        re.IGNORECASE,
    )


def extract_skills(text: str, skills_db: dict) -> list[str]:
    """Return the sorted list of skills from ``skills_db`` found in ``text``."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    validate_skills_db(skills_db)
    normalised = re.sub(r"\s+", " ", text)
    if not normalised.strip():
        return []

    found = set()
    for skills in skills_db.values():
        for skill, aliases in skills.items():
            # Only explicit aliases are used, so 'Go' or 'R' never match ordinary words.
            candidates = set(aliases) or {skill}
            if any(alias.strip() and _alias_pattern(alias).search(normalised) for alias in candidates):
                found.add(skill)
    return sorted(found, key=str.lower)


def skill_category_map(skills_db: dict) -> dict[str, str]:
    """Map each skill name to its category."""
    validate_skills_db(skills_db)
    return {skill: category for category, skills in skills_db.items() for skill in skills}


def group_by_category(skills: list[str], skills_db: dict) -> dict[str, list[str]]:
    """Group a list of skills by category (unknown skills go under 'Other')."""
    mapping = skill_category_map(skills_db)
    grouped: dict[str, list[str]] = {}
    for skill in skills:
        grouped.setdefault(mapping.get(skill, "Other"), []).append(skill)
    return {category: sorted(items, key=str.lower) for category, items in grouped.items()}


def find_missing_skills(resume_skills: list[str], job_skills: list[str]) -> list[str]:
    """Skills required by the job that the resume does not mention."""
    resume_set = set(resume_skills)
    return sorted((s for s in set(job_skills) if s not in resume_set), key=str.lower)


def compare_skills(resume_skills: list[str], job_skills: list[str]) -> dict:
    """Compare two skill lists.

    Returns matched, missing, extra (resume-only) skills and the skill coverage
    percentage (share of the job's skills found in the resume; 0.0 when the job
    lists no recognised skills).
    """
    resume_set, job_set = set(resume_skills), set(job_skills)
    matched = sorted(resume_set & job_set, key=str.lower)
    missing = find_missing_skills(resume_skills, job_skills)
    extra = sorted(resume_set - job_set, key=str.lower)
    coverage = round(100.0 * len(matched) / len(job_set), 1) if job_set else 0.0
    return {"matched": matched, "missing": missing, "extra": extra, "coverage": coverage}
