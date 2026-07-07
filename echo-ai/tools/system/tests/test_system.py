import unittest
from tools.system.system_service import SystemService
from tools.system.system_utils import bytes_to_gb, format_percent, validate_app

class TestSystemService(unittest.TestCase):
    def setUp(self):
        self.service = SystemService()

    def test_utils(self):
        self.assertEqual(bytes_to_gb(1073741824), 1.0)
        self.assertEqual(bytes_to_gb(1610612736), 1.5)
        self.assertEqual(format_percent(45.234), "45.2%")
        
        # Valid app names
        self.assertTrue(validate_app("notepad.exe"))
        self.assertTrue(validate_app("C:\\Windows\\notepad.exe"))
        # Invalid commands (command injection characters)
        self.assertFalse(validate_app("notepad.exe; rm -rf /"))
        self.assertFalse(validate_app("calc.exe & echo Hacked"))

    def test_service_metrics(self):
        cpu = self.service.cpu_usage()
        self.assertTrue(cpu.cores_logical >= 1)
        self.assertTrue(0.0 <= cpu.percent_usage <= 100.0)

        mem = self.service.memory_usage()
        self.assertTrue(mem.total_gb > 0)
        self.assertTrue(0.0 <= mem.percent_used <= 100.0)

        disk = self.service.disk_usage()
        self.assertTrue(disk.total_gb > 0)

        battery = self.service.battery_status()
        self.assertTrue(0.0 <= battery.percent <= 100.0)

    def test_processes(self):
        procs = self.service.list_processes(limit=5)
        self.assertTrue(len(procs) >= 0)

if __name__ == "__main__":
    unittest.main()
