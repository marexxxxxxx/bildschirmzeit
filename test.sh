#!/bin/bash

# === Funktion zum Finden des Hyprland-Event-Sockets ===
find_socket() {
    local sig="${HYPRLAND_INSTANCE_SIGNATURE}"
    local runtime="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

    # Methode 1: über die Signatur-Umgebungsvariable
    if [[ -n "$sig" ]]; then
        local socket_path="$runtime/hypr/$sig/.socket2.sock"
        if [[ -S "$socket_path" ]]; then
            echo "$socket_path"
            return
        fi
    fi

    # Methode 2: Erstes passendes Verzeichnis durchsuchen
    for dir in "$runtime"/hypr/*; do
        local candidate="$dir/.socket2.sock"
        if [[ -S "$candidate" ]]; then
            echo "$candidate"
            return
        fi
    done
}

# === Aktuelles Fenster über hyprctl (JSON) ermitteln ===
get_current_info() {
    hyprctl -j activewindow 2>/dev/null | jq -r '[.class, .title] | @tsv' 2>/dev/null
}

# === Fortschritt aus Titel extrahieren (z. B. "Download (73%)") ===
extract_progress() {
    local title="$1"
    if [[ "$title" =~ ([0-9]{1,3})% ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

# === Hauptprogramm ===
SOCKET=$(find_socket)
if [[ -z "$SOCKET" ]]; then
    echo "FEHLER: Hyprland Socket2 nicht gefunden. Läuft Hyprland und wird das Skript in der Session ausgeführt?"
    exit 1
fi

# socat muss installiert sein (auf Omarchy: sudo pacman -S socat)
if ! command -v socat &> /dev/null; then
    echo "FEHLER: socat ist nicht installiert. Bitte mit 'sudo pacman -S socat' nachrüsten."
    exit 1
fi

# Initialen Zustand holen und ausgeben
prev_line=""
init_info=$(get_current_info)
if [[ -n "$init_info" ]]; then
    IFS=$'\t' read -r prev_class prev_title <<< "$init_info"
    echo "Start: class='$prev_class' title='$prev_title'"
    # Schon beim Start prüfen, ob ein Fortschritt im Titel steht
    progress=$(extract_progress "$prev_title")
    [[ -n "$progress" ]] && echo "  → Fortschritt: $progress%"
fi

# Auf Events lauschen
socat -u UNIX-CONNECT:"$SOCKET" - | while read -r line; do
    if [[ "$line" == activewindow\>\>* ]]; then
        # Format: activewindow>>class,title
        IFS=',' read -r class title <<< "${line#activewindow>>}"
        # Leerzeichen am Ende entfernen (sicherheitshalber)
        title="${title%"${title##*[![:space:]]}"}"
        # Nur bei Änderung ausgeben (vergleiche mit letztem bekannten Zustand)
        if [[ "$class" != "$prev_class" || "$title" != "$prev_title" ]]; then
            prev_class="$class"
            prev_title="$title"
            echo "Fokus/Titel geändert: class='$class' title='$title'"
            progress=$(extract_progress "$title")
            [[ -n "$progress" ]] && echo "  → Fortschritt: $progress%"
        fi
    elif [[ "$line" == closewindow\>\>* ]]; then
        echo "Fenster geschlossen: ${line#closewindow>>}"
        # Optional: Wenn das geschlossene Fenster das aktive war, zurücksetzen
        # hyprctl -j activewindow liefert dann den neuen Fokus; das merkt unser nächster activewindow-Event von selbst.
    fi
done
