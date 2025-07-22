from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from typing import Dict, Optional


class State:
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics, game_queue=None):
        self._moves = moves
        self._graphics = graphics
        self._physics = physics
        self._game_queue = game_queue  # תור פקודות של המשחק
        self.state = "idle"  # המצב הנוכחי: idle, move, jump, rest_short, rest_long
        self.transitions = {
            "idle": {"move": "move", "jump": "jump"},
            "move": {"arrived": "rest_long"},
            "jump": {"arrived": "rest_short"},
            "rest_short": {"rest_done": "idle"},
            "rest_long": {"rest_done": "idle"},
        }
        self.rest_start = None
        self.rest_time = {"rest_short": 2000, "rest_long": 5000}  # 2 שניות קצר, 5 שניות ארוך
        self._last_cmd: Optional[Command] = None

    def reset(self, cmd: Command):
        # print(f"🔧 State.reset: קיבל פקודה {cmd.type} ל-{cmd.target}")
        self._last_cmd = cmd
        self._physics.reset(cmd)
        if cmd.type in ("rest_short", "rest_long"):
            self.rest_start = cmd.timestamp if hasattr(cmd, "timestamp") else 0
        # הוספה: מעבר מצב מיידי אם קיבלנו move/jump
        elif cmd.type in ("move", "jump"):
            # print(f"🔧 State.reset: עובר למצב {cmd.type}")
            self._transition(cmd.type, getattr(cmd, "timestamp", 0))
        
        # Graphics reset עם הפקודה הנכונה
        self._graphics.reset(cmd)

    def update(self, now_ms: int) -> "State":
        self._graphics.update(now_ms)
        # טיפול במצבי מנוחה
        if self.state in ("rest_short", "rest_long"):
            if self.rest_start is not None and now_ms - self.rest_start >= self.rest_time[self.state]:
                elapsed = (now_ms - self.rest_start) / 1000  # שניות
                expected = self.rest_time[self.state] / 1000  # שניות
                print(f"⏰ מנוחה {self.state} הסתיימה אחרי {elapsed:.1f} שניות (ציפייה: {expected:.1f})")
                self._last_cmd = Command(timestamp=now_ms, piece_id=None, type="rest_done", params=None)
                self._transition("rest_done", now_ms)
        else:
            cmd = self._physics.update(now_ms)
            if cmd is not None:
                self._last_cmd = cmd
                # אם זו פקודת arrived, הוסף אותה לתור של המשחק
                if cmd.type == "arrived" and self._game_queue is not None:
                    print(f"🔍 ARRIVED DEBUG: piece_id='{cmd.piece_id}', target={cmd.target}, params={cmd.params}")
                    self._game_queue.put(cmd)
                    print(f"🏁 הוספתי פקודת arrived לתור: {cmd.piece_id}")
                self._transition(cmd.type, now_ms)
        return self

    def _transition(self, event: str, now_ms: int):
        next_state = self.transitions.get(self.state, {}).get(event)
        if next_state:
            old_state = self.state
            self.state = next_state
            print(f"🔄 מעבר מצב: {old_state} -> {self.state} (אירוע: {event})")
            
            # עדכן Graphics עם reset שמכיל את המצב החדש
            state_cmd = Command(timestamp=now_ms, piece_id=None, type="state_change", 
                              params={"target_state": self.state})
            self._graphics.reset(state_cmd)
            
            # אתחול מנוחה אם צריך
            if self.state in ("rest_short", "rest_long"):
                self.rest_start = now_ms
                rest_duration = self.rest_time[self.state] / 1000  # המרה למילישניות
                print(f"💤 התחלת מנוחה {self.state} למשך {rest_duration} שניות")
            elif self.state == "idle":
                self.rest_start = None  # איפוס מנוחה כשחוזרים ל-idle
                print(f"✅ חזרה למצב idle - מוכן לתנועה חדשה")

    def can_transition(self, now_ms: int) -> bool:
        # אפשר להרחיב לפי הצורך
        return True

    def get_command(self) -> Optional[Command]:
        return self._last_cmd

    def process_command(self, cmd: Command) -> "State":
        """Process an incoming command and return the next state."""
        # print(f"🔧 State.process_command: מעבד פקודה {cmd.type} עבור {cmd.piece_id}")
        
        # בדיקה אם הכלי במנוחה - דחה פקודות תנועה חדשות
        if self.state in ("rest_short", "rest_long") and cmd.type in ("move", "jump"):
            if self.rest_start is not None:
                now_ms = cmd.timestamp if hasattr(cmd, 'timestamp') else 0
                elapsed_ms = now_ms - self.rest_start
                required_ms = self.rest_time[self.state]
                
                if elapsed_ms < required_ms:
                    remaining_sec = (required_ms - elapsed_ms) / 1000
                    print(f"🚫 {cmd.piece_id} במנוחה {self.state} - נותרו {remaining_sec:.1f} שניות - דוחה פקודת {cmd.type}")
                    return self  # דחה את הפקודה
        
        # טיפול בפקודות תנועה
        if cmd.type == "move":
            print(f"🎯 State: מבצע תנועה ל-{cmd.target}")
            
            # איפוס הפיזיקה לטפל בתנועה עם אנימציה
            self._physics.reset(cmd)
            
            # מעבר מיידי למצב move
            self.state = "move"
            self._last_cmd = cmd
            
        elif cmd.type == "jump":
            print(f"🎯 State: מבצע קפיצה ל-{cmd.target}")
            if hasattr(self._physics, 'cell') and cmd.target:
                old_pos = self._physics.cell
                self._physics.cell = cmd.target
                print(f"🎯 State: עדכון מיקום מ-{old_pos} ל-{self._physics.cell}")
            
            self.state = "jump"
            self._last_cmd = cmd
            self._transition("arrived", cmd.timestamp if hasattr(cmd, 'timestamp') else 0)
            
        elif cmd.type == "reset":
            # print(f"🔧 State: איפוס למצב idle")
            self.reset(cmd)
        
        else:
            print(f"❓ State: פקודה לא מוכרת: {cmd.type}")
        
        return self
