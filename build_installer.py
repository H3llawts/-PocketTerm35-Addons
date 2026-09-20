from pathlib import Path
root=Path(__file__).resolve().parent
header='''#!/usr/bin/env bash
# Self-contained installer for Raspberry Pi OS Bookworm/Trixie.
set -Eeuo pipefail
trap 'echo "Install stopped at line $LINENO. Fix the reported error and rerun; do not assume installation succeeded." >&2' ERR
if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: sudo bash $0 [--rotation 0|90|180|270] [--speed 0.1..20] [--red 0..255] [--green 0..255] [--blue 0..255] [--white 0..255]"
  echo "Omitted options preserve existing settings, or use defaults on first install."
  exit 0
fi
if (( EUID != 0 )); then
  echo "Run: sudo bash $0" >&2
  exit 1
fi
if [[ ! -r /proc/device-tree/model ]] || ! grep -aq 'Raspberry Pi' /proc/device-tree/model; then
  echo "This installer requires a Raspberry Pi." >&2
  exit 1
fi
if [[ ! -d /run/systemd/system ]] || ! command -v apt-get >/dev/null; then
  echo "Requires Raspberry Pi OS with apt and systemd." >&2
  exit 1
fi
exec 9>/run/lock/pocketterm35-trackball-install.lock
flock -n 9 || { echo "Another installation is running." >&2; exit 1; }
boot=/boot/firmware/config.txt
[[ -f "$boot" ]] || boot=/boot/config.txt
[[ -f "$boot" ]] || { echo "Cannot find boot config.txt." >&2; exit 1; }
command -v python3 >/dev/null || { echo "Install python3 first." >&2; exit 1; }
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
'''
parts=[header]
for name in ('trackball_mouse.py', 'configure.py', 'trackball.ini', 'pocketterm35-trackball.service'):
 parts.append(f"cat > \"$stage/{name}\" <<'POCKETTERM_EOF'\n{(root/'trackball'/name).read_text()}POCKETTERM_EOF\n")
parts.append('''# Validate all options before apt, service changes or configuration writes.
/usr/bin/python3 "$stage/configure.py" --existing /etc/pocketterm35-trackball.ini --defaults "$stage/trackball.ini" --output "$stage/config.ini" "$@"
apt-get update
apt-get install -y python3 python3-smbus2 python3-evdev
install -d -m 755 /opt/pocketterm35-addons/trackball
systemctl stop pocketterm35-trackball.service 2>/dev/null || true
if [[ -f /etc/pocketterm35-trackball.ini ]]; then
  cp -p /etc/pocketterm35-trackball.ini "/etc/pocketterm35-trackball.ini.backup.$(date +%Y%m%d-%H%M%S)"
fi
install -m 644 "$stage/trackball_mouse.py" /opt/pocketterm35-addons/trackball/trackball_mouse.py
install -m 644 "$stage/config.ini" /etc/pocketterm35-trackball.ini
install -m 644 "$stage/pocketterm35-trackball.service" /etc/systemd/system/pocketterm35-trackball.service
''')
parts.append('''# Validate preserved user settings before enabling the service.
/usr/bin/python3 - <<'CONFIG_CHECK'
import sys
sys.path.insert(0, '/opt/pocketterm35-addons/trackball')
from trackball_mouse import settings
settings()
CONFIG_CHECK
# Append one clearly marked block; preserve every existing overlay and setting.
if ! grep -q '^# BEGIN PocketTerm35 trackball$' "$boot"; then
  cp -p "$boot" "${boot}.before-trackball.$(date +%Y%m%d-%H%M%S)"
  cat >> "$boot" <<'BOOT_EOF'

# BEGIN PocketTerm35 trackball
[all]
dtparam=i2c_arm=on
# END PocketTerm35 trackball
BOOT_EOF
fi
printf 'i2c-dev\\nuinput\\n' > /etc/modules-load.d/pocketterm35-trackball.conf
modprobe i2c-dev
modprobe uinput
systemctl daemon-reload
systemctl enable pocketterm35-trackball.service
if /usr/bin/python3 /opt/pocketterm35-addons/trackball/trackball_mouse.py --probe; then
  systemctl restart pocketterm35-trackball.service
  sleep 2
  if systemctl is-active --quiet pocketterm35-trackball.service; then
    echo "Trackball detected and service running. Automatic boot startup enabled."
  else
    journalctl -u pocketterm35-trackball.service -n 20 --no-pager
    exit 1
  fi
else
  echo "Installed and enabled, but the trackball is NOT detected yet."
  echo "If I2C was disabled, reboot once: sudo reboot"
  echo "Otherwise check wiring, bus and address in /etc/pocketterm35-trackball.ini."
  echo "After correcting wiring: sudo systemctl restart pocketterm35-trackball"
  echo "The boot service will retry automatically every five seconds."
  exit 2
fi
''')
(root/'install-trackball.sh').write_text(''.join(parts))
