"""
llm_client.py
Integrates with NVIDIA NIM to generate per-student risk reports
and intervention recommendations.
Falls back to a detailed mock report if no API key is configured.
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()
_api_key = os.getenv("NVIDIA_API_KEY")
_model = os.getenv("NVIDIA_NIM_MODEL", "nvidia/nemotron-3-nano-30b-a3b")
_base_url = "https://integrate.api.nvidia.com/v1"


def _call_nvidia_nim(prompt: str) -> str:
    """Call an NVIDIA-hosted NIM model using its OpenAI-compatible API."""
    from openai import OpenAI

    client = OpenAI(base_url=_base_url, api_key=_api_key)
    response = client.chat.completions.create(
        model=_model,
        messages=[
            {"role": "system", "content": "You are a careful academic risk analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1400,
    )
    return (response.choices[0].message.content or "").strip()


def _build_prompt(student: dict) -> str:
    """Build the structured NIM prompt for one student."""
    att_pct = f"{student['attendance_rate'] * 100:.1f}"
    avg_pct = f"{student['assessment_avg']:.1f}"
    notes   = student.get("all_notes", "No notes recorded.")

    return f"""You are an academic risk analyst for a higher education institution.
A student risk engine has processed the following student data.
Generate a structured Student Risk Report using EXACTLY the 6 sections below.
Be specific, professional, and concise. Do not add extra sections.

STUDENT DATA:
- Student ID                        : {student['student_id']}
- Name                              : {student['name']}
- Programme                         : {student['programme']}
- Year                              : Year {student['year']}
- Mentor                            : {student['mentor_name']}
- Attendance Rate                   : {att_pct}%
- Total Absences                    : {student['total_absences']} sessions
- Longest Consecutive Absence Streak: {student['consecutive_absences']} sessions
- Assessment Average                : {avg_pct}%
- Failed Modules                    : {student['failed_modules']} out of 4
- Risk Score                        : {student['risk_score']} / 100
- Risk Tier                         : {student['risk_tier']}
- Mentor Notes                      : {notes}

Generate the report in this EXACT format:

OVERALL RISK LEVEL: [{student['risk_tier']}] — [one sentence stating the primary reason]

RISK SCORE: {student['risk_score']}/100 — [one sentence explaining what drove the score]

ATTENDANCE ANALYSIS:
[2–3 sentences analysing attendance rate, absences, and streak vs 75% threshold]

ACADEMIC PERFORMANCE ANALYSIS:
[2–3 sentences on assessment average, failed modules, and any declining trend]

MENTOR INSIGHTS SUMMARY:
[2–3 sentences synthesising mentor notes and identifying key themes]

INTERVENTION RECOMMENDATIONS:
1. [Specific action] [TYPE: Academic / Attendance / Wellbeing / Mentoring]
2. [Specific action] [TYPE: ...]
3. [Specific action] [TYPE: ...]
{"4. [Specific action] [TYPE: ...]" if student['risk_tier'] == 'High' else ""}

MONITORING PLAN:
[2 sentences on follow-up schedule, metrics to track, and responsible staff member]"""


def generate_student_report(student: dict) -> str:
    """
    Generate a structured risk report for one student.
    Uses NVIDIA NIM if an API key is set, otherwise returns a detailed mock report.

    Parameters
    ----------
    student : dict
        A single row from the risk-scored DataFrame converted to dict.

    Returns
    -------
    str
        Formatted report text.
    """
    if _api_key:
        try:
            return _call_nvidia_nim(_build_prompt(student))
        except Exception as e:
            return f"[API Error] {str(e)}\n\n" + _mock_report(student)
    return _mock_report(student)


def generate_batch_reports(df) -> dict:
    """
    Generate reports for multiple students in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Risk-scored DataFrame from risk_engine.compute_risk()

    Returns
    -------
    dict
        Mapping of student_id → report string
    """
    reports = {}
    for _, row in df.iterrows():
        student = row.to_dict()
        reports[student["student_id"]] = generate_student_report(student)
        time.sleep(1.5)
    return reports


def _mock_report(student: dict) -> str:
    """Return a realistic mock report when no API key is available."""
    att_pct = f"{student['attendance_rate'] * 100:.1f}"
    avg_pct = f"{student['assessment_avg']:.1f}"
    tier    = student["risk_tier"]

    interventions = {
        "High": (
            "1. Schedule an urgent welfare check with the pastoral care lead [TYPE: Wellbeing]\n"
            "2. Provide structured catch-up materials for all missed sessions [TYPE: Academic]\n"
            "3. Explore a flexible attendance arrangement for the remainder of term [TYPE: Attendance]\n"
            "4. Refer to student support services for counselling or financial assistance [TYPE: Wellbeing]"
        ),
        "Medium": (
            "1. Arrange a one-to-one academic support session with the module tutor [TYPE: Academic]\n"
            "2. Set weekly attendance check-ins with the assigned mentor [TYPE: Mentoring]\n"
            "3. Provide revision resources and formative feedback before next assessment [TYPE: Academic]"
        ),
        "Low": (
            "1. Continue regular mentor check-ins to maintain current trajectory [TYPE: Mentoring]\n"
            "2. Offer optional enrichment activities to sustain engagement [TYPE: Academic]\n"
            "3. Acknowledge progress in the next mentor meeting to reinforce positive behaviour [TYPE: Mentoring]"
        ),
    }

    risk_reasons = {
        "High":   "Student shows critical deficits in both attendance and assessment performance, compounded by adverse mentor observations.",
        "Medium": "Student is borderline on one or more risk indicators and requires close monitoring.",
        "Low":    "Student is performing within acceptable parameters across all monitored dimensions.",
    }

    score_reasons = {
        "High":   "Attendance and assessment scores are both well below institutional thresholds, with negative mentor sentiment adding further weight.",
        "Medium": "One or more indicators are below the acceptable threshold, resulting in a moderate composite score.",
        "Low":    "All three risk indicators — attendance, assessment, and mentor sentiment — are within or above acceptable thresholds.",
    }

    att_below = float(att_pct) < 75
    att_comment = (
        f"This is significantly below the institutional minimum threshold of 75%, representing a critical concern."
        if float(att_pct) < 65 else
        f"This falls below the 75% threshold and requires monitoring." if att_below else
        f"This meets the institutional 75% attendance threshold."
    )

    perf_comment = (
        f"This places the student at serious academic risk, well below the 50% pass threshold."
        if student["failed_modules"] >= 3 else
        f"While passing some modules, the overall average suggests inconsistent academic consolidation."
        if student["failed_modules"] >= 1 else
        f"The student is meeting the pass threshold across all modules."
    )

    notes_comment = (
        "Mentor notes consistently reference signs of disengagement, anxiety, and failure to submit work on time. "
        "The student has been observed as withdrawn and struggling to keep up with the demands of the programme. "
        "These observations align closely with the quantitative risk signals and suggest personal or situational factors may be contributing."
        if student["has_negative_notes"] else
        "Mentor notes do not indicate significant behavioural or welfare concerns at this time. "
        "The student appears to be engaging adequately with the academic programme. "
        "Continued mentor contact is recommended to catch any emerging issues early."
    )

    return f"""OVERALL RISK LEVEL: [{tier}] — {risk_reasons[tier]}

RISK SCORE: {student['risk_score']}/100 — {score_reasons[tier]}

ATTENDANCE ANALYSIS:
{student['name']} has an attendance rate of {att_pct}%, with {student['total_absences']} total missed sessions and a longest consecutive absence streak of {student['consecutive_absences']} sessions. {att_comment} {"Immediate follow-up is required to establish the reasons for absence and prevent further deterioration." if att_below else "Attendance should continue to be monitored going forward."}

ACADEMIC PERFORMANCE ANALYSIS:
The student's assessment average stands at {avg_pct}%, with {student['failed_modules']} out of 4 modules resulting in a fail grade. {perf_comment} {"Targeted academic intervention is strongly recommended before the next assessment cycle." if student['failed_modules'] >= 2 else "Performance should be monitored over the next assessment cycle."}

MENTOR INSIGHTS SUMMARY:
{notes_comment}

INTERVENTION RECOMMENDATIONS:
{interventions[tier]}

MONITORING PLAN:
A formal follow-up review should be scheduled within two weeks of this report, at which point attendance rate, submission status, and overall wellbeing should be reassessed by {student['mentor_name']}. If no measurable improvement is observed within four weeks, the case should be escalated to the Head of Student Support for further action.
"""
