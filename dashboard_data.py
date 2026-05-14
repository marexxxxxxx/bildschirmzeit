import sqlite3
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DB_PATH = os.path.expanduser("~/.local/share/window_monitor/windows.db")

# Sample Category Mapping
CATEGORY_MAP = {
    "Code": "Productivity",
    "Cursor": "Productivity",
    "Kitty": "Productivity",
    "Alacritty": "Productivity",
    "Google Chrome": "Communication",
    "Firefox": "Communication",
    "Slack": "Communication",
    "Discord": "Entertainment",
    "Spotify": "Entertainment",
}

def get_today_bounds():
    tz = ZoneInfo("Europe/Zurich")
    now = datetime.now(tz)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Store in DB as UTC ISO format, so we need to convert boundaries to UTC
    start_utc = start_of_day.astimezone(timezone.utc)
    end_utc = end_of_day.astimezone(timezone.utc)
    return start_utc.isoformat(), end_utc.isoformat()

def fetch_today_data():
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    start_str, end_str = get_today_bounds()

    # Get events that started before end of today AND ended after start of today
    cursor.execute('''
        SELECT * FROM window_events
        WHERE timestamp <= ? AND end_timestamp >= ? AND duration IS NOT NULL
    ''', (end_str, start_str))

    rows = cursor.fetchall()
    conn.close()

    start_dt = datetime.fromisoformat(start_str)
    end_dt = datetime.fromisoformat(end_str)

    processed_rows = []
    for row in rows:
        row_dict = dict(row)
        event_start = datetime.fromisoformat(row_dict['timestamp'])
        event_end = datetime.fromisoformat(row_dict['end_timestamp'])

        # Calculate overlap
        overlap_start = max(event_start, start_dt)
        overlap_end = min(event_end, end_dt)

        overlap_duration = (overlap_end - overlap_start).total_seconds()
        if overlap_duration > 0:
            row_dict['duration'] = overlap_duration
            # Also update timestamp so it falls inside today's hours if it started yesterday
            row_dict['timestamp'] = overlap_start.isoformat()
            processed_rows.append(row_dict)

    return processed_rows

def get_total_screen_time():
    data = fetch_today_data()
    total_seconds = sum(row['duration'] for row in data if row['duration'])
    return total_seconds

def get_daily_usage_by_hour():
    data = fetch_today_data()
    # Initialize hours from 6 to 21 (9 PM)
    hours = {h: 0.0 for h in range(6, 22)}

    for row in data:
        try:
            dt = datetime.fromisoformat(row['timestamp'])
            hour = dt.hour
            if hour in hours:
                hours[hour] += row['duration']
        except Exception:
            pass

    return hours

def get_most_used_apps():
    data = fetch_today_data()
    apps = {}

    for row in data:
        # Fallback to class if app is None
        app_name = row['app'] if row['app'] else row['class']
        if not app_name:
            continue

        if app_name not in apps:
            apps[app_name] = 0.0
        apps[app_name] += row['duration']

    # Sort by duration descending
    sorted_apps = sorted(apps.items(), key=lambda item: item[1], reverse=True)
    return sorted_apps

def get_categories():
    data = fetch_today_data()
    categories = {"Productivity": 0.0, "Communication": 0.0, "Entertainment": 0.0, "Other": 0.0}
    total = 0.0

    for row in data:
        app_name = row['app'] if row['app'] else row['class']
        if not app_name:
            continue

        duration = row['duration']
        total += duration

        cat = CATEGORY_MAP.get(app_name, "Other")
        categories[cat] += duration

    percentages = {}
    if total > 0:
        for cat, dur in categories.items():
            percentages[cat] = (dur / total) * 100
    else:
        for cat in categories:
            percentages[cat] = 0.0

    return percentages

if __name__ == "__main__":
    print(f"Total: {get_total_screen_time()}s")
    print(f"Daily Usage: {get_daily_usage_by_hour()}")
    print(f"Most Used: {get_most_used_apps()}")
    print(f"Categories: {get_categories()}")
