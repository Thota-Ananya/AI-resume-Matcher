# Sample data

All people, companies and job postings in this project are **fictional** and exist only for testing.

| File | Description |
|------|-------------|
| `sample_resume.txt` | A fictional student resume in plain text. The app can load it with the "Use sample resume" checkbox. |
| `sample_resume.pdf` | The same resume as a PDF, so you can test the upload feature. |
| `../data/sample_job_descriptions.json` | Four fictional job descriptions (ML Intern, Python Developer, Data Analyst, AI Engineer). |

## Regenerating the sample PDF

If you edit `sample_resume.txt`, rebuild the PDF from the project root:

```powershell
python -m src.sample_pdf
```

## Testing with your own resume

Upload your own PDF in the app. It is processed in memory only and is never saved.
Do not commit real resumes to a public GitHub repository.
