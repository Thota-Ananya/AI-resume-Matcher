"""Tests for src/skill_extractor.py."""

import json

import pytest

from src.skill_extractor import (
    SkillDatabaseError,
    compare_skills,
    extract_skills,
    find_missing_skills,
    group_by_category,
    load_skills,
)

SKILLS = load_skills()


def test_extracts_known_skills_case_insensitively():
    found = extract_skills("Experienced in PYTHON, sql and Docker.", SKILLS)
    assert {"Python", "SQL", "Docker"} <= set(found)


def test_empty_text_returns_empty_list():
    assert extract_skills("", SKILLS) == []
    assert extract_skills("   \n  ", SKILLS) == []


def test_non_string_text_raises_type_error():
    with pytest.raises(TypeError):
        extract_skills(None, SKILLS)


def test_java_is_not_detected_inside_javascript():
    found = extract_skills("I build websites with JavaScript.", SKILLS)
    assert "JavaScript" in found
    assert "Java" not in found


def test_sql_is_not_detected_inside_postgresql():
    found = extract_skills("Worked with PostgreSQL daily.", SKILLS)
    assert "PostgreSQL" in found
    assert "SQL" not in found


def test_special_character_skills_and_aliases():
    found = extract_skills("Wrote C++ and C# code; used Node.js, sklearn and k8s.", SKILLS)
    assert {"C++", "C#", "Node.js", "scikit-learn", "Kubernetes"} <= set(found)


def test_ordinary_words_do_not_trigger_go_or_r():
    found = extract_skills("Ready to go to market. R&D team player.", SKILLS)
    assert "Go" not in found
    assert "R" not in found


def test_multi_word_skill_with_extra_whitespace():
    assert "Machine Learning" in extract_skills("machine\n  learning projects", SKILLS)


def test_find_missing_skills():
    assert find_missing_skills(["Python", "SQL"], ["Python", "Docker", "AWS"]) == ["AWS", "Docker"]


def test_find_missing_skills_when_nothing_missing():
    assert find_missing_skills(["Python", "SQL", "Git"], ["Python", "SQL"]) == []


def test_compare_skills_coverage_and_sets():
    result = compare_skills(["Python", "Git"], ["Python", "SQL", "Docker", "AWS"])
    assert result["matched"] == ["Python"]
    assert result["missing"] == ["AWS", "Docker", "SQL"]
    assert result["extra"] == ["Git"]
    assert result["coverage"] == 25.0


def test_compare_skills_with_no_job_skills_gives_zero_coverage():
    assert compare_skills(["Python"], [])["coverage"] == 0.0


def test_group_by_category():
    grouped = group_by_category(["Python", "SQL", "Mystery"], SKILLS)
    assert grouped["Programming Languages"] == ["Python"]
    assert grouped["Databases"] == ["SQL"]
    assert grouped["Other"] == ["Mystery"]


def test_default_skills_file_loads():
    assert len(SKILLS) >= 5


def test_invalid_skills_structure_raises():
    with pytest.raises(SkillDatabaseError):
        extract_skills("python", {"Languages": ["python"]})
    with pytest.raises(SkillDatabaseError):
        extract_skills("python", {})


def test_missing_or_broken_skills_file_raises(tmp_path):
    with pytest.raises(SkillDatabaseError):
        load_skills(tmp_path / "does_not_exist.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(SkillDatabaseError):
        load_skills(broken)


def test_custom_skills_file_is_respected(tmp_path):
    path = tmp_path / "skills.json"
    path.write_text(json.dumps({"Hobbies": {"Chess": ["chess"]}}), encoding="utf-8")
    assert extract_skills("I love chess", load_skills(path)) == ["Chess"]
