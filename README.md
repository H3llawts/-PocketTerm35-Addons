# PocketTerm35 Addons

Addons for a Waveshare PocketTerm35, starting with the Pimoroni I2C Trackball Breakout. Intended first target: Raspberry Pi 4, Raspberry Pi OS Trixie, Waveshare preconfigured image. Bookworm should also work. Other operating systems and Pi 5 are not validated.

## Hardware wiring

Shut down and disconnect power before wiring. Use the Pi's **physical header numbers**, not a connector's pin order. Check the actual PocketTerm board labels before soldering.

| Trackball | Raspberry Pi signal | Physical header pin |
| --- | --- | --- |
| 3–5V / VIN | 3.3V | 1 or 17 |
| GND | Ground | 6 (or another GND) |
| SDA | GPIO2 / SDA1 | 3 |
| SCL | GPIO3 / SCL1 | 5 |
| INT | Unconnected (polled) | — |

Default address is 0x0A; change configuration to 0x0B if the module is configured for its alternate address. I2C lines can be shared with other devices with different addresses. No PocketTerm internal solder pad or accessory connector pinout is assumed here.

## One-run install

Download `install-trackball.sh` to the Pi, open a terminal in its folder, and run:

```bash
sudo bash install-trackball.sh
```

### Set rotation, speed and brightness during installation

For Rob's rear mounting, slower motion and brighter green illumination:

```bash
sudo bash install-trackball.sh --rotation 90 --speed 1.0 --green 128
```

Supported options: `--rotation 0|90|180|270`, `--speed 0.1..20`, and `--red`, `--green`, `--blue`, `--white` (each 0..255). Green 128 is brighter than the default 12; 255 is maximum. Speed 1.0 halves the driver's movement scaling compared with the default 2.0; desktop acceleration can also affect perceived speed.

Omitted settings retain the installed values, or use defaults on first installation. Explicit options override only those settings. Values are validated before package installation or service changes; existing configuration is backed up before replacement. Run `bash install-trackball.sh --help` for usage.

For an already working installation, edit `/etc/pocketterm35-trackball.ini` and restart `pocketterm35-trackball` to apply tuning without reinstalling.

This is self-contained: the other repository files are not needed to install. An internet connection is needed for Debian packages. No pip, virtual environment, desktop autostart entry or login is needed.

The installer installs OS-packaged `python3-smbus2` and `python3-evdev`, backs up boot config before appending an I2C-enable block, preserves existing overlays, enables i2c-dev/uinput at boot, validates the chip identity, and enables a systemd service. Re-running preserves your tuning config. It never reboots automatically.

If I2C was off, the first run may exit **2**, reporting installed but hardware not detected. Run `sudo reboot` once. A successful installation exits 0; other failures exit nonzero. If detection still fails, check wiring/address before assuming it works. Only the selected address is probed; the installer does not scan the entire bus.

## Behavior and tuning

Movement plus left click: press the ball to click, hold it to drag. No right-click or scrolling gestures in this first version. Pointer input is delivered through Linux uinput for Wayland or X11 desktops. Boot startup does not wait for the network or a user login. A missing/disconnected device makes the service retry every five seconds; removing the virtual mouse also releases held buttons. Do not hot-wire the module.

```bash
sudo nano /etc/pocketterm35-trackball.ini
sudo systemctl restart pocketterm35-trackball
```

Set `rotation` to 0/90/180/270 for the mounting orientation. Set `invert_x`/`invert_y` if needed, and `speed` between 0.1 and 20. Fractional movement is retained. Adjust `red`, `green`, `blue`, `white` from 0–255 (all zero turns illumination off). Defaults are bus 1, address 0x0A, speed 2, dim green.

## Check startup and troubleshoot

```bash
systemctl is-enabled pocketterm35-trackball
systemctl status pocketterm35-trackball --no-pager
journalctl -u pocketterm35-trackball -b -n 40 --no-pager
```

Expected log: `Trackball ready on I2C-1 at 0x0a`. Reboot and confirm movement, click, drag, and service status. If a bus error appears, inspect wiring/power and address. An unexpected chip ID stops driver initialization. If the service is ready but there is no desktop cursor movement, inspect desktop input settings. Disable any previous driver for this same trackball before using this one.

The service runs as root to access I2C and uinput, with a read-only filesystem sandbox, no privilege escalation, and protected home directories. It does not collect data or use the network.

## Remove

From the extracted project folder:

```bash
sudo bash trackball/uninstall.sh
```

Removes only this service and driver. Keeps I2C enabled, packages, boot backups, and tuning config because other peripherals may depend on them.

## Private repository

Repository: `H3llawts/-PocketTerm35-Addons` (Private). The leading hyphen is part of the repository name.

On the Pi, you can download `install-trackball.sh` from GitHub while signed in and run the one command above. Alternatively, if you already have GitHub SSH authentication configured:

```bash
git clone git@github.com:H3llawts/-PocketTerm35-Addons.git PocketTerm35-Addons
cd PocketTerm35-Addons
sudo bash install-trackball.sh
```

Private repository downloads require authentication; an unauthenticated public curl command will not work. Never paste access tokens into scripts or commit them to the repo.

## Validation and sources

Local checks cover Python/shell syntax, movement transforms, and mocked hardware register protocol/chip validation. Physical hardware, actual cursor response, apt installation, and reboot behavior have **not** been tested. This is a first hardware-test candidate, not a guarantee of trouble-free operation.

Protocol reference: [Pimoroni trackball driver](https://github.com/pimoroni/trackball-python/blob/master/library/trackball/__init__.py). Uses its documented register layout, chip ID, and separate write/read transactions with 20ms delay. Boot configuration reference: [Waveshare software guide](https://docs.waveshare.com/PocketTerm35/Software-Guide).

After editing the source driver, run `python3 build_installer.py` to regenerate the self-contained installer. Run `python3 -m unittest discover -s tests -v` for local checks.
