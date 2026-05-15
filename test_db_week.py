import sqlite3
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

DB_DIR = os.path.expanduser("~/.local/share/window_monitor")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "windows.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get today's start in Zurich
zurich = ZoneInfo("Europe/Zurich")
now = datetime.now(zurich)
start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

events = []
# Create events for Monday to Sunday of the current week
current_weekday = start_of_today.weekday()
start_of_week = start_of_today - timedelta(days=current_weekday)

for i in range(7):
    day_dt = start_of_week + timedelta(days=i)

    # 2 hours Productivity
    events.append((
        day_dt.replace(hour=10, minute=0).astimezone(timezone.utc).isoformat(),
        7200, "activewindow", "Code", "VS Code", "Code", None, None
    ))

    # 1 hour Communication
    events.append((
        day_dt.replace(hour=13, minute=0).astimezone(timezone.utc).isoformat(),
        3600, "activewindow", "Slack", "Slack", "Slack", None, None
    ))

    # 30 mins Entertainment
    events.append((
        day_dt.replace(hour=20, minute=0).astimezone(timezone.utc).isoformat(),
        1800, "activewindow", "Discord", "Discord", "Discord", None, None
    ))

for ev in events:
    cursor.execute('''
        INSERT INTO window_events
        (timestamp, duration, event_type, class, title, app, project, progress)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ev)

conn.commit()
conn.close()
print("Test DB with weekly data populated")
