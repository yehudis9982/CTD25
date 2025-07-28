import pytest
import queue
import numpy as np

from CTD25.It1_interfaces.Game import Game

class DummyBoard:
    def __init__(self):
        self.drawn = False
        # תמונה שחורה בגודל 10x10 עם 3 ערוצים
        self.img = np.zeros((10, 10, 3), dtype=np.uint8)
    def draw(self):
        self.drawn = True
    def cell_to_pixel(self, cell): return (0, 0)

class DummyPiece:
    def __init__(self, piece_id):
        self.piece_id = piece_id
        self.reset_called = False
        self.updated = False
        self.drawn = False
        self.last_cmd = None
    def reset(self, start_ms):
        self.reset_called = True
    def update(self, now):
        self.updated = True
    def draw_on_board(self, board, now):
        self.drawn = True
    def on_command(self, cmd, now):
        self.last_cmd = cmd

class DummyCommand:
    def __init__(self, piece_id):
        self.piece_id = piece_id

@pytest.fixture
def game():
    board = DummyBoard()
    pieces = [DummyPiece("A"), DummyPiece("B")]
    return Game(pieces, board)

def test_game_reset_and_update(game):
    # בדוק ש-reset וה-update עובדים על כל הכלים
    game.pieces["A"].reset_called = False
    game.pieces["B"].reset_called = False
    for p in game.pieces.values():
        p.reset(123)
        p.update(456)
    assert game.pieces["A"].reset_called
    assert game.pieces["B"].reset_called
    assert game.pieces["A"].updated
    assert game.pieces["B"].updated

def test_game_draw(game, monkeypatch):
    monkeypatch.setattr("cv2.imshow", lambda *a, **kw: None)
    game._draw()
    assert game.board.drawn
    assert game.pieces["A"].drawn
    assert game.pieces["B"].drawn

def test_game_process_input(game):
    cmd = DummyCommand("A")
    game._process_input(cmd)
    assert game.pieces["A"].last_cmd == cmd

def test_game_run_one_loop(game, monkeypatch):
    monkeypatch.setattr(game, "_is_win", lambda: True)
    monkeypatch.setattr("cv2.imshow", lambda *a, **kw: None)
    monkeypatch.setattr("cv2.destroyAllWindows", lambda *a, **kw: None)
    game.run()
    assert game.pieces["A"].reset_called
    assert game.pieces["B"].reset_called