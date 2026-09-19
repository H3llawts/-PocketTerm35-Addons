import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('driver', Path(__file__).parents[1] / 'trackball/trackball_mouse.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

class Tests(unittest.TestCase):
    def test_mounting_rotations(self):
        c = dict(rotation=0, speed=1, invert_x=False, invert_y=False)
        for angle, expected in [(0,(3,5)),(90,(-5,3)),(180,(-3,-5)),(270,(5,-3))]:
            c['rotation'] = angle
            self.assertEqual(d.movement(1,4,2,7,c), expected)
        c.update(rotation=0, invert_x=True, speed=0.5)
        self.assertEqual(d.movement(1,4,2,7,c),(-1.5,2.5))

    def test_stop_delay_and_chip_identity(self):
        events=[]
        class Msg:
            @staticmethod
            def write(address, payload):
                return ('write', address, payload)
            @staticmethod
            def read(address, count):
                events.append(('read',address,count))
                return [0x11,0xba]
        class Bus:
            def i2c_rdwr(self, msg):
                events.append(('transfer',msg))
        with patch.dict(sys.modules, smbus2=types.SimpleNamespace(i2c_msg=Msg)), patch.object(d.time,'sleep',lambda t:events.append(('delay',t))):
            d.Trackball(Bus(),0x0a).verify()
        self.assertEqual(events[0],('transfer',('write',0x0a,[0xfa])))
        self.assertEqual(events[1],('delay',0.02))
        self.assertEqual(events[2],('read',0x0a,2))
        with patch.object(d.Trackball,'read',return_value=[0,0]):
            with self.assertRaises(RuntimeError):
                d.Trackball(None,0x0a).verify()

    def test_default_config(self):
        c=d.settings(str(Path(__file__).parents[1]/'trackball/trackball.ini'))
        self.assertEqual(c['address'],10)
        self.assertEqual(c['led'],[0,12,0,0])

    def test_embedded_files_match(self):
        root=Path(__file__).parents[1]
        installer=(root/'install-trackball.sh').read_text()
        for name in ['trackball_mouse.py','trackball.ini','pocketterm35-trackball.service']:
            self.assertIn((root/'trackball'/name).read_text(),installer)

if __name__=='__main__':
    unittest.main()
