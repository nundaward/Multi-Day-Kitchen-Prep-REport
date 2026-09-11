import io

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .parsing import parse_pdf

app = FastAPI(title="Kitchen Report Breakout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/parse")
async def parse(
    files: list[UploadFile] = File(...),
    day_labels: list[str] = Form(...),
):
    """Parse N kitchen report PDFs, one per day.

    day_labels must be the same length as files, in matching order (e.g. the
    calendar date or "Monday"/"Tuesday" label the user assigned to each file).

    Returns: { day_label: { station: { shift_label: [{name, qty}, ...] } } }
    plus a parallel `bread_summary` map for any station-level cross-check totals.
    """
    result = {}
    bread_summary_by_day = {}

    for file, label in zip(files, day_labels):
        contents = await file.read()
        report, bread_summary = parse_pdf(io.BytesIO(contents))
        result[label] = report
        bread_summary_by_day[label] = bread_summary

    return {"days": result, "bread_summary": bread_summary_by_day}


@app.get("/health")
def health():
    return {"status": "ok"}
