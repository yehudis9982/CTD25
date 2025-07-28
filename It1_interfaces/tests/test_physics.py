import pytest

class DummyBoard:
    def cell_to_pixel(self, cell):
        return (cell[0]*100, cell[1]*100)

class DummyCommand:
    def __init__(self, type, target, timestamp, params=None):
        self.type = type
        self.target = target
        self.timestamp = timestamp
        self.params = params or {}

from CTD25.It1_interfaces.Physics import Physics

def test_physics_move():
    board = DummyBoard()
    p = Physics((0, 0), board, speed_m_s=1.0)
    cmd = DummyCommand("move", (3, 4), 1000)
    p.reset(cmd)
    assert p.moving
    assert p.target_cell == (3, 4)
    # לפני הזמן - לא מגיע
    assert p.update(2000) is None
    # אחרי הזמן - מגיע
    arrived = p.update(6000)
    assert arrived is not None
    assert arrived.type == "arrived"
    assert p.cell == (3, 4)
    assert not p.moving

def test_physics_idle():
    board = DummyBoard()
    p = Physics((1, 1), board)
    cmd = DummyCommand("idle", (1, 1), 1000)
    p.reset(cmd)
    assert not p.moving
    assert p.update(2000) is None

def test_physics_arrival_command():
    board = DummyBoard()
    p = Physics((0, 0), board, speed_m_s=1.0)
    cmd = DummyCommand("move", (3, 4), 1000)
    p.reset(cmd)
    assert p.moving
    assert p.target_cell == (3, 4)
    # simulate passage of time until arrival
    arrived = p.update(6000)
    assert arrived is not None
    assert arrived.type == "arrived"
    assert p.cell == (3, 4)
    assert not p.moving
    # check if arrival command is as expected
    arrival_cmd = p.update(6000)
    assert arrival_cmd is None  # כי כבר לא בתנועה