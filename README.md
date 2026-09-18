# Claude-Code-Projects

## PwC job screening (LinkedIn/careers postings)

`screen.py` is a small CLI that scores a candidate resume or LinkedIn
profile export (plain text) against a PwC job description, splitting the
posting into its "What You Must Have" (required) and "What Sets You
Apart" (preferred) sections and reporting matched/missing keywords and an
overall fit score.

It works on plain-text files you provide (e.g. a job posting you paste
from LinkedIn/PwC careers, or a resume export) — it does not scrape
LinkedIn itself, since automated scraping of LinkedIn violates its terms
of service.

### Usage

Screen a single resume against a job description:

```
python3 screen.py --job jobs/pwc_forward_deployed_data_engineering_senior_associate.txt \
                   --resume resumes/sample_candidate.txt
```

Screen every resume in a directory and rank candidates:

```
python3 screen.py --job jobs/pwc_forward_deployed_data_engineering_senior_associate.txt \
                   --resume-dir resumes --top 10
```

### Layout

- `screen.py` — the screening CLI
- `jobs/` — job description text files (e.g. the PwC Forward Deployed
  Data Engineering - Senior Associate posting)
- `resumes/` — resume/profile text files to screen, one per candidate
