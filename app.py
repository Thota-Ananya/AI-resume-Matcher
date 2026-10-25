"""AI Resume Analyzer & Job Matcher - Streamlit web app.

Run with:  python -m streamlit run app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.charts import BAD, GOOD, category_chart, gauge_chart, keyword_chart
from src.matcher import analyze_match
from src.pdf_parser import PDFParsingError, extract_text_from_pdf
from src.recommendations import RULE_BASED_NOTE, generate_recommendations
from src.report import build_report_dataframe, report_to_csv_bytes
from src.skill_extractor import SkillDatabaseError, group_by_category, load_skills

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_JOBS_PATH = BASE_DIR / "data" / "sample_job_descriptions.json"
SAMPLE_RESUME_PATH = BASE_DIR / "sample_data" / "sample_resume.txt"
MIN_WORDS = 20  # below this, a similarity score is not meaningful
CUSTOM_OPTION = "- Paste my own job description -"

st.set_page_config(page_title="AI Resume Analyzer & Job Matcher", page_icon="📄", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1200px;}
    .hero {padding: 1.2rem 1.5rem; border-radius: 14px; margin-bottom: 1rem;
           background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: white;}
    .hero h1 {color: white; margin: 0; font-size: 2rem;}
    .hero p {margin: .3rem 0 0 0; opacity: .92;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------- data loading
@st.cache_data
def get_skills_db() -> dict:
    return load_skills()


@st.cache_data
def get_sample_jobs() -> list[dict]:
    with open(SAMPLE_JOBS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


@st.cache_data
def get_sample_resume() -> str:
    return SAMPLE_RESUME_PATH.read_text(encoding="utf-8")


def apply_sample_job() -> None:
    """Callback: copy the chosen sample job description into the text area."""
    choice = st.session_state.get("sample_choice", CUSTOM_OPTION)
    for job in get_sample_jobs():
        if job["title"] == choice:
            st.session_state["job_text"] = job["description"]
            return
    st.session_state["job_text"] = ""


# ------------------------------------------------------------------ rendering
def chips(skills: list[str]) -> str:
    return " ".join(f"`{skill}`" for skill in skills) if skills else "_None_"


def render_results(result: dict, skills_db: dict) -> None:
    analysis, recommendations = result["analysis"], result["recommendations"]

    st.header("Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Match score", f"{analysis['score']:.1f}%")
    c2.metric("Verdict", analysis["label"])
    c3.metric("Skill coverage", f"{analysis['skill_coverage']:.0f}%")
    c4.metric("Skills matched", f"{len(analysis['matched'])} / {len(analysis['job_skills'])}")
    st.caption("Match score = TF-IDF cosine similarity of the two texts. "
               "Skill coverage = share of the job's recognised skills found in your resume. "
               "Raw text-similarity scores are usually low (often 5-35%) even for good fits, "
               "so read the score together with skill coverage.")

    left, right = st.columns(2)
    left.plotly_chart(gauge_chart(analysis["score"]))
    figure = category_chart(analysis, skills_db)
    if figure is not None:
        right.plotly_chart(figure)
    else:
        right.info("No skills from the skill dictionary were found in the job description.")

    st.subheader("Skill gap analysis")
    matched_col, missing_col = st.columns(2)
    with matched_col:
        st.markdown("#### ✅ Matched skills")
        for category, skills in group_by_category(analysis["matched"], skills_db).items():
            st.markdown(f"**{category}:** {chips(skills)}")
        if not analysis["matched"]:
            st.markdown("_None_")
    with missing_col:
        st.markdown("#### ❌ Missing skills")
        for category, skills in group_by_category(analysis["missing"], skills_db).items():
            st.markdown(f"**{category}:** {chips(skills)}")
        if not analysis["missing"]:
            st.markdown("_None - your resume covers every recognised job skill._")
    if analysis["extra"]:
        with st.expander("Other skills on your resume that this job does not mention"):
            st.markdown(chips(analysis["extra"]))

    st.subheader("Keyword analysis")
    k1, k2 = st.columns(2)
    shared_fig = keyword_chart(analysis["keywords"]["shared"], "Important job keywords found in your resume", GOOD)
    missing_fig = keyword_chart(analysis["keywords"]["job_only"], "Important job keywords not in your resume", BAD)
    if shared_fig is not None:
        k1.plotly_chart(shared_fig)
    if missing_fig is not None:
        k2.plotly_chart(missing_fig)

    st.subheader("Resume improvement suggestions")
    st.info("🧰 **Rule-based suggestions.** " + RULE_BASED_NOTE)
    icons = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}
    for rec in recommendations:
        st.markdown(f"{icons[rec['priority']]} **{rec['area']}** ({rec['priority']} priority)  \n{rec['suggestion']}")

    report = build_report_dataframe(analysis, recommendations, skills_db, result["job_title"])
    st.download_button(
        "⬇️ Download CSV report",
        data=report_to_csv_bytes(report),
        file_name="resume_match_report.csv",
        mime="text/csv",
    )
    with st.expander("How is the score calculated?"):
        st.markdown(
            "- Both texts are cleaned and converted into **TF-IDF vectors** (weighted words and "
            "two-word phrases).\n"
            "- The **cosine similarity** between the vectors is shown as a percentage.\n"
            "- This is a classic statistical technique - **there is no trained machine-learning "
            "model and no external AI service**. It measures shared wording, not true "
            "qualification, so use it as a guide only."
        )


# ------------------------------------------------------------------------ main
def main() -> None:
    st.markdown(
        '<div class="hero"><h1>📄 AI Resume Analyzer &amp; Job Matcher</h1>'
        "<p>Compare your resume with a job description, find skill gaps and get practical, "
        "rule-based improvement ideas.</p></div>",
        unsafe_allow_html=True,
    )

    try:
        skills_db = get_skills_db()
        sample_jobs = get_sample_jobs()
        sample_resume = get_sample_resume()
    except (SkillDatabaseError, OSError, json.JSONDecodeError) as exc:
        st.error(f"Could not load the project data files: {exc}")
        st.stop()

    with st.sidebar:
        st.header("About")
        st.write("Uses TF-IDF + cosine similarity and a configurable skill dictionary. "
                 "No API keys, no paid services.")
        st.subheader("🔒 Privacy")
        st.write("Your resume is processed in memory while the app runs. "
                 "It is never saved to disk or sent to an external service.")
        st.caption("All sample people, companies and jobs are fictional.")

    col_resume, col_job = st.columns(2)
    with col_resume:
        st.subheader("1. Your resume")
        uploaded = st.file_uploader("Upload a text-based PDF resume", type=["pdf"])
        use_sample = st.checkbox("Use the sample resume instead")
    with col_job:
        st.subheader("2. Job description")
        st.selectbox(
            "Try a fictional sample job (optional)",
            [CUSTOM_OPTION] + [job["title"] for job in sample_jobs],
            key="sample_choice",
            on_change=apply_sample_job,
        )
        st.text_area("Paste the job description", key="job_text", height=260,
                     placeholder="Paste the full job posting here...")

    if st.button("🔍 Analyze match", type="primary"):
        job_text = st.session_state.get("job_text", "")
        job_title = st.session_state.get("sample_choice", CUSTOM_OPTION)
        job_title = "" if job_title == CUSTOM_OPTION else job_title

        resume_text = None
        if use_sample:
            resume_text = sample_resume
        elif uploaded is not None:
            try:
                resume_text = extract_text_from_pdf(uploaded.getvalue())
            except PDFParsingError as exc:
                st.error(f"Could not read the resume: {exc}")
        else:
            st.warning("Please upload a PDF resume or tick 'Use the sample resume'.")

        if resume_text is not None:
            if not job_text.strip():
                st.warning("Please paste a job description (or pick a sample job).")
            elif len(job_text.split()) < MIN_WORDS:
                st.warning(f"The job description is very short. Please paste at least {MIN_WORDS} words.")
            elif len(resume_text.split()) < MIN_WORDS:
                st.warning("The resume contains very little text, so the result would not be meaningful.")
            else:
                try:
                    with st.spinner("Analysing..."):
                        analysis = analyze_match(resume_text, job_text, skills_db)
                        recommendations = generate_recommendations(analysis, resume_text, skills_db)
                    st.session_state["result"] = {
                        "analysis": analysis,
                        "recommendations": recommendations,
                        "job_title": job_title,
                    }
                except (ValueError, TypeError) as exc:
                    st.error(f"Could not analyse the texts: {exc}")
                except Exception:  # last-resort guard so the app never shows a stack trace
                    st.error("Something unexpected went wrong. Please try again with different input.")

    if "result" in st.session_state:
        render_results(st.session_state["result"], skills_db)


main()
