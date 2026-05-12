#!/bin/bash
while true; do
    output=$(hyprctl -j activewindow 2>/dev/null)
    if [ -n "$output" ]; then
        class=$(echo "$output" | jq -r '.class // ""')
        title=$(echo "$output" | jq -r '.title // ""')
        # Nur ausgeben, wenn sich etwas ändert
        if [ "$class" != "$prev_class" ] || [ "$title" != "$prev_title" ]; then
            echo "Fenster: class='$class' title='$title'"
            prev_class="$class"
            prev_title="$title"
        fi
    fi
    sleep 1
done
