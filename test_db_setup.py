import sqlite3
import os
from datetime import datetime, timezone, timedelta

DB_DIR = os.path.expanduser("~/.local/share/window_monitor")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "windows.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS window_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        end_timestamp TEXT,
        duration REAL,
        event_type TEXT,
        class TEXT,
        title TEXT,
        app TEXT,
        project TEXT,
        progress INTEGER
    )
''')

# insert some test data for today
now = datetime.now(timezone.utc)
events = [
    # 2 hours on VS Code
    (now.replace(hour=8, minute=0).isoformat(), 7200, "activewindow", "Code", "project.py - VS Code", "Code", "project", None),
    # 1 hour on Chrome
    (now.replace(hour=10, minute=30).isoformat(), 3600, "activewindow", "Google-chrome", "Google - Google Chrome", "Google Chrome", None, None),
    # 30 mins on Slack
    (now.replace(hour=14, minute=0).isoformat(), 1800, "activewindow", "Slack", "Slack - general", "Slack", None, None),
]

for ev in events:
    cursor.execute('''
        INSERT INTO window_events
        (timestamp, duration, event_type, class, title, app, project, progress)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ev)

conn.commit()
conn.close()
print("Test DB created")
