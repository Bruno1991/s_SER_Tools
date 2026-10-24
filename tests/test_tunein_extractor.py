"""Testes unitários para o extrator do TuneIn Radio."""

import json
from unittest.mock import MagicMock, patch
import pytest

from adb_tools.tunein_extractor import (
    TuneInRadioExtractor,
    make_request,
    resolve_station_stream,
)


def test_resolve_station_stream_success():
    mock_payload = {
        "head": {"status": "200"},
        "body": [
            {
                "element": "audio",
                "url": "https://stream.example.com/radio.aac",
                "media_type": "aac",
                "bitrate": 128,
                "reliability": 98,
                "is_direct": True,
            }
        ],
    }

    station = {
        "guide_id": "s12345",
        "name": "Radio Teste FM",
        "category": "Brasil > São Paulo",
    }

    with patch("adb_tools.tunein_extractor.make_request", return_value=mock_payload):
        res = resolve_station_stream(station)
        assert res["direct_stream_url"] == "https://stream.example.com/radio.aac"
        assert res["stream_media_type"] == "aac"
        assert res["stream_bitrate"] == 128
        assert len(res["all_streams"]) == 1


def test_resolve_station_stream_no_guide_id():
    station = {"name": "Sem ID"}
    res = resolve_station_stream(station)
    assert res == station


def test_extract_outlines_parsing():
    extractor = TuneInRadioExtractor(max_workers=2)
    mock_body = [
        {
            "element": "outline",
            "type": "audio",
            "text": "Rádio Mix FM",
            "guide_id": "s9999",
            "formats": "mp3",
            "bitrate": "128",
            "image": "http://logo.png",
        },
        {
            "element": "outline",
            "type": "link",
            "text": "Subcategoria Rock",
            "URL": "http://opml.radiotime.com/Browse.ashx?id=c123",
        },
    ]

    queue = []
    extractor._extract_outlines(mock_body, "Música", queue)

    assert "s9999" in extractor.stations
    assert extractor.stations["s9999"]["name"] == "Rádio Mix FM"
    assert len(queue) == 1
    assert queue[0]["url"] == "http://opml.radiotime.com/Browse.ashx?id=c123"


def test_save_to_files(tmp_path):
    extractor = TuneInRadioExtractor()
    stations = [
        {
            "guide_id": "s1",
            "name": "Rádio 1",
            "category": "Pop",
            "direct_stream_url": "http://stream1.mp3",
        },
        {
            "guide_id": "s2",
            "name": "Rádio 2",
            "category": "Rock",
            "direct_stream_url": None,
        },
    ]

    out_file = tmp_path / "radios_test.json"
    dataset = extractor.save_to_files(stations, [str(out_file)])

    assert out_file.exists()
    assert dataset["metadata"]["total_stations"] == 2
    assert dataset["metadata"]["total_active_streams"] == 1
    assert dataset["metadata"]["coverage_percentage"] == "50.00%"

    with open(out_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert loaded["metadata"]["total_stations"] == 2
        assert len(loaded["stations"]) == 2
