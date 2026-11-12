import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st


# Find the database in the same folder as this Python file.
DATABASE_PATH = Path(__file__).resolve().parent / "placements.db"

APPLICATION_STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]

st.set_page_config(page_title="Placement Application Tracker", page_icon="📋")
st.title("Placement Application Tracker")
st.write("Keep track of your job applications and their current status.")

# Show a helpful message instead of silently creating an empty database.
if not DATABASE_PATH.exists():
    st.error(
        f"Database not found: {DATABASE_PATH}. "
        "Create placements.db with the applications table, then run this app again."
    )
    st.stop()


def add_application(
    company_name: str, job_role: str, application_date: str, status: str
) -> None:
    """Save one application to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO applications (company_name, job_role, application_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status),
        )
        connection.commit()
    finally:
        connection.close()


def get_applications() -> pd.DataFrame:
    """Read all application records from the database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT application_id, company_name, job_role, application_date, status
            FROM applications
            ORDER BY application_date DESC, application_id DESC
            """
        )
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        return pd.DataFrame(rows, columns=column_names)
    finally:
        connection.close()


def get_total_applications() -> int:
    """Return the number of application records."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        result = connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()
        return result[0]
    finally:
        connection.close()


def get_most_applied_role():
    """Return the most applied-for role and its application count."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        return connection.execute(
            """
            SELECT job_role, COUNT(*) AS application_count
            FROM applications
            GROUP BY job_role
            ORDER BY application_count DESC, job_role COLLATE NOCASE ASC, job_role ASC
            LIMIT 1
            """
        ).fetchone()
    finally:
        connection.close()


def get_status_counts() -> dict[str, int]:
    """Return application totals grouped by status."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        rows = connection.execute(
            """
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
            """
        ).fetchall()
    finally:
        connection.close()

    counts = {status: 0 for status in APPLICATION_STATUSES}
    for status, count in rows:
        # Include older or blank statuses too, so no database records are omitted.
        display_status = status if status else "Not specified"
        counts[display_status] = counts.get(display_status, 0) + count
    return counts


# Feature 1: Add a new application.
st.header("Add Application")
with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input(
        "Application Date",
        value=date.today(),
        format="YYYY-MM-DD",
    )
    status = st.selectbox("Status", APPLICATION_STATUSES)
    submitted = st.form_submit_button("Add Application")

if submitted:
    if not company_name.strip():
        st.error("Please enter a company name.")
    elif not job_role.strip():
        st.error("Please enter a job role.")
    else:
        add_application(
            company_name.strip(),
            job_role.strip(),
            application_date.isoformat(),
            status,
        )
        st.success("Application added successfully.")

# Features 3 and 4: Show the total and the most frequently applied-for role.
st.header("Application Overview")
total_applications = get_total_applications()
most_applied_role = get_most_applied_role()

overview_columns = st.columns(2)
overview_columns[0].metric("Total Applications", total_applications)
if most_applied_role is None:
    overview_columns[1].write("**Most Applied Role**")
    overview_columns[1].write("No applications yet.")
else:
    role_name, role_count = most_applied_role
    overview_columns[1].metric("Most Applied Role", role_name)
    overview_columns[1].write(f"{role_count} application(s)")

# Feature 2: Display all application records.
st.header("View Applications")
applications = get_applications()
if applications.empty:
    st.info("No applications are available yet. Add one using the form above.")
else:
    st.dataframe(applications, width="stretch", hide_index=True)

# Feature 5: Show each status total and a bar chart.
st.header("Status-wise Summary")
status_counts = get_status_counts()
status_summary = pd.DataFrame(
    {
        "Status": list(status_counts.keys()),
        "Applications": list(status_counts.values()),
    }
)
st.dataframe(status_summary, width="stretch", hide_index=True)
st.bar_chart(status_summary, x="Status", y="Applications")
