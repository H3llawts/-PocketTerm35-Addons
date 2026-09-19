#!/usr/bin/python3
"""Pimoroni trackball -> Linux uinput, independent of the desktop session."""
import configparser
import logging
import math
import signal
import sys
import time

CONFIG = '/etc/pocketterm35-trackball.ini'


def settings(path=CONFIG):
    cfg = configparser.ConfigParser()
    cfg.read(path)
    s = cfg['trackball']
    result = dict(bus=s.getint('bus', 1), address=int(s.get('address', '0x0a'), 0),
                  rotation=s.getint('rotation', 0), speed=s.getfloat('speed', 2.0),
                  invert_x=s.getboolean('invert_x', False),
                  invert_y=s.getboolean('invert_y', False),
                  led=[s.getint(k, 0) for k in ('red', 'green', 'blue', 'white')])
    if result['rotation'] not in (0, 90, 180, 270):
        raise ValueError('rotation must be 0, 90, 180 or 270')
    if not math.isfinite(result['speed']) or not 0.1 <= result['speed'] <= 20:
        raise ValueError('speed must be between 0.1 and 20')
    if not 0x08 <= result['address'] <= 0x77 or result['bus'] < 0:
        raise ValueError('Invalid I2C bus/address')
    if any(not 0 <= v <= 255 for v in result['led']):
        raise ValueError('LED values must be 0..255')
    return result


def movement(left, right, up, down, cfg):
    x, y = right - left, down - up
    rotation = cfg['rotation']
    if rotation == 90:
        x, y = -y, x
    elif rotation == 180:
        x, y = -x, -y
    elif rotation == 270:
        x, y = y, -x
    return (x * cfg['speed'] * (-1 if cfg['invert_x'] else 1),
            y * cfg['speed'] * (-1 if cfg['invert_y'] else 1))


class Trackball:
    def __init__(self, bus, address):
        self.bus, self.address = bus, address

    def read(self, register, count):
        from smbus2 import i2c_msg
        # Match Pimoroni's STOP + 20ms delay; do not use a combined transfer.
        self.bus.i2c_rdwr(i2c_msg.write(self.address, [register]))
        time.sleep(0.02)
        reply = i2c_msg.read(self.address, count)
        self.bus.i2c_rdwr(reply)
        return list(reply)

    def verify(self):
        lo, hi = self.read(0xfa, 2)
        if lo | hi << 8 != 0xba11:
            raise RuntimeError('Unexpected chip ID; refusing to drive this device')

    def leds(self, values):
        from smbus2 import i2c_msg
        self.bus.i2c_rdwr(i2c_msg.write(self.address, [0, *values]))


def main():
    from smbus2 import SMBus
    from evdev import UInput, ecodes as e
    cfg = settings()
    with SMBus(cfg['bus']) as bus:
        ball = Trackball(bus, cfg['address'])
        ball.verify()
        if '--probe' in sys.argv:
            print('Pimoroni trackball detected (chip 0xBA11).')
            return
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        with UInput({e.EV_REL: [e.REL_X, e.REL_Y], e.EV_KEY: [e.BTN_LEFT]},
                    name='PocketTerm35 Pimoroni Trackball', bustype=e.BUS_I2C) as mouse:
            try:
                ball.leds(cfg['led'])
                logging.info('Trackball ready on I2C-%s at 0x%02x', cfg['bus'], cfg['address'])
                pressed = False
                carry_x = carry_y = 0.0
                while True:
                    left, right, up, down, switch = ball.read(0x04, 5)
                    x, y = movement(left, right, up, down, cfg)
                    carry_x += x
                    carry_y += y
                    dx, dy = int(carry_x), int(carry_y)
                    carry_x -= dx
                    carry_y -= dy
                    if dx:
                        mouse.write(e.EV_REL, e.REL_X, dx)
                    if dy:
                        mouse.write(e.EV_REL, e.REL_Y, dy)
                    now = bool(switch & 0x80)
                    if now != pressed:
                        mouse.write(e.EV_KEY, e.BTN_LEFT, int(now))
                    pressed = now
                    mouse.syn()
                    time.sleep(0.005)
            finally:
                mouse.write(e.EV_KEY, e.BTN_LEFT, 0)
                mouse.syn()
                try:
                    ball.leds([0, 0, 0, 0])
                except OSError:
                    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        logging.error('%s', exc)
        sys.exit(1)
