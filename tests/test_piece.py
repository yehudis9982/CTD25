import pytest

from CTD25.It1_interfaces.Piece import Piece
from CTD25.It1_interfaces.State import State

# דמוי אובייקטים פשוטים
class DummyGraphics:
    def __init__(self):
        self.updated = False
    def reset(self, cmd=None): self.updated = False
    def update(self, now_ms): self.updated = True
    def get_img(self): return self
    def draw_on(self, board, x, y): board["drawn"] = (x, y)

class DummyPhysics:
    def __init__(self):
        self.cell = (1, 2)
        self.updated = False
    def reset(self, cmd): self.updated = False
    def update(self, now_ms): self.updated = True

class DummyBoard(dict):
    def cell_to_pixel(self, cell): return (cell[0]*10, cell[1]*10)

@pytest.fixture
def piece():
    graphics = DummyGraphics()
    physics = DummyPhysics()
    state = State(moves=None, graphics=graphics, physics=physics)
    return Piece(piece_id="A", init_state=state)

def test_reset(piece):
    piece.reset(1234)
    assert hasattr(piece._state, "_graphics")
    assert hasattr(piece._state, "_physics")

def test_update(piece):
    piece.update(1000)
    assert piece._state._graphics.updated
    assert piece._state._physics.updated

def test_on_command(piece):
    class DummyCmd:
        def __init__(self): self.type = "move"
    piece.on_command(DummyCmd(), 2000)
    # לא נבדק שינוי מצב כי process_command לא ממומש בדמי

def test_draw_on_board(piece):
    board = DummyBoard()
    piece.draw_on_board(board, 0)
    # נבדוק שהציור בוצע
    assert "drawn" in board
    assert board["drawn"] == (10, 20)