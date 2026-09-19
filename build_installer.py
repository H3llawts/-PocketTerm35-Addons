from pathlib import Path
root=Path(__file__).resolve().parent
header='''#!/usr/bin/env bash
# Self-contained installer for Raspberry Pi OS Bookworm/Trixie.
set -Eeuo pipefail
trap 'echo "Install stopped at line $LINENO. Fix the reported error and rerun; do not assume installation succeeded." >&2' ERR
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
apt-get update
apt-get install -y python3 python3-smbus2 python3-evdev
install -d -m 755 /opt/pocketterm35-addons/trackball
# Stop our service before updating or probing; never run two readers at once.
systemctl stop pocketterm35-trackball.service 2>/dev/null || true
'''
parts=[header]
for src,dst in [('trackball/trackball_mouse.py','/opt/pocketterm35-addons/trackball/trackball_mouse.py'),('trackball/trackball.ini','/etc/pocketterm35-trackball.ini'),('trackball/pocketterm35-trackball.service','/etc/systemd/system/pocketterm35-trackball.service')]:
 if src.endswith('.ini'): parts.append(f'if [[ ! -e {dst} ]]; then\n')
 parts.append(f"cat > {dst} <<'POCKETTERM_EOF'\n{(root/src).read_text()}POCKETTERM_EOF\nchmod 644 {dst}\n")
 if src.endswith('.ini'): parts.append('fi\n')
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
