#!/bin/bash

echo "Entferne Hyprland Window Monitor..."

# 1. Dienst stoppen und deaktivieren
systemctl --user disable --now window-monitor.service
echo "Dienst gestoppt und deaktiviert."

# 2. Dateien entfernen
rm -f ~/.local/bin/window_monitor.py
rm -f ~/.config/systemd/user/window-monitor.service
echo "Dateien entfernt."

# 3. Systemd neu laden
systemctl --user daemon-reload
echo "Systemd-Konfiguration neu geladen."

echo "Deinstallation abgeschlossen! Die Datenbank unter ~/.local/share/window_monitor/windows.db bleibt erhalten."
