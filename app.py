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
APPLICATION_COLUMNS = [
    "application_id",
    "company_name",
    "job_role",
    "application_date",
    "status",
    "interview_date",
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


def ensure_interview_date_column() -> None:
    """Add the optional interview date to an existing database if needed."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(applications)")
        }
        if not columns:
            raise RuntimeError(
                "The placements.db database does not contain an applications table. "
                "Run init_db.py to create it."
            )
        if "interview_date" not in columns:
            connection.execute(
                "ALTER TABLE applications ADD COLUMN interview_date TEXT"
            )
            connection.commit()
    finally:
        connection.close()


ensure_interview_date_column()

if "application_notice" in st.session_state:
    st.success(st.session_state.pop("application_notice"))


def add_application(
    company_name: str,
    job_role: str,
    application_date: str,
    status: str,
    interview_date: str | None,
) -> None:
    """Save one application to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO applications (
                company_name, job_role, application_date, status, interview_date
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status, interview_date),
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
            SELECT application_id, company_name, job_role, application_date,
                   status, interview_date
            FROM applications
            ORDER BY application_date DESC, application_id DESC
            """
        )
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=APPLICATION_COLUMNS)
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
        display_status = status if status else "Not specified"
        counts[display_status] = counts.get(display_status, 0) + count
    return counts


def update_application(
    application_id: int, status: str, interview_date: str | None
) -> None:
    """Update an application's status and optional interview date."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            UPDATE applications
            SET status = ?, interview_date = ?
            WHERE application_id = ?
            """,
            (status, interview_date, application_id),
        )
        connection.commit()
    finally:
        connection.close()


def delete_application(application_id: int) -> None:
    """Delete one application by its ID."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            "DELETE FROM applications WHERE application_id = ?",
            (application_id,),
        )
        connection.commit()
    finally:
        connection.close()


def get_upcoming_interviews() -> pd.DataFrame:
    """Return scheduled interviews today or later, in date order."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT application_id, company_name, job_role, interview_date, status
            FROM applications
            WHERE status = ? AND interview_date >= ?
            ORDER BY interview_date ASC, application_id ASC
            """,
            ("Interview Scheduled", date.today().isoformat()),
        )
        rows = cursor.fetchall()
        return pd.DataFrame(
            rows,
            columns=[
                "application_id",
                "company_name",
                "job_role",
                "interview_date",
                "status",
            ],
        )
    finally:
        connection.close()


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
    interview_date = st.date_input(
        "Interview Date (optional)",
        value=None,
        format="YYYY-MM-DD",
    )
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
            interview_date.isoformat() if interview_date else None,
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

# Display interviews that are scheduled for today or a future date.
st.header("Upcoming Interviews")
upcoming_interviews = get_upcoming_interviews()
if upcoming_interviews.empty:
    st.info("No upcoming interviews. Add an interview date to a scheduled application.")
else:
    st.dataframe(upcoming_interviews, width="stretch", hide_index=True)

# Search and filter the existing application records.
st.header("View Applications")
applications = get_applications()
available_statuses = list(APPLICATION_STATUSES)
additional_statuses = sorted(
    {
        status
        for status in applications["status"].dropna().unique()
        if status and status not in available_statuses
    },
    key=str.casefold,
)
status_options = ["All statuses", *available_statuses, *additional_statuses]
if applications["status"].isna().any() or applications["status"].eq("").any():
    status_options.append("Not specified")

search_column, filter_column = st.columns(2)
search_text = search_column.text_input("Search by Company Name")
selected_status = filter_column.selectbox("Filter by Status", status_options)

filtered_applications = applications
if search_text.strip():
    matching_company = filtered_applications["company_name"].fillna("").str.contains(
        search_text.strip(), case=False, regex=False
    )
    filtered_applications = filtered_applications[matching_company]
if selected_status == "Not specified":
    missing_status = filtered_applications["status"].fillna("").str.strip().eq("")
    filtered_applications = filtered_applications[missing_status]
elif selected_status != "All statuses":
    filtered_applications = filtered_applications[
        filtered_applications["status"] == selected_status
    ]

if applications.empty:
    st.info("No applications are available yet. Add one using the form above.")
elif filtered_applications.empty:
    st.info("No applications match the selected search and status filter.")
else:
    st.dataframe(filtered_applications, width="stretch", hide_index=True)

st.download_button(
    "Export Applications to CSV",
    data=applications.to_csv(index=False).encode("utf-8-sig"),
    file_name="placement_applications.csv",
    mime="text/csv",
    disabled=applications.empty,
)

# Update an application's status or interview date.
if not applications.empty:
    st.subheader("Update Application")
    application_options = {
        (
            f"#{row.application_id} - {row.company_name} - {row.job_role}"
        ): row.application_id
        for row in applications.itertuples(index=False)
    }
    selected_application_label = st.selectbox(
        "Choose an application to update",
        list(application_options),
        key="update_application_choice",
    )
    selected_application_id = application_options[selected_application_label]
    selected_application = applications[
        applications["application_id"] == selected_application_id
    ].iloc[0]
    current_status = selected_application["status"]
    if pd.isna(current_status):
        current_status = ""
    status_options_for_update = list(APPLICATION_STATUSES)
    if current_status and current_status not in status_options_for_update:
        status_options_for_update.append(current_status)

    with st.form("update_application_form"):
        updated_status = st.selectbox(
            "New Status",
            status_options_for_update,
            index=(
                status_options_for_update.index(current_status)
                if current_status in status_options_for_update
                else 0
            ),
        )
        current_interview_date = selected_application["interview_date"]
        interview_date_value = (
            date.fromisoformat(str(current_interview_date))
            if pd.notna(current_interview_date) and current_interview_date
            else None
        )
        updated_interview_date = st.date_input(
            "Interview Date (optional)",
            value=interview_date_value,
            format="YYYY-MM-DD",
        )
        update_submitted = st.form_submit_button("Save Changes")

    if update_submitted:
        update_application(
            selected_application_id,
            updated_status,
            updated_interview_date.isoformat() if updated_interview_date else None,
        )
        st.session_state["application_notice"] = "Application updated successfully."
        st.rerun()

    # Require explicit confirmation before permanently deleting a record.
    st.subheader("Delete Application")
    with st.form("delete_application_form"):
        delete_application_label = st.selectbox(
            "Choose an application to delete",
            list(application_options),
            key="delete_application_choice",
        )
        confirmed_delete = st.checkbox(
            "I confirm that I want to permanently delete this application."
        )
        delete_submitted = st.form_submit_button("Delete Application")

    if delete_submitted:
        if not confirmed_delete:
            st.error("Please confirm before deleting the application.")
        else:
            delete_application(application_options[delete_application_label])
            st.session_state["application_notice"] = "Application deleted successfully."
            st.rerun()

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
