import sqlite3
from pathlib import Path

# Store the database in the same folder as this Python file.
database_path = Path(__file__).resolve().parent / "placements.db"

connection = sqlite3.connect(database_path)
try:
    # Create the applications table if it has not already been created.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            application_date TEXT,
            status TEXT,
            interview_date TEXT
        )
    """)

    # Add the new optional column when initializing an older database.
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(applications)")
    }
    if "interview_date" not in columns:
        connection.execute("ALTER TABLE applications ADD COLUMN interview_date TEXT")

    # Save the table changes.
    connection.commit()
finally:
    # Always close the database connection.
    connection.close()

# Let the user know the database and table are ready.
print("Database and applications table are ready.")
