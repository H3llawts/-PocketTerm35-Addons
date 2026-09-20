import configparser
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ConfigurationTests(unittest.TestCase):
    def test_override_preservation_and_invalid_values(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            existing = temp / 'old.ini'
            existing.write_text('[trackball]\nbus=3\naddress=0x0b\ninvert_x=true\nrotation=180\n')
            output = temp / 'new.ini'
            base = [sys.executable, str(ROOT/'trackball/configure.py'), '--existing', str(existing), '--defaults', str(ROOT/'trackball/trackball.ini'), '--output', str(output)]
            result = subprocess.run(base + ['--rotation','90','--speed','1','--green','128'], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            cfg = configparser.ConfigParser(); cfg.read(output)
            self.assertEqual(cfg['trackball']['bus'], '3')
            self.assertEqual(cfg['trackball']['invert_x'], 'true')
            self.assertEqual(cfg['trackball']['green'], '128')
            self.assertEqual(cfg['trackball']['rotation'], '90')
            for flag, value in [('--speed','nan'),('--speed','0'),('--green','256'),('--rotation','45')]:
                result = subprocess.run(base + [flag,value], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
            self.assertIn('rotation=180', existing.read_text())

if __name__ == '__main__':
    unittest.main()
