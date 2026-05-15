import sqlite3
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

DB_PATH = os.path.expanduser("~/.local/share/window_monitor/windows.db")

# Sample Category Mapping (Used to seed DB if empty)
INITIAL_CATEGORY_MAP = {
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

def init_categories_db():
    if not os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure tables exist (in case of an old database)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            color TEXT,
            is_productive BOOLEAN
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category_mapping (
            app_name TEXT PRIMARY KEY,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()

    # Check if we have any categories
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        # Seed initial categories
        categories_to_seed = {
            "Productivity": ("#64B5F6", True),
            "Communication": ("#81C784", False),
            "Entertainment": ("#FFB74D", False),
            "Other": ("#9E9E9E", False)
        }
        for cat_name, (color, is_prod) in categories_to_seed.items():
            cursor.execute("INSERT INTO categories (name, color, is_productive) VALUES (?, ?, ?)", (cat_name, color, is_prod))

        # Seed initial mappings
        cursor.execute("SELECT id, name FROM categories")
        cat_rows = cursor.fetchall()
        cat_id_map = {row[1]: row[0] for row in cat_rows}

        for app, cat_name in INITIAL_CATEGORY_MAP.items():
            cat_id = cat_id_map.get(cat_name)
            if cat_id:
                cursor.execute("INSERT INTO category_mapping (app_name, category_id) VALUES (?, ?)", (app, cat_id))

        conn.commit()

    conn.close()

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

def get_app_category_map():
    if not os.path.exists(DB_PATH):
        return {}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cm.app_name, c.name
        FROM category_mapping cm
        JOIN categories c ON cm.category_id = c.id
    ''')
    mapping = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return mapping

def get_weekly_usage_by_day_and_category():
    data = fetch_week_data()

    # Initialize with base categories, dynamically add others if found
    base_cats = ["Productivity", "Communication", "Entertainment", "Other"]
    weekly_data = {
        i: {cat: 0.0 for cat in base_cats}
        for i in range(7)
    }

    zurich = ZoneInfo("Europe/Zurich")
    app_cat_map = get_app_category_map()

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
            cat = app_cat_map.get(app_name, "Other")

            if weekday in weekly_data:
                if cat not in weekly_data[weekday]:
                    weekly_data[weekday][cat] = 0.0
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

    app_cat_map = get_app_category_map()

    for row in data:
        app_name = row['app'] if row['app'] else row['class']
        if not app_name:
            continue

        duration = row['duration']
        total += duration

        cat = app_cat_map.get(app_name, "Other")
        if cat not in categories:
            categories[cat] = 0.0
        categories[cat] += duration

    percentages = {}
    if total > 0:
        for cat, dur in categories.items():
            percentages[cat] = (dur / total) * 100
    else:
        for cat in categories:
            percentages[cat] = 0.0

    return percentages

def get_all_categories():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    cats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cats

def add_category(name, color, is_productive):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name, color, is_productive) VALUES (?, ?, ?)",
                       (name, color, is_productive))
        conn.commit()
        cat_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cat_id = None
    finally:
        conn.close()
    return cat_id

def delete_category(category_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()

def assign_apps_to_category(category_id, app_names_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for app_name in app_names_list:
        cursor.execute('''
            INSERT INTO category_mapping (app_name, category_id)
            VALUES (?, ?)
            ON CONFLICT(app_name) DO UPDATE SET category_id=excluded.category_id
        ''', (app_name, category_id))

    conn.commit()
    conn.close()

def get_all_tracked_apps():
    """Returns a list of unique app names (or fallback to class) tracked in the DB so far."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT app, class FROM window_events")

    apps = set()
    for row in cursor.fetchall():
        app_name = row[0] if row[0] else row[1]
        if app_name:
            apps.add(app_name)

    conn.close()
    return list(apps)

if __name__ == "__main__":
    print(f"Total: {get_total_screen_time()}s")
    print(f"Weekly Usage: {get_weekly_usage_by_day_and_category()}")
    print(f"Most Used: {get_most_used_apps()}")
    print(f"Categories: {get_categories()}")
