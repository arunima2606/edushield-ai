"""
risk_engine.py
Computes a weighted risk score (0–100) and risk tier (High/Medium/Low)
for each student based on attendance, assessment, and mentor sentiment.
"""

import pandas as pd


def _score_attendance(rate: float) -> int:
    """Return attendance risk points (0–40)."""
    if rate < 0.65:   return 40
    elif rate < 0.75: return 25
    elif rate < 0.85: return 10
    else:             return 0


def _score_assessment(avg: float) -> int:
    """Return assessment risk points (0–40)."""
    if avg < 45:   return 40
    elif avg < 55: return 25
    elif avg < 65: return 10
    else:          return 0


def _score_mentor(has_negative: bool) -> int:
    """Return mentor sentiment risk points (0–20)."""
    return 20 if has_negative else 0


def _get_tier(score: int) -> str:
    """Convert numeric score to risk tier label."""
    if score >= 60:   return "High"
    elif score >= 30: return "Medium"
    else:             return "Low"


def compute_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add risk_score and risk_tier columns to the student DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Output of data_loader.load_all_data()

    Returns
    -------
    pd.DataFrame
        Same DataFrame with two new columns: risk_score (int), risk_tier (str)
    """
    df = df.copy()

    df["att_points"]    = df["attendance_rate"].apply(_score_attendance)
    df["assess_points"] = df["assessment_avg"].apply(_score_assessment)
    df["mentor_points"] = df["has_negative_notes"].apply(_score_mentor)

    df["risk_score"] = (df["att_points"] + df["assess_points"] + df["mentor_points"]).astype(int)
    df["risk_tier"]  = df["risk_score"].apply(_get_tier)

    # Drop intermediate columns
    df.drop(columns=["att_points", "assess_points", "mentor_points"], inplace=True)

    return df


if __name__ == "__main__":
    from data_loader import load_all_data
    df = load_all_data()
    df = compute_risk(df)
    print(df[["student_id", "name", "attendance_rate", "assessment_avg",
              "risk_score", "risk_tier"]].to_string())
    print("\nRisk distribution:")
    print(df["risk_tier"].value_counts())
