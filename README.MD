# Hyprland Window Monitor for Omarchy Linux

Ein Hintergrunddienst, der alle Fensterwechsel im Hyprland-Fenstermanager protokolliert. Er speichert die Klasse, den Titel, intelligent erkannte Apps (z.B. Chrome, Firefox) und Projekte (z.B. in VS Code) sowie die aktive Dauer jedes Fensters in einer lokalen SQLite-Datenbank.

## Installation & Aktivierung

Um den Time Tracker zu installieren und in Omarchy (https://omarchy.org/) zu integrieren, so dass die Zeit getrackt wird, führe das Installationsskript aus:

```bash
./install.sh
```

Dieses Skript kopiert das Monitor-Skript an die richtige Stelle (`~/.local/bin/`), richtet den systemd-Service ein (`~/.config/systemd/user/`) und startet/aktiviert den Dienst automatisch.

## Deaktivieren und Entfernen des Dienstes

Wenn du den Dienst stoppen, deaktivieren und löschen möchtest, führe das Entfernen-Skript aus:

```bash
./remove.sh
```

Dieses Skript beendet den Dienst, entfernt die Dateien und lädt die systemd-Konfiguration neu. Die Datenbank bleibt zur Sicherheit erhalten.

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
