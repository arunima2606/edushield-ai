"""
data_loader.py
Ingests all four synthetic datasets and merges them into a single
per-student DataFrame with computed risk features.
"""

import pandas as pd
import json
from datetime import datetime


NEGATIVE_KEYWORDS = [
    "missed", "disengaged", "anxious", "not submitted", "concerning",
    "withdrawn", "falling behind", "absent", "struggling", "failed to attend",
    "overwhelmed", "incomplete", "no explanation", "serious concern"
]


def compute_consecutive_absences(group: pd.DataFrame) -> int:
    """Return the longest streak of consecutive absent sessions for a student."""
    statuses = group.sort_values("date")["status"].tolist()
    max_streak = streak = 0
    for s in statuses:
        if s == "absent":
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


def load_all_data() -> pd.DataFrame:
    """
    Load all four data sources, compute per-student features, and return
    a single merged DataFrame with one row per student.

    Returns
    -------
    pd.DataFrame
        Columns: student_id, name, programme, year, mentor_name,
                 attendance_rate, total_absences, consecutive_absences,
                 assessment_avg, failed_modules, has_negative_notes, all_notes
    """
    # ── Load raw files ──────────────────────────────────────────────────
    students    = pd.read_csv("data/students.csv")
    attendance  = pd.read_csv("data/attendance.csv")
    assessments = pd.read_csv("data/assessments.csv")
    with open("data/mentor_notes.json") as f:
        notes_raw = json.load(f)
    notes = pd.DataFrame(notes_raw)

    # ── Attendance features ─────────────────────────────────────────────
    total_sessions = attendance.groupby("student_id").size().rename("total_sessions")

    present_mask = attendance["status"].isin(["present", "late"])
    sessions_attended = attendance[present_mask].groupby("student_id").size().rename("sessions_attended")

    total_absences = (
        attendance[attendance["status"] == "absent"]
        .groupby("student_id").size()
        .rename("total_absences")
    )

    consecutive_absences = (
        attendance.groupby("student_id")
        .apply(compute_consecutive_absences)
        .rename("consecutive_absences")
    )

    att_features = pd.concat(
        [total_sessions, sessions_attended, total_absences, consecutive_absences], axis=1
    ).fillna(0).astype(int)
    att_features["attendance_rate"] = (
        att_features["sessions_attended"] / att_features["total_sessions"]
    ).round(4)

    # ── Assessment features ─────────────────────────────────────────────
    assess_agg = assessments.groupby("student_id").agg(
        assessment_avg=("marks_obtained", "mean"),
        failed_modules=("pass_fail", lambda x: (x == "Fail").sum())
    ).round({"assessment_avg": 1})

    # ── Mentor note features ─────────────────────────────────────────────
    def analyse_notes(group):
        combined = " ".join(group["note"].tolist()).lower()
        has_negative = any(kw in combined for kw in NEGATIVE_KEYWORDS)
        return pd.Series({
            "has_negative_notes": has_negative,
            "all_notes": " | ".join(group["note"].tolist())
        })

    note_features = notes.groupby("student_id").apply(analyse_notes)

    # ── Merge everything ────────────────────────────────────────────────
    df = (
        students
        .merge(att_features[["attendance_rate", "total_absences", "consecutive_absences"]],
               on="student_id", how="left")
        .merge(assess_agg, on="student_id", how="left")
        .merge(note_features, on="student_id", how="left")
    )

    df["has_negative_notes"] = df["has_negative_notes"].fillna(False)
    df["all_notes"] = df["all_notes"].fillna("No mentor notes recorded.")

    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = load_all_data()
    print(df[["student_id", "name", "attendance_rate", "assessment_avg",
              "failed_modules", "has_negative_notes"]].to_string())
