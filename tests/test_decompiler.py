"""Testes unitarios para o modulo de descompilacao de s_ADB_Tools."""

import unittest
from pathlib import Path

from adb_tools.decompiler import ApkDecompiler, JadxManager, JavaEnvironment


class TestDecompiler(unittest.TestCase):
    def test_java_environment_resolution(self):
        java_home = JavaEnvironment.resolve_java_home()
        self.assertIsNotNone(java_home, "Java Runtime (JDK 17) deve ser resolvido.")
        java_exe = java_home / "bin" / "java.exe"
        self.assertTrue(java_exe.is_file(), "java.exe deve existir.")

    def test_jadx_installation_and_binaries(self):
        jadx_mgr = JadxManager()
        self.assertTrue(jadx_mgr.is_installed(), "JADX deve estar instalado em tools/jadx.")
        cli = jadx_mgr.get_jadx_cli()
        gui = jadx_mgr.get_jadx_gui()
        self.assertIsNotNone(cli)
        self.assertIsNotNone(gui)
        self.assertTrue(cli.is_file())
        self.assertTrue(gui.is_file())

    def test_locate_apk(self):
        apk = ApkDecompiler.locate_apk("com.smartexpenditure")
        self.assertIsNotNone(apk, "Deve localizar o APK de com.smartexpenditure.")
        self.assertTrue(apk.is_file())
        self.assertEqual(apk.suffix.lower(), ".apk")

    def test_decompiled_sources_structure(self):
        decomp_dir = Path(r"C:\dev\s_ADB_Tools\decompiled_sources\com.smartexpenditure")
        self.assertTrue(decomp_dir.exists(), "Pasta de codigo descompilado deve existir.")

        # Verificar AndroidManifest.xml
        manifest = decomp_dir / "app" / "src" / "main" / "AndroidManifest.xml"
        self.assertTrue(manifest.is_file(), "AndroidManifest.xml deve existir e ser legivel.")

        # Verificar assets do app web
        main_js = decomp_dir / "app" / "src" / "main" / "assets" / "www" / "js" / "main.js"
        self.assertTrue(main_js.is_file(), "Codigo fonte JavaScript principal (main.js) deve existir.")


if __name__ == "__main__":
    unittest.main()
