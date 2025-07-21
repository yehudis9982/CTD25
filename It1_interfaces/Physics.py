from typing import Tuple, Optional
from CTD25.It1_interfaces.Command import Command
from CTD25.It1_interfaces.Board import Board


class Physics:
    """
    בסיס לפיזיקה של כלי: מיקום, מהירות, האם אפשר לתפוס/להיתפס, עדכון מצב.
    """

    def __init__(self, start_cell: Tuple[int, int], board: Board, speed_m_s: float = 1.0):
        self.board = board
        self.cell = start_cell
        self.speed = speed_m_s
        self.pixel_pos = self.board.cell_to_pixel(start_cell)
        self._can_capture = True
        self._can_be_captured = True
        self.target_cell = start_cell
        self.moving = False
        self.start_time = 0
        self.end_time = 0
        self.mode = "idle"  # מצב פיזי נוכחי: idle/move/jump

    def reset(self, cmd: Command):
        """
        אתחול פיזיקה לפי פקודה חדשה (למשל התחלת תנועה, קפיצה, עמידה).
        """
        self.mode = cmd.type
        if cmd.type == "move":
            self.target_cell = cmd.target
            self.moving = True
            self.start_time = getattr(cmd, "time_ms", getattr(cmd, "timestamp", 0))
            dist = self._cell_distance(self.cell, self.target_cell)
            self.end_time = self.start_time + int(dist / self.speed * 1000)
        elif cmd.type == "jump":
            self.target_cell = self.cell  # קפיצה במקום, לא משנה תא
            self.moving = False           # אין תנועה בפועל
        elif cmd.type == "idle":
            self.target_cell = self.cell
            self.moving = False
        else:
            self.moving = False

    def update(self, now_ms: int) -> Optional[Command]:
        """
        עדכון מצב פיזי לפי הזמן הנוכחי. מחזיר פקודה אם הסתיימה תנועה/קפיצה.
        """
        if self.moving:
            if now_ms >= self.end_time:
                self.cell = self.target_cell
                self.pixel_pos = self.board.cell_to_pixel(self.cell)
                self.moving = False
                return Command(timestamp=now_ms, piece_id=self.cell, type="arrived", params=None)
        return None

    def can_be_captured(self) -> bool:
        return self._can_be_captured

    def can_capture(self) -> bool:
        return self._can_capture

    def get_pos(self) -> Tuple[int, int]:
        return self.pixel_pos

    def _cell_distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        dr = b[0] - a[0]
        dc = b[1] - a[1]
        return (dr ** 2 + dc ** 2) ** 0.5


class IdlePhysics(Physics):
    def reset(self, cmd: Command):
        self.moving = False
        self.mode = "idle"

    def update(self, now_ms: int) -> Optional[Command]:
        return None


class MovePhysics(Physics):
    pass  # אפשר להרחיב אם תרצה התנהגות מיוחדת

