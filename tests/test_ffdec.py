"""Testes unitários para o módulo FfdecManager e descompilação de SWF."""

import unittest
from pathlib import Path

from adb_tools.ffdec_manager import FfdecManager


class TestFfdecManager(unittest.TestCase):
    def setUp(self):
        self.ffdec = FfdecManager()
        self.slither_swf = Path(
            r"C:\dev\s_ADB_Tools\decompiled_sources\air.com.hypah.io.slither\air_extracted\slither android.swf"
        )

    def test_ffdec_installed(self):
        self.assertTrue(self.ffdec.is_installed(), "FFDec deve estar instalado e reconhecido.")
        jar = self.ffdec.get_ffdec_jar()
        self.assertIsNotNone(jar)
        self.assertTrue(jar.is_file())
        self.assertEqual(jar.name, "ffdec.jar")

    def test_locate_swf(self):
        # 1. Por caminho direto
        found = self.ffdec.locate_swf(str(self.slither_swf))
        self.assertIsNotNone(found)
        self.assertEqual(found.resolve(), self.slither_swf.resolve())

        # 2. Por nome do pacote
        found_pkg = self.ffdec.locate_swf("air.com.hypah.io.slither")
        self.assertIsNotNone(found_pkg)
        self.assertTrue(found_pkg.is_file())
        self.assertEqual(found_pkg.suffix.lower(), ".swf")

        # 3. Por termo parcial "slither"
        found_term = self.ffdec.locate_swf("slither")
        self.assertIsNotNone(found_term)


if __name__ == "__main__":
    unittest.main()
