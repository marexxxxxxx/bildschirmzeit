#!/bin/bash
HIS=$(echo $HYPRLAND_INSTANCE_SIGNATURE)
EVENT_SOCKET="$XDG_RUNTIME_DIR/hypr/$HIS/.socket2.sock"

# Auf das Event 'activewindow' lauschen und Details holen
socat -u UNIX-CONNECT:"$EVENT_SOCKET" - | while read -r line; do
    case "$line" in
        activewindow\>\>*)
            class=$(echo "$line" | cut -d '>' -f 2 | cut -d ',' -f 1)
            title=$(echo "$line" | cut -d '>' -f 2 | cut -d ',' -f 2)
            echo "Aktives Fenster gewechselt: Class='$class', Title='$title'"
            ;;
    esac
done
