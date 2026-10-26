"""Testes para o módulo desktop_bin: StringsExtractor, Checksec e PEAnalyzer."""

import pytest
from pathlib import Path
from ser_tools.desktop_bin.strings_extractor import StringsExtractor
from ser_tools.desktop_bin.checksec import ChecksecScanner
from ser_tools.desktop_bin.pe_analyzer import PEAnalyzer


def test_strings_extractor_ascii_and_patterns():
    sample_data = (
        b"Welcome to the secret binary!\x00"
        b"https://api.example.com/v1/auth\x00"
        b"Contact admin at security@example.org\x00"
        b"Server IP is 192.168.1.100\x00"
        b"C:\\Windows\\System32\\kernel32.dll\x00"
    )

    res = StringsExtractor.extract_from_bytes(sample_data, min_len=4)
    assert res.total_strings > 0
    assert any("secret binary" in s for s in res.ascii_strings)
    assert "https://api.example.com/v1/auth" in res.urls
    assert "security@example.org" in res.emails
    assert "192.168.1.100" in res.ip_addresses


def test_strings_extractor_unicode():
    text = "UnicodeStringTest"
    sample_data = text.encode("utf-16le")

    res = StringsExtractor.extract_from_bytes(sample_data, min_len=4)
    assert any("UnicodeStringTest" in s for s in res.unicode_strings)


def test_pe_analyzer_entropy_calculation():
    zero_bytes = b"\x00" * 100
    assert PEAnalyzer.calculate_entropy(zero_bytes) == 0.0

    # Dados aleatórios devem ter alta entropia (> 7.0)
    import os
    random_bytes = os.urandom(1000)
    assert PEAnalyzer.calculate_entropy(random_bytes) > 7.0


def test_checksec_non_binary(tmp_path):
    text_file = tmp_path / "plain.txt"
    text_file.write_text("Hello world")

    res = ChecksecScanner.scan(text_file)
    assert res.binary_format == "Unknown"
    assert res.overall_score == 0
