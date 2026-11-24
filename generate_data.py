"""
generate_data.py
Generates all four synthetic datasets for EduShield AI (PS164).
Run this once before launching app.py.
"""

import pandas as pd
import json
import random
from datetime import date, timedelta
import os

random.seed(42)
os.makedirs("data", exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────
STUDENT_IDS = [f"STU-{str(i).zfill(3)}" for i in range(1, 26)]

NAMES = [
    "Priya Menon", "James Okafor", "Sofia Reyes", "Tom Brinkley", "Anika Sharma",
    "Rahul Nair", "Chloe Bennett", "Mohammed Al-Farsi", "Divya Krishnan", "Ethan Clarke",
    "Neha Patel", "Lucas Fernandez", "Yuna Kim", "Samuel Adeola", "Ishaan Bose",
    "Emily Walsh", "Arjun Mehta", "Fatima Zahra", "Dylan Hughes", "Kavya Reddy",
    "Noah Kim", "Tanvi Joshi", "Oliver Grant", "Shreya Das", "Liam O'Brien"
]

PROGRAMMES = [
    "BSc Computer Science", "BSc Data Science",
    "BEng Software Engineering", "BSc Artificial Intelligence"
]

MENTORS = ["Dr. Anand Rao", "Prof. Sarah Mitchell", "Dr. James Chen",
           "Ms. Priya Kapoor", "Mr. David Osei"]

ASSESSMENTS = ["Assignment 1", "Mid-Term Exam", "Assignment 2", "Project Submission"]

# ── Session dates: Mon/Wed/Fri across one term (10 weeks = 30 sessions) ───
def get_session_dates():
    dates = []
    start = date(2025, 9, 1)
    d = start
    count = 0
    while count < 30:
        if d.weekday() in (0, 2, 4):  # Mon, Wed, Fri
            dates.append(d)
            count += 1
        d += timedelta(days=1)
    return dates

SESSION_DATES = get_session_dates()

# ── Attendance patterns by risk group ─────────────────────────────────────
def get_attendance_pattern(student_idx):
    """Return target attendance rate based on student index (0-based)."""
    if student_idx < 5:    return random.uniform(0.40, 0.63)   # high risk
    elif student_idx < 12: return random.uniform(0.65, 0.80)   # medium risk
    else:                  return random.uniform(0.85, 1.00)   # low risk

# ── Assessment marks by risk group ────────────────────────────────────────
def get_marks(student_idx, assessment_idx):
    if student_idx < 5:
        base = random.randint(25, 44)
        # declining trend for some
        return max(10, base - assessment_idx * random.randint(0, 4))
    elif student_idx < 12:
        return random.randint(45, 62)
    else:
        return random.randint(63, 95)

# ── Mentor notes by risk group ────────────────────────────────────────────
HIGH_RISK_NOTES = [
    "Student has missed {n} consecutive sessions with no explanation provided. Performance is concerning.",
    "Meeting held — student appears disengaged and anxious about upcoming assessments. Not submitted last assignment.",
    "Raised with student welfare team. Student is withdrawn and falling behind on all modules.",
    "Student failed to attend scheduled mentor meeting. Repeated absences are a serious concern.",
    "Student expressed feeling overwhelmed. Struggling to keep up with coursework. Immediate support recommended.",
]

MEDIUM_RISK_NOTES = [
    "Student attended today's session but seems distracted. Marks are borderline — will monitor.",
    "Discussed upcoming deadlines. Student is managing but flagged some personal difficulties at home.",
    "Performance is average. Student participates occasionally. Follow-up scheduled for next week.",
    "Some improvement noted this week. Still below target on attendance — encouraged to attend all sessions.",
    "Student submitted late work with partial completion. Agreed on an action plan going forward.",
]

LOW_RISK_NOTES = [
    "Student is performing well and actively participates in class discussions.",
    "Excellent progress this term. Student is on track and proactive in seeking feedback.",
    "Strong submission on Assignment 2. Student is engaged and improving each week.",
    "Student flagged a minor concern about workload — offered optional study group. No further action needed.",
    "Positive meeting. Student is well-organised and meeting all deadlines comfortably.",
]

def get_notes(student_idx, student_id, mentor):
    pool = HIGH_RISK_NOTES if student_idx < 5 else MEDIUM_RISK_NOTES if student_idx < 12 else LOW_RISK_NOTES
    selected = random.sample(pool, 3)
    note_dates = sorted(random.sample(SESSION_DATES, 3))
    notes = []
    for i, (note, d) in enumerate(zip(selected, note_dates)):
        notes.append({
            "student_id": student_id,
            "date": str(d),
            "mentor_name": mentor,
            "note": note.replace("{n}", str(random.randint(2, 5)))
        })
    return notes

# ── GENERATE STUDENTS ──────────────────────────────────────────────────────
students = []
for i, (sid, name) in enumerate(zip(STUDENT_IDS, NAMES)):
    students.append({
        "student_id": sid,
        "name": name,
        "programme": PROGRAMMES[i % len(PROGRAMMES)],
        "year": random.choice([1, 2, 3]),
        "mentor_name": MENTORS[i % len(MENTORS)]
    })
df_students = pd.DataFrame(students)
df_students.to_csv("data/students.csv", index=False)
print(f"✓ students.csv — {len(df_students)} students")

# ── GENERATE ATTENDANCE ────────────────────────────────────────────────────
attendance_rows = []
absence_reasons = ["illness", "family", "transport", "unknown", ""]

for i, s in enumerate(students):
    rate = get_attendance_pattern(i)
    for d in SESSION_DATES:
        rand = random.random()
        if rand < rate:
            status = "present" if random.random() > 0.1 else "late"
            reason = ""
        else:
            status = "absent"
            reason = random.choice(absence_reasons)
        attendance_rows.append({
            "student_id": s["student_id"],
            "date": str(d),
            "session_type": random.choice(["Lecture", "Lab", "Tutorial"]),
            "status": status,
            "absence_reason": reason
        })

df_att = pd.DataFrame(attendance_rows)
df_att.to_csv("data/attendance.csv", index=False)
print(f"✓ attendance.csv — {len(df_att)} rows")

# ── GENERATE ASSESSMENTS ───────────────────────────────────────────────────
assessment_rows = []
sub_dates = [date(2025, 9, 20), date(2025, 10, 15), date(2025, 11, 5), date(2025, 11, 28)]

for i, s in enumerate(students):
    for j, aname in enumerate(ASSESSMENTS):
        marks = get_marks(i, j)
        assessment_rows.append({
            "student_id": s["student_id"],
            "assessment_name": aname,
            "max_marks": 100,
            "marks_obtained": marks,
            "submission_date": str(sub_dates[j]),
            "pass_fail": "Pass" if marks >= 50 else "Fail"
        })

df_assess = pd.DataFrame(assessment_rows)
df_assess.to_csv("data/assessments.csv", index=False)
print(f"✓ assessments.csv — {len(df_assess)} rows")

# ── GENERATE MENTOR NOTES ──────────────────────────────────────────────────
all_notes = []
for i, s in enumerate(students):
    all_notes.extend(get_notes(i, s["student_id"], s["mentor_name"]))

with open("data/mentor_notes.json", "w") as f:
    json.dump(all_notes, f, indent=2)
print(f"✓ mentor_notes.json — {len(all_notes)} notes")

print("\nAll datasets generated successfully in /data")
