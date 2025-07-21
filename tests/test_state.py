import time

class DummyGraphics:
    def reset(self): pass
    def update(self, now_ms): pass

class DummyPhysics:
    def __init__(self):
        self._cmd = None
        self._sent = False
    def reset(self, cmd):
        self._cmd = cmd
        self._sent = False
    def update(self, now_ms):
        if not self._sent and self._cmd and self._cmd.type in ("move", "jump"):
            self._sent = True
            return DummyCommand(timestamp=now_ms, piece_id=None, type="arrived", params=None)
        return None

class DummyCommand:
    def __init__(self, timestamp, piece_id, type, params=None):
        self.timestamp = timestamp
        self.piece_id = piece_id
        self.type = type
        self.params = params or {}

from CTD25.It1_interfaces.State import State

def test_state_machine_flow():
    moves = None
    graphics = DummyGraphics()
    physics = DummyPhysics()
    state = State(moves, graphics, physics)

    # מתחילים ב-idle, שולחים פקודת move
    cmd = DummyCommand(timestamp=1000, piece_id=None, type="move")
    state.reset(cmd)
    assert state.state == "move"

    # update ראשון: physics מחזיר arrived, מעבר ל-rest_long
    state.update(1100)
    assert state.state == "rest_long"

    # מחכים מספיק זמן כדי שהמנוחה תסתיים (1500ms)
    state.update(1100 + 1500)
    assert state.state == "idle"  # אם יש לולאה, אחרת אולי idle

def test_jump_short_rest():

    moves = None
    graphics = DummyGraphics()
    physics = DummyPhysics()
    state = State(moves, graphics, physics)

    # מתחילים ב-idle, שולחים פקודת jump
    cmd = DummyCommand(2000, None, "jump")
    state.reset(cmd)
    assert state.state == "jump"

    # update ראשון: physics מחזיר arrived, מעבר ל-rest_short
    state.update(2100)
    assert state.state == "rest_short"

    # מחכים מספיק זמן כדי שהמנוחה תסתיים (500ms)
    state.update(2100 + 500)
    assert state.state == "idle"  # אם יש לולאה, אחרת אולי idled