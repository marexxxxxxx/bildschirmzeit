#!/bin/bash

echo "Installiere Hyprland Window Monitor..."

# 1. Skript platzieren
mkdir -p ~/.local/bin
cp window_monitor.py ~/.local/bin/
chmod +x ~/.local/bin/window_monitor.py
echo "Skript nach ~/.local/bin/ kopiert."

# 2. Systemd Service einrichten
mkdir -p ~/.config/systemd/user/
cp window-monitor.service ~/.config/systemd/user/
echo "Systemd-Service kopiert."

# 3. Dienst aktivieren und starten
systemctl --user daemon-reload
systemctl --user enable --now window-monitor.service
echo "Dienst aktiviert und gestartet."

echo "Installation abgeschlossen!"
