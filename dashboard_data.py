import sqlite3
import os
from datetime import datetime, timezone, timedelta
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
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_of_day.isoformat(), end_of_day.isoformat()

def fetch_today_data():
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    start, end = get_today_bounds()

    cursor.execute('''
        SELECT * FROM window_events
        WHERE timestamp >= ? AND timestamp <= ? AND duration IS NOT NULL
    ''', (start, end))

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_total_screen_time():
    data = fetch_today_data()
    total_seconds = sum(row['duration'] for row in data if row['duration'])
    return total_seconds

def get_week_bounds():
    zurich = ZoneInfo("Europe/Zurich")
    now = datetime.now(zurich)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    current_weekday = start_of_today.weekday()
    start_of_week = start_of_today - timedelta(days=current_weekday)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    return start_of_week.astimezone(timezone.utc).isoformat(), end_of_week.astimezone(timezone.utc).isoformat()

def fetch_week_data():
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    start, end = get_week_bounds()

    cursor.execute('''
        SELECT * FROM window_events
        WHERE timestamp >= ? AND timestamp <= ? AND duration IS NOT NULL
    ''', (start, end))

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_weekly_usage_by_day_and_category():
    data = fetch_week_data()
    # Initialize days 0 (Monday) to 6 (Sunday)
    weekly_data = {
        i: {"Productivity": 0.0, "Communication": 0.0, "Entertainment": 0.0, "Other": 0.0}
        for i in range(7)
    }

    zurich = ZoneInfo("Europe/Zurich")

    for row in data:
        try:
            dt = datetime.fromisoformat(row['timestamp'])
            # Convert UTC DB timestamp to Zurich time to get correct weekday
            dt_zurich = dt.astimezone(zurich)
            weekday = dt_zurich.weekday()

            app_name = row['app'] if row['app'] else row['class']
            if not app_name:
                continue

            duration = row['duration']
            cat = CATEGORY_MAP.get(app_name, "Other")

            if weekday in weekly_data:
                weekly_data[weekday][cat] += duration
        except Exception:
            pass

    return weekly_data

def get_most_used_apps():
    data = fetch_today_data()
    apps = {}

    for row in data:
        # Fallback to class if app is None
        app_name = row['app'] if row['app'] else row['class']
        if not app_name:
            continue

        if app_name not in apps:
            apps[app_name] = {'duration': 0.0, 'class': row['class']}
        apps[app_name]['duration'] += row['duration']

    # Sort by duration descending
    sorted_apps = []
    for name, info in sorted(apps.items(), key=lambda item: item[1]['duration'], reverse=True):
        sorted_apps.append((name, info['duration'], info['class']))

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
    print(f"Weekly Usage: {get_weekly_usage_by_day_and_category()}")
    print(f"Most Used: {get_most_used_apps()}")
    print(f"Categories: {get_categories()}")
