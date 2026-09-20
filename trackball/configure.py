#!/usr/bin/env python3
"""Prepare and validate configuration without modifying the installed file."""
import argparse
import configparser
from pathlib import Path
from trackball_mouse import settings


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--existing', required=True)
    p.add_argument('--defaults', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--rotation', type=int, choices=(0, 90, 180, 270))
    p.add_argument('--speed', type=float)
    for color in ('red', 'green', 'blue', 'white'):
        p.add_argument('--' + color, type=int)
    a = p.parse_args()
    cfg = configparser.ConfigParser()
    cfg.read(a.defaults)
    cfg.read(a.existing)
    for key in ('rotation', 'speed', 'red', 'green', 'blue', 'white'):
        value = getattr(a, key)
        if value is not None:
            cfg['trackball'][key] = str(value)
    with open(a.output, 'w') as f:
        cfg.write(f)
    try:
        result = settings(a.output)
    except Exception:
        Path(a.output).unlink(missing_ok=True)
        raise
    print('Configuration:', result)


if __name__ == '__main__':
    main()
