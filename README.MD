# Hyprland Window Monitor for Omarchy Linux

Ein Hintergrunddienst, der alle Fensterwechsel im Hyprland-Fenstermanager protokolliert. Er speichert die Klasse, den Titel, intelligent erkannte Apps (z.B. Chrome, Firefox) und Projekte (z.B. in VS Code) sowie die aktive Dauer jedes Fensters in einer lokalen SQLite-Datenbank.

## Installation & Aktivierung

1. **Skript platzieren**
   Kopiere das Skript `window_monitor.py` in ein Verzeichnis deiner Wahl, am besten nach `~/.local/bin/`. Mache es ausführbar:
   ```bash
   mkdir -p ~/.local/bin
   cp window_monitor.py ~/.local/bin/
   chmod +x ~/.local/bin/window_monitor.py
   ```

2. **Systemd Service einrichten**
   Kopiere die Datei `window-monitor.service` in das systemd-Verzeichnis für deinen Benutzer:
   ```bash
   mkdir -p ~/.config/systemd/user/
   cp window-monitor.service ~/.config/systemd/user/
   ```

3. **Dienst aktivieren und starten**
   Lade die systemd-Konfiguration neu und starte/aktiviere den Dienst:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now window-monitor.service
   ```
   *`enable --now` bewirkt, dass der Dienst sofort startet und bei jedem Login automatisch mitgestartet wird.*

## Deaktivieren des Dienstes

Wenn du den Dienst stoppen und nicht mehr automatisch starten möchtest:
```bash
systemctl --user disable --now window-monitor.service
```

## Überprüfen, ob der Dienst läuft

Du kannst den Status des Dienstes und die letzten Logs wie folgt abrufen:
```bash
systemctl --user status window-monitor.service
journalctl --user -u window-monitor.service -f
```

## Die Datenbank

Die Daten werden in einer SQLite-Datenbank unter folgendem Pfad gespeichert:
`~/.local/share/window_monitor/windows.db`

### Schema der Tabelle `window_events`

| Spalte | Datentyp | Beschreibung |
|--------|----------|--------------|
| `id` | INTEGER | Eindeutige ID des Eintrags |
| `timestamp` | TEXT | ISO-Zeitstempel, wann das Fenster fokussiert wurde |
| `end_timestamp` | TEXT | ISO-Zeitstempel, wann der Fokus gewechselt hat |
| `duration` | REAL | Wie lange das Fenster aktiv war (in Sekunden) |
| `event_type` | TEXT | Meist `activewindow` oder `initial` |
| `class` | TEXT | Die Fenster-Klasse (z.B. `google-chrome`) |
| `title` | TEXT | Der komplette Fenstertitel |
| `app` | TEXT | Extrahierte App, z.B. `YouTube` (bei Browsern) |
| `project` | TEXT | Extrahiertes Projekt (bei IDEs wie VS Code) |
| `progress` | INTEGER | Ein erkannter Prozentwert im Titel (z.B. für Downloads) |

### Abfragen der Daten (Beispiele)

Du kannst die Datenbank jederzeit z.B. mit `sqlite3` abfragen. (Falls nicht installiert: `sudo pacman -S sqlite`)

**Alle Einträge ansehen:**
```bash
sqlite3 ~/.local/share/window_monitor/windows.db "SELECT * FROM window_events;"
```

**Wie viel Zeit in welchem Projekt verbracht wurde:**
```bash
sqlite3 ~/.local/share/window_monitor/windows.db \
"SELECT project, SUM(duration)/60 as minutes FROM window_events WHERE project IS NOT NULL GROUP BY project ORDER BY minutes DESC;"
```

**Welche Apps (z.B. in Chrome) am längsten aktiv waren:**
```bash
sqlite3 ~/.local/share/window_monitor/windows.db \
"SELECT app, SUM(duration)/60 as minutes FROM window_events WHERE app IS NOT NULL GROUP BY app ORDER BY minutes DESC;"
```
