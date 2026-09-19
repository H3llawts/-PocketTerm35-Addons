#!/usr/bin/env bash
set -euo pipefail
(( EUID == 0 )) || { echo "Run with sudo bash."; exit 1; }
systemctl disable --now pocketterm35-trackball.service || true
rm -f /etc/systemd/system/pocketterm35-trackball.service
rm -f /etc/modules-load.d/pocketterm35-trackball.conf
rm -f /opt/pocketterm35-addons/trackball/trackball_mouse.py
systemctl daemon-reload
# Preserve I2C, installed packages, boot backup and tuning configuration:
# other PocketTerm peripherals may need these.
echo "Trackball service removed. I2C and /etc/pocketterm35-trackball.ini preserved."
