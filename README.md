# 📄 AI Resume Analyzer & Job Matcher

A Streamlit web app that compares a PDF resume with a job description, scores how closely they match, finds skill gaps, and gives practical **rule-based** improvement suggestions - all locally, with **no API keys and no paid services**.

> **Honest note on the approach:** the match score uses **TF-IDF + cosine similarity** (classic statistical text analysis). There is **no trained machine-learning model, no deep learning and no external AI service**. Suggestions come from transparent rules, not from an AI reviewer.

## Problem statement

Job seekers often don't know why their resume gets ignored. Recruiters and applicant tracking systems look for specific skills and wording from the job posting. This tool shows a candidate, within seconds, how much of a job's language and required skills their resume covers - and what to improve.

## Objectives

- Extract text from PDF resumes reliably and handle bad files gracefully.
- Quantify resume-job similarity with an explainable algorithm.
- Detect technical skills from a configurable dictionary and report matched and missing skills.
- Present results in a clean dashboard and an exportable CSV report.
- Respect privacy: resumes are processed in memory and never stored.

## Features

| # | Feature |
|---|---------|
| 1 | Upload a PDF resume (10 MB limit, password-protected / scanned / corrupt files give friendly errors) |
| 2 | Paste a job description or choose one of four fictional samples |
| 3 | TF-IDF + cosine similarity match score with a plain-language verdict |
| 4 | Skill extraction from a configurable dictionary (`data/skills.json`, 67 skills with aliases) |
| 5 | Skill-gap analysis: matched, missing and extra skills, grouped by category |
| 6 | Plotly dashboard: gauge, skills-by-category chart, keyword charts |
| 7 | Rule-based resume suggestions (clearly labelled as such) |
| 8 | Downloadable CSV report (Excel-friendly, formula-injection safe) |
| 9 | Sample resume (TXT + PDF) and fictional job descriptions |
| 10 | Input validation and error handling - no crashes on empty or invalid input |

## Technologies used

Python 3.11 / 3.12, Streamlit, PyMuPDF, scikit-learn, Pandas, Plotly, Pytest, Git & GitHub, Streamlit Community Cloud.

## Project architecture

```
AI-Resume-Matcher/
├── app.py                      # Streamlit UI (input, validation, dashboard)
├── requirements.txt
├── pytest.ini
├── src/
│   ├── pdf_parser.py           # PDF bytes -> clean text (in memory)
│   ├── matcher.py              # TF-IDF, cosine similarity, keyword overlap, analyze_match()
│   ├── skill_extractor.py      # dictionary skill detection and skill-gap comparison
│   ├── recommendations.py      # rule-based improvement suggestions
│   ├── report.py               # CSV report builder
│   ├── charts.py               # Plotly figures
│   └── sample_pdf.py           # tiny PDF writer for the sample PDF and tests
├── data/
│   ├── skills.json             # editable skill dictionary
│   └── sample_job_descriptions.json
├── sample_data/                # fictional sample resume (.txt and .pdf)
├── tests/                      # pytest unit tests
└── screenshots/                # put your screenshots here
```

Data flow: `PDF upload -> pdf_parser -> matcher + skill_extractor -> recommendations -> charts / CSV report`.

## How the matching algorithm works

1. **Clean** both texts: lower-case, remove URLs and e-mail addresses, collapse whitespace.
2. **Vectorise** with scikit-learn's `TfidfVectorizer` (English stop words removed, 1-2 word phrases, sub-linear term frequency). TF-IDF gives higher weight to words that are distinctive rather than common.
3. **Compare** the two vectors with **cosine similarity** (0 = nothing in common, 1 = identical wording), shown as a percentage.
4. **Skills** are found by whole-word, case-insensitive dictionary matching (so "Java" is not found inside "JavaScript"). Skill coverage = matched job skills / all job skills.

**Reading the score:** raw TF-IDF similarity between a resume and a job post is usually low even for a good fit. In a run with the bundled fictional data, the sample resume scored 17.1% against the ML Intern job (70.6% skill coverage), 9.2% against the Data Analyst job, and 3.4% against the AI Engineer job. The verdict thresholds (≥7 partial, ≥15 good, ≥30 strong) are rough guides chosen on that sample data - not validated benchmarks. Always read the score together with the skill-gap analysis.

## Installation (Windows + VS Code)

1. Install **Python 3.11** (or 3.12) from python.org. Tick **"Add python.exe to PATH"** during installation.
2. Extract `AI-Resume-Matcher.zip`, then in VS Code choose **File -> Open Folder...** and select the `AI-Resume-Matcher` folder.
3. Open a terminal in VS Code (**Terminal -> New Terminal**, PowerShell) and run:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

If you installed Python 3.12, use `py -3.12` in the first command. If PowerShell blocks the activation script, run once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and activate again.

The app opens at <http://localhost:8501>. In VS Code, select the interpreter with **Ctrl+Shift+P -> "Python: Select Interpreter" -> `.venv`**.

## Running the tests

```powershell
python -m pytest -v
```

## Deploying on Streamlit Community Cloud (free)

1. Push the project to a **public** GitHub repository (see below).
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **Create app**, choose your repository and branch, set the main file path to `app.py`.
4. Click **Deploy**. Dependencies are installed from `requirements.txt` automatically.
5. Add the public URL to your README, GitHub "About" section and resume.

Do not deploy with real resumes committed to the repo.

## Example use case

1. Run the app, tick **Use the sample resume instead**.
2. Select **Machine Learning Intern** in the sample job dropdown.
3. Click **Analyze match**. You will see the score, matched skills (Python, Pandas, scikit-learn, SQL, Git...), missing skills (TensorFlow, PyTorch, PostgreSQL, Unit Testing, Deep Learning) and suggestions such as "add a small deep-learning project".
4. Download the CSV report.

To test the upload feature, upload `sample_data/sample_resume.pdf`.

## Customising the skill dictionary

Edit `data/skills.json`. Format: `{"Category": {"Skill name": ["alias1", "alias2"]}}`. Only the listed aliases are matched (aliases are matched whole-word and case-insensitively). Avoid aliases that are ordinary words (for example "go" or "r").

## Limitations and future improvements

**Limitations**
- TF-IDF measures shared wording, not meaning: synonyms ("ML" vs "machine learning") only match if both are in the skill dictionary.
- Scanned (image-only) PDFs are not supported - there is no OCR.
- Multi-column or heavily designed resumes may extract in a jumbled order.
- Skill detection only finds skills in `skills.json`; ambiguous words (e.g. "react") can give false positives.
- Suggestions are simple rules, not expert judgement. English only.
- The score is not a prediction of hiring outcomes.

**Future improvements**
- Semantic similarity with sentence embeddings (e.g. `sentence-transformers`).
- OCR for scanned PDFs, DOCX upload support.
- Section-aware scoring (skills vs experience), experience-level detection.
- Batch comparison of one resume against many jobs; export to PDF.

## Screenshots

Create your own screenshots after running the app and save them in the `screenshots/` folder:

1. Run the app, load the sample resume and a sample job, click **Analyze match**.
2. Take screenshots (Windows: **Win + Shift + S**) of the dashboard and the skill-gap section.
3. Save them as `screenshots/dashboard.png` and `screenshots/skill-gap.png`.
4. Uncomment the lines below in this README:

```markdown
<!-- ![Dashboard](screenshots/dashboard.png) -->
<!-- ![Skill gap](screenshots/skill-gap.png) -->
```

## Uploading to GitHub

1. Install Git from <https://git-scm.com> and create a free GitHub account.
2. On GitHub click **New repository**, name it `AI-Resume-Matcher`, keep it empty (no README), and create it.
3. In the VS Code terminal, from the project folder:

```powershell
git init
git add .
git commit -m "Initial commit: AI Resume Analyzer & Job Matcher"
git branch -M main
git remote add origin https://github.com/<your-username>/AI-Resume-Matcher.git
git push -u origin main
```

4. Edit `LICENSE` and replace `Your Name` with your name before publishing.

## Resume project description

**AI Resume Analyzer & Job Matcher** | Python, Streamlit, scikit-learn, PyMuPDF, Pandas, Plotly, Pytest
- Built a web app that parses PDF resumes and scores their similarity to job descriptions using TF-IDF vectorisation and cosine similarity.
- Implemented a configurable dictionary-based skill extractor and skill-gap analysis with category-level Plotly dashboards and CSV export.
- Wrote unit tests with Pytest for matching, skill extraction, report generation and PDF error handling; deployed on Streamlit Community Cloud.
- Designed privacy-first processing: resumes are handled in memory and never stored.

**Keywords:** Python, Streamlit, NLP, TF-IDF, cosine similarity, scikit-learn, text mining, PyMuPDF, Pandas, Plotly, data visualization, pytest, unit testing, Git, GitHub, modular design.

> Be ready to explain in interviews that this project uses classical NLP (TF-IDF), not a trained neural model.

## License

MIT - see `LICENSE`.
