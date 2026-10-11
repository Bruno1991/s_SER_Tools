"""Testes unitarios para s_ADB_Tools."""

import unittest
from pathlib import Path
import zipfile
import io

from adb_tools.cli import format_bytes
from adb_tools.adb_client import AdbClient, AndroidDevice


class TestAdbTools(unittest.TestCase):
    def test_format_bytes(self):
        self.assertEqual(format_bytes(500), "500.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(5 * 1024 * 1024), "5.00 MB")

    def test_resolve_adb_path_finds_platform_tools(self):
        resolved = AdbClient._resolve_adb_path()
        self.assertTrue(resolved.endswith("adb.exe") or resolved == "adb")
        self.assertTrue(Path(resolved).exists() or resolved == "adb")

    def test_extracted_apk_validity_if_present(self):
        apk_path = Path(r"C:\dev\s_ADB_Tools\extracted_apks\com.smartexpenditure.apk")
        if apk_path.exists():
            self.assertTrue(apk_path.stat().st_size > 1_000_000)
            with zipfile.ZipFile(apk_path, "r") as zf:
                self.assertIsNone(zf.testzip())
                names = zf.namelist()
                self.assertIn("classes.dex", names)
                self.assertIn("AndroidManifest.xml", names)


if __name__ == "__main__":
    unittest.main()
