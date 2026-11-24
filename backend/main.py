"""
backend/main.py
EduShield AI — FastAPI Backend
PS164 | Education & EdTech
"""

import sys
import os
import io
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from data_loader import load_all_data
from risk_engine import compute_risk
from llm_client import generate_student_report

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="EduShield AI API",
    description="AI-powered student risk detection and early intervention — PS164",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load data once at startup ────────────────────────────────────────────────
_df = None

def get_df():
    global _df
    if _df is None:
        raw = load_all_data()
        _df = compute_risk(raw)
    return _df


# ── Pydantic models ──────────────────────────────────────────────────────────
class ReportRequest(BaseModel):
    student_id: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"project": "EduShield AI", "code": "PS164", "status": "running"}


@app.get("/api/cohort")
def get_cohort(tier: Optional[str] = None):
    """Return all students with risk scores. Optionally filter by tier."""
    df = get_df()
    if tier and tier in ["High", "Medium", "Low"]:
        df = df[df["risk_tier"] == tier]

    students = []
    for _, row in df.iterrows():
        students.append({
            "student_id":            row["student_id"],
            "name":                  row["name"],
            "programme":             row["programme"],
            "year":                  int(row["year"]),
            "mentor_name":           row["mentor_name"],
            "attendance_rate":       round(float(row["attendance_rate"]), 4),
            "total_absences":        int(row["total_absences"]),
            "consecutive_absences":  int(row["consecutive_absences"]),
            "assessment_avg":        round(float(row["assessment_avg"]), 1),
            "failed_modules":        int(row["failed_modules"]),
            "has_negative_notes":    bool(row["has_negative_notes"]),
            "risk_score":            int(row["risk_score"]),
            "risk_tier":             row["risk_tier"],
        })
    return {"students": students, "total": len(students)}


@app.get("/api/student/{student_id}")
def get_student(student_id: str):
    """Return full profile for one student including mentor notes."""
    df = get_df()
    row = df[df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    r = row.iloc[0]
    return {
        "student_id":           r["student_id"],
        "name":                 r["name"],
        "programme":            r["programme"],
        "year":                 int(r["year"]),
        "mentor_name":          r["mentor_name"],
        "attendance_rate":      round(float(r["attendance_rate"]), 4),
        "total_absences":       int(r["total_absences"]),
        "consecutive_absences": int(r["consecutive_absences"]),
        "assessment_avg":       round(float(r["assessment_avg"]), 1),
        "failed_modules":       int(r["failed_modules"]),
        "has_negative_notes":   bool(r["has_negative_notes"]),
        "all_notes":            r["all_notes"],
        "risk_score":           int(r["risk_score"]),
        "risk_tier":            r["risk_tier"],
    }


@app.get("/api/metrics")
def get_metrics():
    """Return cohort-level summary metrics."""
    df = get_df()
    return {
        "total":          len(df),
        "high_risk":      int((df["risk_tier"] == "High").sum()),
        "medium_risk":    int((df["risk_tier"] == "Medium").sum()),
        "low_risk":       int((df["risk_tier"] == "Low").sum()),
        "avg_attendance": round(float(df["attendance_rate"].mean()) * 100, 1),
        "avg_assessment": round(float(df["assessment_avg"].mean()), 1),
    }


@app.post("/api/report")
def generate_report(req: ReportRequest):
    """Generate an AI risk report for one student."""
    df = get_df()
    row = df[df["student_id"] == req.student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Student {req.student_id} not found")
    student = row.iloc[0].to_dict()
    try:
        report = generate_student_report(student)
        return {"student_id": req.student_id, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report/download/{student_id}")
def download_report(student_id: str):
    """Download a single student's report as a .txt file."""
    df = get_df()
    row = df[df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    student = row.iloc[0].to_dict()
    report  = generate_student_report(student)
    buf = io.BytesIO(report.encode("utf-8"))
    return StreamingResponse(
        buf,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=EduShield_{student_id}_Report.txt"}
    )


@app.get("/api/report/batch-zip")
def download_batch_zip():
    """Generate reports for all High risk students and return as a ZIP."""
    df = get_df()
    high_df = df[df["risk_tier"] == "High"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _, row in high_df.iterrows():
            student = row.to_dict()
            report  = generate_student_report(student)
            zf.writestr(f"EduShield_{student['student_id']}_Report.txt", report)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=EduShield_HighRisk_Reports.zip"}
    )
