#!/usr/bin/env python3
"""
Hyprland Window Monitor
Liest das aktive Fenster sowie Fensterwechsel/-titeländerungen über den
Hyprland Event-Socket (socket2), speichert die Daten in einer SQLite-Datenbank,
berechnet die Dauer der Fensteraktivität und extrahiert App-/Projektnamen.
"""

import os
import re
import sys
import json
import socket
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------
# Datenbank-Setup
# ----------------------------------------------------------------------

DB_DIR = os.path.expanduser("~/.local/share/window_monitor")
DB_PATH = os.path.join(DB_DIR, "windows.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
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
    return conn

# ----------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------

def find_hyprland_socket():
    """Durchsucht die üblichen Pfade nach Hyprlands .socket2.sock."""
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    if sig:
        path = Path(runtime) / "hypr" / sig / ".socket2.sock"
        if path.is_socket():
            return str(path)

    base = Path(runtime) / "hypr"
    if base.is_dir():
        for hypr_dir in base.iterdir():
            candidate = hypr_dir / ".socket2.sock"
            if candidate.is_socket():
                return str(candidate)
    return None

def get_current_window_info():
    """Ruft das aktuell fokussierte Fenster via hyprctl ab."""
    try:
        res = subprocess.run(
            ["hyprctl", "-j", "activewindow"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if data and "class" in data:
                return data
    except Exception:
        pass
    return None

def extract_progress(title: str):
    """Sucht nach einer Zahl mit %-Zeichen im Fenstertitel."""
    if not title:
        return None
    match = re.search(r"(\d{1,3})\s*%", title)
    if match:
        return int(match.group(1))
    return None

def parse_title(cls, title):
    """Extrahiert App (bei Browsern) oder Projekt (bei IDEs) aus dem Titel."""
    app = None
    project = None
    if not cls or not title:
        return app, project

    cls_lower = cls.lower()
    parts = [p.strip() for p in title.split(" - ")]

    # Browser matching
    if any(b in cls_lower for b in ["chrome", "firefox", "brave", "edge", "chromium"]):
        if len(parts) >= 2:
            app = parts[-2]
        elif len(parts) == 1:
            app = parts[0]

    # IDE matching
    elif any(i in cls_lower for i in ["code", "cursor", "idea", "pycharm", "webstorm"]):
        if len(parts) >= 2:
            project = parts[-2]

    return app, project

# ----------------------------------------------------------------------
# Hauptlogik
# ----------------------------------------------------------------------

def main():
    socket_path = find_hyprland_socket()
    if not socket_path:
        print(json.dumps({"error": "Hyprland-Socket nicht gefunden"}), file=sys.stderr)
        sys.exit(1)

    conn = init_db()
    cursor = conn.cursor()

    prev_class = None
    prev_title = None
    current_event_id = None
    current_event_time = None

    def record_event(event_type, cls, title):
        nonlocal current_event_id, current_event_time
        now = datetime.now(timezone.utc)

        # Vorheriges Event schließen (Dauer berechnen)
        if current_event_id is not None and current_event_time is not None:
            duration = (now - current_event_time).total_seconds()
            cursor.execute('''
                UPDATE window_events
                SET end_timestamp = ?, duration = ?
                WHERE id = ?
            ''', (now.isoformat(), duration, current_event_id))
            conn.commit()

        prog = extract_progress(title)
        app, project = parse_title(cls, title)

        cursor.execute('''
            INSERT INTO window_events
            (timestamp, event_type, class, title, app, project, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (now.isoformat(), event_type, cls, title, app, project, prog))
        conn.commit()

        current_event_id = cursor.lastrowid
        current_event_time = now

        print(f"[{now.isoformat()}] {event_type}: '{cls}' / '{title}' (App: {app}, Projekt: {project}, Forts.: {prog}%)", flush=True)

    # Initialer Zustand
    initial = get_current_window_info()
    if initial:
        cls = initial.get("class", "")
        title = initial.get("title", "")
        record_event("initial", cls, title)
        prev_class, prev_title = cls, title
    else:
        record_event("initial", "", "")
        prev_class, prev_title = "", ""

    # Socket lesen
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(socket_path)
            buffer = ""

            while True:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    if line.startswith("activewindow>>"):
                        parts = line.split(">>", 1)[1]
                        if "," in parts:
                            cls, title = parts.split(",", 1)
                            title = title.strip()
                            if cls != prev_class or title != prev_title:
                                record_event("activewindow", cls, title)
                                prev_class, prev_title = cls, title

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        # Beim Beenden das letzte Event abschließen
        if current_event_id is not None and current_event_time is not None:
            now = datetime.now(timezone.utc)
            duration = (now - current_event_time).total_seconds()
            cursor.execute('''
                UPDATE window_events
                SET end_timestamp = ?, duration = ?
                WHERE id = ?
            ''', (now.isoformat(), duration, current_event_id))
            conn.commit()
        conn.close()

if __name__ == "__main__":
    main()
