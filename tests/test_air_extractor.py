"""Testes unitários para o módulo de extração e análise de apps Adobe AIR / SWF."""

import tempfile
import unittest
from pathlib import Path

from adb_tools.air_extractor import AirExtractor, parse_swf_header


class TestAirExtractor(unittest.TestCase):
    def setUp(self):
        self.slither_apk = Path(r"C:\dev\s_ADB_Tools\extracted_apks\air.com.hypah.io.slither.apk")
        self.expense_apk = Path(r"C:\dev\s_ADB_Tools\extracted_apks\com.smartexpenditure\com.smartexpenditure.apk")

    def test_is_air_apk_detection(self):
        self.assertTrue(
            AirExtractor.is_air_apk(self.slither_apk),
            "air.com.hypah.io.slither.apk deve ser detectado como app Adobe AIR.",
        )
        if self.expense_apk.exists():
            self.assertFalse(
                AirExtractor.is_air_apk(self.expense_apk),
                "com.smartexpenditure não deve ser detectado como app Adobe AIR.",
            )

    def test_inspect_apk_metadata(self):
        info = AirExtractor.inspect_apk(self.slither_apk)
        self.assertTrue(info.is_air)
        self.assertEqual(info.app_id, "com.hypah.io.slither")
        self.assertEqual(info.app_name, "slither.io")
        self.assertEqual(info.version, "3.06")
        self.assertEqual(info.air_sdk_version, "51.2")
        self.assertEqual(info.main_swf_name, "slither android.swf")
        self.assertEqual(info.render_mode, "direct")
        self.assertTrue(info.fullscreen)
        self.assertGreaterEqual(len(info.extensions), 5)
        self.assertIn("androidx.core", info.extensions)
        self.assertGreaterEqual(len(info.all_swfs), 50)

    def test_parse_swf_header(self):
        # Test CWS header (ZLIB compressed SWF, version 51, length 30145878)
        sample_header = b"CWS\x33\x56\x78\xcb\x01"
        header = parse_swf_header(sample_header)
        self.assertIsNotNone(header)
        self.assertEqual(header.signature, "CWS")
        self.assertEqual(header.version, 51)
        self.assertTrue(header.is_valid)

        # Invalid header
        invalid = parse_swf_header(b"XYZ12345")
        self.assertIsNone(invalid)

    def test_extract_air_assets_in_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "test_air_extracted"
            res = AirExtractor.extract_air_assets(self.slither_apk, output_dir=out_path)

            self.assertTrue(res.success)
            self.assertIsNotNone(res.main_swf_file)
            self.assertTrue(res.main_swf_file.is_file())
            self.assertEqual(res.main_swf_file.name, "slither android.swf")
            self.assertGreater(res.main_swf_file.stat().st_size, 10 * 1024 * 1024)

            # Relatório
            self.assertIsNotNone(res.report_file)
            self.assertTrue(res.report_file.is_file())
            report_content = res.report_file.read_text(encoding="utf-8")
            self.assertIn("Adobe AIR (Flash / ActionScript 3)", report_content)
            self.assertIn("JPEXS Free Flash Decompiler", report_content)
            self.assertIn("slither android.swf", report_content)

            # SWFs adicionais e assets
            self.assertGreater(len(res.all_swf_files), 10)
            self.assertGreater(res.total_files_extracted, 50)


if __name__ == "__main__":
    unittest.main()
