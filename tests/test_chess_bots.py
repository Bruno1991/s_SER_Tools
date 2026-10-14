"""Testes unitários para o gerenciador e emulador de bots do Chess.com."""

import pytest
from pathlib import Path
from adb_tools.chess_bots import ChessBotsManager

try:
    import chess
    import chess.polyglot
    HAS_CHESS = True
except ImportError:
    HAS_CHESS = False


@pytest.fixture
def manager():
    return ChessBotsManager()


def test_manager_load_data(manager):
    data = manager.load_data()
    assert "botGroups" in data
    assert len(data["botGroups"]) > 0


def test_manager_get_all_bots(manager):
    bots = manager.get_all_bots()
    assert len(bots) >= 200
    # Verifica que Martin existe
    martin = next((b for b in bots if b.get("name") == "Martin"), None)
    assert martin is not None
    assert martin.get("username") == "Martin-BOT"
    assert martin.get("rating") == 250
    assert martin.get("book") == "beginner"


def test_manager_search_bots(manager):
    results = manager.search_bots("Hikaru")
    assert len(results) >= 1
    assert results[0].get("name") == "Hikaru"


def test_manager_find_bot(manager):
    bot = manager.find_bot("Nelson")
    assert bot is not None
    assert bot.get("name") == "Nelson"
    assert bot.get("rating") == 1300


def test_polyglot_books_available(manager):
    books = manager.list_available_books()
    assert len(books) > 0
    book_names = [b.name for b in books]
    assert "beginner.bin" in book_names
    assert "nakamura.bin" in book_names


@pytest.mark.skipif(not HAS_CHESS, reason="python-chess não instalado")
def test_polyglot_book_read(manager):
    book_path = manager.get_book_path("beginner")
    assert book_path is not None
    assert book_path.is_file()

    board = chess.Board()
    with chess.polyglot.open_reader(str(book_path)) as reader:
        moves = list(reader.find_all(board))
        assert len(moves) > 0
        ucios = [m.move.uci() for m in moves]
        assert "e2e4" in ucios
