# Kitchen Report Breakout

Turns N days' worth of "Kitchen Report" PDFs into a shift-by-shift breakout:
one station per page, items with a quantity column per day, exportable as a
`.docx`. See `kitchen-report-app-handoff.md` for the original spec and the
parsing algorithm this implements.

## Backend (parsing service)

```
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Runs on `http://localhost:8000` by default. `POST /parse` accepts multipart
`files` (PDFs) + `day_labels` (one label per file, same order).

Run tests: `.venv/bin/python -m pytest tests/ -v`

The test suite uses a synthetic PDF fixture (`tests/fixtures.py`, built with
`reportlab`) since no real sample report was available while building this.
**Re-validate the parsing regexes/heuristics against a real kitchen report
PDF before trusting this in production** -- see the NOTE in
`app/parsing/line_classifier.py` for the specific assumption most likely to
need adjusting (the BREAD SUMMARY line format).

## Frontend

```
cd frontend
npm install
npm run dev
```

Defaults to calling the backend at `http://localhost:8000`; override with a
`VITE_API_BASE` env var (e.g. in `frontend/.env.local`) if needed.
