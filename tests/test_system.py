"""Unit tests for system metrics collection (CPU, Memory, Disk)."""

import os
import unittest
from unittest.mock import MagicMock, patch

from sysmon_cli.system import (
    get_cpu_metrics,
    get_disk_metrics,
    get_memory_metrics,
    get_swap_metrics,
    get_system_health,
)


class TestSystemMetrics(unittest.TestCase):
    """Test system health metrics collection."""

    def test_cpu_metrics(self):
        cpu = get_cpu_metrics(interval=0.0)
        self.assertIsInstance(cpu["usage_percent"], float)
        self.assertGreaterEqual(cpu["usage_percent"], 0.0)
        self.assertLessEqual(cpu["usage_percent"], 100.0)

        self.assertIsInstance(cpu["count_logical"], int)
        self.assertGreaterEqual(cpu["count_logical"], 1)

        self.assertIsInstance(cpu["count_physical"], int)
        self.assertGreaterEqual(cpu["count_physical"], 1)

        self.assertIsInstance(cpu["per_cpu_percent"], list)
        self.assertEqual(len(cpu["per_cpu_percent"]), cpu["count_logical"])
        for val in cpu["per_cpu_percent"]:
            self.assertIsInstance(val, float)

    def test_cpu_metrics_invalid_and_negative_intervals(self):
        # Negative, string, and NaN intervals clamp safely to 0.0
        cpu_neg = get_cpu_metrics(interval=-1.0)
        self.assertIsInstance(cpu_neg["usage_percent"], float)

        cpu_str = get_cpu_metrics(interval="invalid")
        self.assertIsInstance(cpu_str["usage_percent"], float)

        cpu_nan = get_cpu_metrics(interval=float("nan"))
        self.assertIsInstance(cpu_nan["usage_percent"], float)

    def test_memory_metrics(self):
        mem = get_memory_metrics()
        self.assertIsInstance(mem["total_bytes"], int)
        self.assertGreater(mem["total_bytes"], 0)

        self.assertIsInstance(mem["used_bytes"], int)
        self.assertGreaterEqual(mem["used_bytes"], 0)

        self.assertIsInstance(mem["available_bytes"], int)
        self.assertGreaterEqual(mem["available_bytes"], 0)

        self.assertIsInstance(mem["percent"], float)
        self.assertGreaterEqual(mem["percent"], 0.0)
        self.assertLessEqual(mem["percent"], 100.0)

        # Human-readable strings
        self.assertIn("B", mem["total_human"])
        self.assertIn("B", mem["used_human"])
        self.assertIn("B", mem["available_human"])

    def test_swap_metrics(self):
        swap = get_swap_metrics()
        self.assertIsInstance(swap["total_bytes"], int)
        self.assertGreaterEqual(swap["total_bytes"], 0)
        self.assertIsInstance(swap["percent"], float)

    def test_disk_metrics(self):
        disks = get_disk_metrics()
        self.assertIsInstance(disks, list)
        self.assertGreater(len(disks), 0)

        for d in disks:
            self.assertIn("device", d)
            self.assertIn("mountpoint", d)
            self.assertIsInstance(d["total_bytes"], int)
            self.assertGreater(d["total_bytes"], 0)
            self.assertIsInstance(d["percent"], float)
            self.assertGreaterEqual(d["percent"], 0.0)
            self.assertLessEqual(d["percent"], 100.0)
            self.assertTrue(d["accessible"])

    def test_disk_metrics_specific_path(self):
        cwd = os.getcwd()
        disks = get_disk_metrics(target_path=cwd)
        self.assertEqual(len(disks), 1)
        self.assertEqual(disks[0]["mountpoint"], cwd)
        self.assertGreater(disks[0]["total_bytes"], 0)
        self.assertTrue(disks[0]["accessible"])

    def test_disk_metrics_nonexistent_path(self):
        res = get_disk_metrics(target_path="Z:\\NonExistent_Fake_Drive\\12345")
        self.assertEqual(len(res), 1)
        self.assertFalse(res[0]["accessible"])
        self.assertEqual(res[0]["total_bytes"], 0)

    @patch("psutil.disk_usage")
    def test_disk_metrics_inaccessible_partition(self, mock_usage):
        mock_usage.side_effect = PermissionError("Access denied")
        # Specific path that fails
        res = get_disk_metrics(target_path="Z:\\Locked")
        self.assertEqual(len(res), 1)
        self.assertFalse(res[0]["accessible"])
        self.assertEqual(res[0]["total_bytes"], 0)

    def test_system_health_compilation(self):
        health = get_system_health(cpu_interval=0.0)
        self.assertIn("timestamp", health)
        self.assertIn("platform", health)
        self.assertIn("cpu", health)
        self.assertIn("memory", health)
        self.assertIn("swap", health)
        self.assertIn("disk", health)

        plat = health["platform"]
        self.assertIn("system", plat)
        self.assertIn("hostname", plat)


if __name__ == "__main__":
    unittest.main()
