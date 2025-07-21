from CTD25.It1_interfaces.Command import Command
from CTD25.It1_interfaces.Moves import Moves
from CTD25.It1_interfaces.Graphics import Graphics
from CTD25.It1_interfaces.Physics import Physics
from typing import Dict, Optional


class State:
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics):
        self._moves = moves
        self._graphics = graphics
        self._physics = physics
        self.state = "idle"  # המצב הנוכחי: idle, move, jump, rest_short, rest_long
        self.transitions = {
            "idle": {"move": "move", "jump": "jump"},
            "move": {"arrived": "rest_long"},
            "jump": {"arrived": "rest_short"},
            "rest_short": {"rest_done": "idle"},
            "rest_long": {"rest_done": "idle"},
        }
        self.rest_start = None
        self.rest_time = {"rest_short": 500, "rest_long": 1500}
        self._last_cmd: Optional[Command] = None

    def reset(self, cmd: Command):
        self._last_cmd = cmd
        self._graphics.reset()
        self._physics.reset(cmd)
        if cmd.type in ("rest_short", "rest_long"):
            self.rest_start = cmd.timestamp if hasattr(cmd, "timestamp") else 0
        # הוספה: מעבר מצב מיידי אם קיבלנו move/jump
        elif cmd.type in ("move", "jump"):
            self._transition(cmd.type, getattr(cmd, "timestamp", 0))

    def update(self, now_ms: int) -> "State":
        self._graphics.update(now_ms)
        # טיפול במצבי מנוחה
        if self.state in ("rest_short", "rest_long"):
            if self.rest_start is not None and now_ms - self.rest_start >= self.rest_time[self.state]:
                self._last_cmd = Command(timestamp=now_ms, piece_id=None, type="rest_done", params=None)
                self._transition("rest_done", now_ms)
        else:
            cmd = self._physics.update(now_ms)
            if cmd is not None:
                self._last_cmd = cmd
                self._transition(cmd.type, now_ms)
        return self

    def _transition(self, event: str, now_ms: int):
        next_state = self.transitions.get(self.state, {}).get(event)
        if next_state:
            self.state = next_state
            # אתחול מנוחה אם צריך
            if self.state in ("rest_short", "rest_long"):
                self.rest_start = now_ms
            elif self.state == "idle":
                self.rest_start = None  # איפוס מנוחה כשחוזרים ל-idle

    def can_transition(self, now_ms: int) -> bool:
        # אפשר להרחיב לפי הצורך
        return True

    def get_command(self) -> Optional[Command]:
        return self._last_cmd