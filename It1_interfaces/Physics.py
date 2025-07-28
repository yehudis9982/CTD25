from typing import Tuple, Optional
import logging
from Command import Command
from Board import Board

logger = logging.getLogger(__name__)


class Physics:
    """
    בסיס לפיזיקה של כלי: מיקום, מהירות, האם אפשר לתפוס/להיתפס, עדכון מצב.
    """

    def __init__(self, start_cell: Tuple[int, int], board: Board, speed_m_s: float = 1.0, piece_id: str = None):
        self.board = board
        self.cell = start_cell
        self.start_cell = start_cell  # המיקום ההתחלתי לאינטרפולציה
        self.speed = speed_m_s
        self.pixel_pos = self.board.cell_to_pixel(start_cell)
        self._can_capture = True
        self._can_be_captured = True
        self.target_cell = start_cell
        self.moving = False
        self.start_time = 0
        self.end_time = 0
        self.mode = "idle"  # מצב פיזי נוכחי: idle/move/jump
        self.piece_id = piece_id  # שמירת ה-ID של הכלי
        
        # תמיכה במצב המתנה
        self.wait_only = False
        self.start_ms = 0
        self.duration_ms = 0

    def reset(self, cmd: Command):
        """
        אתחול פיזיקה לפי פקודה חדשה (למשל התחלת תנועה, קפיצה, עמידה).
        """
        # print(f"🔧 Physics.reset: קיבל פקודה {cmd.type} מ-{self.cell} ל-{getattr(cmd, 'target', 'N/A')}")
        self.mode = cmd.type
        if cmd.type == "move":
            self.start_cell = self.cell  # שמירת המיקום ההתחלתי לאינטרפולציה
            self.target_cell = cmd.target
            self.moving = True
            self.start_time = getattr(cmd, "time_ms", getattr(cmd, "timestamp", 0))
            
            # מהירות תנועה - נוודא שתמיד יש מהירות חיובית
            move_speed = 2.0  # תאים לשנייה - מהירות תנועה מהירה יותר
            dist = self._cell_distance(self.cell, self.target_cell)
            # print(f"🔧 Physics: מרחק מ-{self.cell} ל-{self.target_cell} = {dist}, מהירות = {move_speed}")
            if dist == 0:
                self.end_time = self.start_time + 100  # 100ms מינימום
            else:
                self.end_time = self.start_time + int(dist / move_speed * 1000)
        elif cmd.type == "jump":
            self.target_cell = cmd.target if hasattr(cmd, 'target') and cmd.target else self.cell
            self.cell = self.target_cell  # קפיצה מיידית למיקום החדש
            self.pixel_pos = self.board.cell_to_pixel(self.cell)  # עדכון pixel_pos
            self.moving = False           # אין תנועה בפועל
            # שמירת זמן לפקודת arrived
            self.start_time = getattr(cmd, "time_ms", getattr(cmd, "timestamp", 0))
            # חישוב זמן קפיצה על פי המהירות בקונפיגורציה
            jump_duration_ms = int(1000 / self.speed)  # ככל שהמהירות נמוכה יותר, הקפיצה ארוכה יותר
            self.end_time = self.start_time + jump_duration_ms
            self.mode = "jump"  # ודא שהמצב הוא קפיצה
        elif cmd.type == "idle":
            self.target_cell = self.cell
            self.pixel_pos = self.board.cell_to_pixel(self.cell)  # וודא שpixel_pos מעודכן
            self.moving = False
        else:
            self.moving = False
            self.pixel_pos = self.board.cell_to_pixel(self.cell)  # וודא עדכון במצבים אחרים

    def update(self, now_ms: int) -> Optional[Command]:
        """
        עדכון מצב פיזי לפי הזמן הנוכחי. מחזיר פקודה אם הסתיימה תנועה/קפיצה.
        """
        # בדיקת מצב המתנה (wait_only)
        if self.wait_only and self.start_ms > 0 and self.duration_ms > 0:
            if now_ms >= self.start_ms + self.duration_ms:
                # המתנה הסתיימה
                self.wait_only = False
                logger.info(f"פיזיקה: המתנה הסתיימה עבור {self.piece_id}")
                return Command(timestamp=now_ms, piece_id=self.piece_id, type="arrived", target=self.cell, params=None)
            return None  # עדיין במצב המתנה
            
        if self.moving:
            if now_ms >= self.end_time:
                # תנועה הסתיימה - הגיעה למיקום הסופי
                self.cell = self.target_cell
                self.pixel_pos = self.board.cell_to_pixel(self.cell)
                self.moving = False
                logger.info(f"פיזיקה: החתיכה ב-{self.cell} הגיעה ליעד")
                return Command(timestamp=now_ms, piece_id=self.piece_id, type="arrived", target=self.cell, params=None)
            else:
                # תנועה בתהליך - אינטרפולציה חלקה
                total_duration = self.end_time - self.start_time
                elapsed = now_ms - self.start_time
                progress = elapsed / total_duration  # אחוז התקדמות (0.0 - 1.0)
                
                # חישוב מיקום ביניים
                start_pixel = self.board.cell_to_pixel(self.start_cell)
                target_pixel = self.board.cell_to_pixel(self.target_cell)
                
                # אינטרפולציה לינארית
                x = start_pixel[0] + (target_pixel[0] - start_pixel[0]) * progress
                y = start_pixel[1] + (target_pixel[1] - start_pixel[1]) * progress
                
                self.pixel_pos = (int(x), int(y))
        elif self.mode == "jump" and now_ms >= self.end_time:
            # קפיצה הסתיימה - צריך ליצור פקודת arrived
            logger.info(f"פיזיקה: החתיכה קפצה ל-{self.cell}")
            self.mode = "idle"  # סיום הקפיצה
            return Command(timestamp=now_ms, piece_id=self.piece_id, type="arrived", target=self.cell, params=None)
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

