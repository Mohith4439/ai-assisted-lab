# Placement Application Tracker

A beginner-friendly application tracker built with Python, Streamlit, and SQLite.

## Run the application

1. Install Python.
2. Open a terminal in this project folder.
3. Install the required Python packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create the SQLite database and its table:

   ```bash
   python init_db.py
   ```

5. Start the Streamlit app:

   ```bash
   streamlit run app.py
   ```

The app lets you add and view applications, see the total number of applications,
find the most frequently applied-for role, and view a summary of applications by
status.

The `placements.db` database is created on your computer and is intentionally
excluded from Git so personal application data is not published.
