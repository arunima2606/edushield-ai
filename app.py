"""
app.py
EduShield AI — Streamlit Dashboard
PS164 | Education & EdTech | Attendance Risk
"""

import streamlit as st
import pandas as pd
import zipfile
import io
import os
from data_loader import load_all_data
from risk_engine import compute_risk
from llm_client import generate_student_report

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduShield AI — PS164",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #111111; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stRadio label { color: #cccccc !important; }
    .risk-high   { background:#fdecea; color:#a32d2d; padding:4px 12px;
                   border-radius:20px; font-weight:600; display:inline-block; }
    .risk-medium { background:#fff3e0; color:#854f0b; padding:4px 12px;
                   border-radius:20px; font-weight:600; display:inline-block; }
    .risk-low    { background:#e8f5e9; color:#2e7d32; padding:4px 12px;
                   border-radius:20px; font-weight:600; display:inline-block; }
    .metric-card { background:#f8f8f8; border:1px solid #e0e0e0;
                   border-radius:10px; padding:18px 22px; }
    .section-title { font-size:13px; font-weight:600; color:#888;
                     text-transform:uppercase; letter-spacing:0.05em;
                     margin-bottom:6px; }
    div[data-testid="stMetric"] { background:#f8f8f8; border-radius:10px;
                                   padding:14px 18px; border:1px solid #ebebeb; }
</style>
""", unsafe_allow_html=True)

# ── Load and cache data ───────────────────────────────────────────────────────
@st.cache_data
def get_data():
    """Load, merge, and score all student data. Cached for performance."""
    df = load_all_data()
    df = compute_risk(df)
    return df

df = get_data()

# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.markdown("## 🛡️ EduShield AI")
st.sidebar.markdown("**PS164** · Education & EdTech")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["📊 Cohort Overview", "🔍 Student Detail", "📤 Export Reports"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<small style='color:#888'>AI-powered student risk detection<br>"
    "Academic Year 2025–2026</small>",
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — COHORT OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
if page == "📊 Cohort Overview":

    st.title("EduShield AI — Student Risk Dashboard")
    st.markdown("**PS164 · Education & EdTech · Attendance Risk**")
    st.markdown("---")

    # ── Top metrics ──────────────────────────────────────────────────────────
    total    = len(df)
    n_high   = len(df[df["risk_tier"] == "High"])
    n_medium = len(df[df["risk_tier"] == "Medium"])
    n_low    = len(df[df["risk_tier"] == "Low"])
    avg_att  = df["attendance_rate"].mean() * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Students", total)
    c2.metric("🔴 High Risk",   n_high,   delta=f"{n_high/total*100:.0f}% of cohort",   delta_color="inverse")
    c3.metric("🟠 Medium Risk", n_medium, delta=f"{n_medium/total*100:.0f}% of cohort", delta_color="off")
    c4.metric("🟢 Low Risk",    n_low,    delta=f"{n_low/total*100:.0f}% of cohort",    delta_color="normal")
    c5.metric("Avg. Attendance", f"{avg_att:.1f}%", delta=f"Target: 75%", delta_color="off")

    st.markdown("---")

    # ── Filter ───────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns([2, 8])
    with col_f1:
        tier_filter = st.selectbox("Filter by Risk Tier", ["All", "High", "Medium", "Low"])

    filtered = df if tier_filter == "All" else df[df["risk_tier"] == tier_filter]

    st.markdown(f"**{len(filtered)} students** {'(all)' if tier_filter == 'All' else f'at {tier_filter} risk'}")

    # ── Styled table ─────────────────────────────────────────────────────────
    def colour_tier(val):
        colours = {"High": "background-color:#fdecea;color:#a32d2d;font-weight:600",
                   "Medium": "background-color:#fff3e0;color:#854f0b;font-weight:600",
                   "Low": "background-color:#e8f5e9;color:#2e7d32;font-weight:600"}
        return colours.get(val, "")

    display_cols = ["student_id", "name", "programme", "year",
                    "attendance_rate", "assessment_avg", "failed_modules",
                    "risk_score", "risk_tier"]
    display = filtered[display_cols].copy()
    display.columns = ["ID", "Name", "Programme", "Year",
                       "Attendance", "Avg. Marks", "Failed",
                       "Risk Score", "Risk Tier"]
    display["Attendance"] = (display["Attendance"] * 100).round(1).astype(str) + "%"
    display["Avg. Marks"] = display["Avg. Marks"].round(1)

    styled = display.style.applymap(colour_tier, subset=["Risk Tier"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Risk distribution bar chart ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Risk Distribution")
    col_chart, col_space = st.columns([2, 3])
    with col_chart:
        dist = df["risk_tier"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
        chart_df = pd.DataFrame({"Risk Tier": dist.index, "Students": dist.values})
        st.bar_chart(chart_df.set_index("Risk Tier"))


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — STUDENT DETAIL
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Student Detail":

    st.title("Student Detail View")
    st.markdown("---")

    # ── Student selector ─────────────────────────────────────────────────────
    options = [f"{row['student_id']} — {row['name']}" for _, row in df.iterrows()]
    selected_label = st.selectbox("Select a student", options)
    selected_id    = selected_label.split(" — ")[0]
    student        = df[df["student_id"] == selected_id].iloc[0].to_dict()

    tier_badge = {
        "High":   '<span class="risk-high">🔴 High Risk</span>',
        "Medium": '<span class="risk-medium">🟠 Medium Risk</span>',
        "Low":    '<span class="risk-low">🟢 Low Risk</span>',
    }

    st.markdown("---")
    left, right = st.columns([1, 1])

    # ── Left column: stats ────────────────────────────────────────────────────
    with left:
        st.markdown("##### Student Profile")
        st.info(
            f"**{student['name']}**\n\n"
            f"📚 {student['programme']} · Year {student['year']}\n\n"
            f"👤 Mentor: {student['mentor_name']}"
        )

        st.markdown(tier_badge[student["risk_tier"]], unsafe_allow_html=True)
        st.markdown("")

        c1, c2 = st.columns(2)
        att_delta = round(student["attendance_rate"] * 100 - 75, 1)
        c1.metric(
            "Attendance Rate",
            f"{student['attendance_rate']*100:.1f}%",
            delta=f"{att_delta:+.1f}% vs 75% threshold",
            delta_color="normal" if att_delta >= 0 else "inverse"
        )
        avg_delta = round(student["assessment_avg"] - 50, 1)
        c2.metric(
            "Assessment Avg.",
            f"{student['assessment_avg']:.1f}%",
            delta=f"{avg_delta:+.1f}% vs 50% pass mark",
            delta_color="normal" if avg_delta >= 0 else "inverse"
        )

        c3, c4 = st.columns(2)
        c3.metric("Total Absences",        student["total_absences"])
        c4.metric("Consecutive Absences",  student["consecutive_absences"])

        c5, c6 = st.columns(2)
        c5.metric("Failed Modules",        f"{student['failed_modules']} / 4")
        c6.metric("Risk Score",            f"{student['risk_score']} / 100")

        st.markdown("**Risk Score Breakdown**")
        st.progress(int(student["risk_score"]))

    # ── Right column: notes + AI report ──────────────────────────────────────
    with right:
        with st.expander("📝 Mentor Notes", expanded=False):
            notes_list = student["all_notes"].split(" | ")
            for note in notes_list:
                st.markdown(f"- {note}")

        st.markdown("##### AI Risk Report")
        if "report_cache" not in st.session_state:
            st.session_state["report_cache"] = {}

        if st.button("🤖 Generate AI Risk Report", type="primary"):
            with st.spinner("Generating report via NVIDIA NIM..."):
                try:
                    report = generate_student_report(student)
                    st.session_state["report_cache"][selected_id] = report
                except Exception as e:
                    st.error(f"Report generation failed: {e}")

        if selected_id in st.session_state["report_cache"]:
            report_text = st.session_state["report_cache"][selected_id]
            st.text_area("Generated Report", value=report_text, height=420)
            st.download_button(
                label="⬇️ Download Report (.txt)",
                data=report_text,
                file_name=f"EduShield_{selected_id}_Report.txt",
                mime="text/plain"
            )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — EXPORT REPORTS
# ════════════════════════════════════════════════════════════════════════════
elif page == "📤 Export Reports":

    st.title("Batch Export — High Risk Students")
    st.markdown("Generate and download intervention reports for all high-risk students.")
    st.markdown("---")

    high_risk_df = df[df["risk_tier"] == "High"].reset_index(drop=True)
    n_high = len(high_risk_df)

    if n_high == 0:
        st.success("No students are currently classified as High Risk.")
    else:
        st.markdown(f"**{n_high} students** are currently classified as High Risk.")

        # Summary table
        summary_cols = ["student_id", "name", "programme", "attendance_rate",
                        "assessment_avg", "risk_score"]
        summary = high_risk_df[summary_cols].copy()
        summary["attendance_rate"] = (summary["attendance_rate"] * 100).round(1).astype(str) + "%"
        summary["assessment_avg"]  = summary["assessment_avg"].round(1)
        summary.columns = ["ID", "Name", "Programme", "Attendance", "Avg. Marks", "Risk Score"]
        st.dataframe(summary, use_container_width=True, hide_index=True)

        st.markdown("---")

        if "batch_reports" not in st.session_state:
            st.session_state["batch_reports"] = {}

        if st.button("🤖 Generate Reports for All High Risk Students", type="primary"):
            progress = st.progress(0)
            status   = st.empty()

            for i, (_, row) in enumerate(high_risk_df.iterrows()):
                student = row.to_dict()
                sid     = student["student_id"]
                status.text(f"Generating report for {student['name']} ({i+1}/{n_high})...")
                try:
                    report = generate_student_report(student)
                    st.session_state["batch_reports"][sid] = (student["name"], report)
                except Exception as e:
                    st.session_state["batch_reports"][sid] = (
                        student["name"], f"[Error] {str(e)}"
                    )
                progress.progress((i + 1) / n_high)

            status.text("✅ All reports generated.")

        # Show generated reports
        if st.session_state.get("batch_reports"):
            st.markdown("---")
            st.markdown("#### Generated Reports")

            # ZIP download
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for sid, (name, report) in st.session_state["batch_reports"].items():
                    zf.writestr(f"EduShield_{sid}_Report.txt", report)
            zip_buffer.seek(0)

            st.download_button(
                label="⬇️ Download All Reports (.zip)",
                data=zip_buffer,
                file_name="EduShield_HighRisk_Reports.zip",
                mime="application/zip"
            )

            st.markdown("")

            for sid, (name, report) in st.session_state["batch_reports"].items():
                with st.expander(f"📄 {name} ({sid})"):
                    st.text_area("Report", value=report, height=380, key=f"report_{sid}")
                    st.download_button(
                        label=f"⬇️ Download {sid} report",
                        data=report,
                        file_name=f"EduShield_{sid}_Report.txt",
                        mime="text/plain",
                        key=f"dl_{sid}"
                    )
