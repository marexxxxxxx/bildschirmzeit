import argparse
import subprocess
import os
import signal
import sys

# Verwende ~/.local/state oder XDG_RUNTIME_DIR anstelle von /tmp für mehr Sicherheit
def get_pid_dir():
    # Versuche XDG_RUNTIME_DIR (Standard in systemd/Wayland-Umgebungen)
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        d = os.path.join(runtime_dir, "hypr_blocker")
    else:
        # Fallback auf lokalen State-Ordner des Users
        d = os.path.expanduser("~/.local/state/hypr_blocker")

    os.makedirs(d, exist_ok=True)
    return d

def get_pid_file_path(title):
    # Einfache Bereinigung für den Dateinamen
    safe_title = "".join(c if c.isalnum() else "_" for c in title)
    return os.path.join(get_pid_dir(), f"hypr_blocker_{safe_title}.pid")

def block_window(title, image_path=None):
    pid_file = get_pid_file_path(title)

    # Prüfe, ob bereits geblockt
    if os.path.exists(pid_file):
        print(f"[{title}] Ist bereits blockiert. PID-Datei existiert: {pid_file}")
        return False

    cmd = ['python3', 'overlay_block.py', '--title', title]
    if image_path:
        cmd += ['--image', image_path]

    try:
        # Die Umgebungsvariablen müssen weitergegeben werden, speziell WAYLAND_DISPLAY etc.
        env = os.environ.copy()

        # Set LD_PRELOAD for Gtk4LayerShell if the library exists
        lib_path = '/usr/lib/libgtk4-layer-shell.so'
        if os.path.exists(lib_path):
            env['LD_PRELOAD'] = lib_path

        proc = subprocess.Popen(cmd, env=env)

        with open(pid_file, "w") as f:
            f.write(str(proc.pid))

        print(f"[{title}] Erfolgreich blockiert. Overlay läuft mit PID {proc.pid}.")
        return True
    except Exception as e:
        print(f"Fehler beim Starten des Overlays für '{title}': {e}")
        return False

def unblock_window(title):
    pid_file = get_pid_file_path(title)

    if not os.path.exists(pid_file):
        print(f"[{title}] Keine aktive Sperre gefunden (PID-Datei nicht vorhanden).")
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)
        print(f"[{title}] Sperre erfolgreich aufgehoben (PID {pid} beendet).")
    except ProcessLookupError:
        print(f"[{title}] Prozess existiert nicht mehr, räume nur PID-Datei auf.")
    except Exception as e:
        print(f"Fehler beim Beenden des Overlays für '{title}': {e}")
    finally:
        if os.path.exists(pid_file):
            os.remove(pid_file)

    return True

def main():
    parser = argparse.ArgumentParser(description="Tracker Backend CLI für Window Blocking")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Befehl (block oder unblock)")

    block_parser = subparsers.add_parser("block", help="Blockiert ein Fenster")
    block_parser.add_argument("title", help="Titel des Fensters, das blockiert werden soll")
    block_parser.add_argument("--image", help="Optionales Bild für das Overlay", default=None)

    unblock_parser = subparsers.add_parser("unblock", help="Hebt die Sperrung eines Fensters auf")
    unblock_parser.add_argument("title", help="Titel des Fensters, das freigegeben werden soll")

    args = parser.parse_args()

    if args.command == "block":
        block_window(args.title, args.image)
    elif args.command == "unblock":
        unblock_window(args.title)

if __name__ == "__main__":
    main()
