#!/usr/bin/env python3
"""
Hyprland Window JSON Monitor
Liest das aktive Fenster sowie Fensterwechsel/-titeländerungen über den
Hyprland Event-Socket (socket2) und gibt strukturierte JSON-Zeilen aus.
"""

import os
import re
import sys
import json
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------

def find_hyprland_socket():
    """Durchsucht die üblichen Pfade nach Hyprlands .socket2.sock."""
    # 1. Umgebungsvariable HYPRLAND_INSTANCE_SIGNATURE
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    if sig:
        path = Path(runtime) / "hypr" / sig / ".socket2.sock"
        if path.is_socket():
            return str(path)

    # 2. Fallback: alle hypr/*-Ordner durchsuchen
    base = Path(runtime) / "hypr"
    if base.is_dir():
        for hypr_dir in base.iterdir():
            candidate = hypr_dir / ".socket2.sock"
            if candidate.is_socket():
                return str(candidate)
    return None


def get_current_window_info():
    """Ruft das aktuell fokussierte Fenster via hyprctl -j ab."""
    try:
        res = subprocess.run(
            ["hyprctl", "-j", "activewindow"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            return json.loads(res.stdout)
    except Exception:
        pass
    return None


def extract_progress(title: str):
    """Sucht nach einer Zahl mit %-Zeichen im Fenstertitel."""
    if title is None:
        return None
    match = re.search(r"(\d{1,3})\s*%", title)
    if match:
        return int(match.group(1))
    return None


def format_json(event, cls=None, title=None, address=None, progress=None):
    """Erzeugt ein JSON-Objekt als String (eine Zeile)."""
    obj = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if address:                     # closewindow-Event
        obj["address"] = address
    else:
        obj["class"] = cls or ""
        obj["title"] = title or ""
        obj["progress"] = progress  # int oder None
    return json.dumps(obj, ensure_ascii=False)


# ----------------------------------------------------------------------
# Hauptlogik
# ----------------------------------------------------------------------

def main():
    socket_path = find_hyprland_socket()
    if not socket_path:
        print(json.dumps({"error": "Hyprland-Socket nicht gefunden"}), file=sys.stderr)
        sys.exit(1)

    # Initialen Zustand holen und ausgeben
    prev_class = None
    prev_title = None

    initial = get_current_window_info()
    if initial:
        cls = initial.get("class", "")
        title = initial.get("title", "")
        prog = extract_progress(title)
        print(format_json("initial", cls, title, progress=prog))
        prev_class, prev_title = cls, title
    else:
        # Trotzdem eine initiale Zeile ausgeben, damit der Stream nie leer beginnt
        print(format_json("initial", "", "", progress=None))
        prev_class, prev_title = "", ""

    # Event-Socket öffnen und lesen
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
                            # Nur ausgeben, wenn sich Klasse oder Titel geändert haben
                            if cls != prev_class or title != prev_title:
                                prev_class, prev_title = cls, title
                                prog = extract_progress(title)
                                print(format_json("activewindow", cls, title, progress=prog))

                    elif line.startswith("closewindow>>"):
                        addr = line.split(">>", 1)[1].strip()
                        print(format_json("closewindow", address=addr))

    except KeyboardInterrupt:
        # Beim sauberen Beenden nichts unternehmen
        pass
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
