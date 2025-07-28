from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING
from Command import Command

if TYPE_CHECKING:
    from typing import Any as StateContext
else:
    StateContext = "StateContext"

class BaseState(ABC):
    """מחלקת בסיס לכל המצבים"""
    
    def __init__(self, context: "StateContext"):
        self.context = context
        self.entry_time: Optional[int] = None
    
    @abstractmethod
    def enter(self, timestamp: int) -> None:
        """נקרא כאשר נכנסים למצב"""
        self.entry_time = timestamp
    
    @abstractmethod
    def exit(self) -> None:
        """נקרא כאשר יוצאים מהמצב"""
        pass
    
    @abstractmethod
    def update(self, now_ms: int) -> Optional["BaseState"]:
        """עדכן את המצב ובדוק אם צריך לעבור למצב אחר"""
        pass
    
    @abstractmethod
    def handle_command(self, cmd: Command) -> Optional["BaseState"]:
        """טפל בפקודה ובדוק אם צריך לעבור למצב אחר"""
        pass
    
    @abstractmethod
    def get_state_name(self) -> str:
        """החזר את שם המצב"""
        pass
    
    def can_accept_command(self, cmd: Command) -> bool:
        """בדוק אם המצב יכול לקבל את הפקודה הזו"""
        return True

class IdleState(BaseState):
    """מצב של חוסר פעילות - מוכן לקבל פקודות"""
    
    def enter(self, timestamp: int) -> None:
        super().enter(timestamp)
        print(f"✅ נכנס למצב Idle בזמן {timestamp}")
        # איפוס גרפיקה למצב idle
        if hasattr(self.context, '_graphics'):
            state_cmd = Command(timestamp=timestamp, piece_id=None, type="state_change", 
                              params={"target_state": "idle"})
            self.context._graphics.reset(state_cmd)
    
    def exit(self) -> None:
        print(f"🚪 יוצא ממצב Idle")
    
    def update(self, now_ms: int) -> Optional["BaseState"]:
        # במצב idle, רק עדכן graphics ואל תחזיר מצב חדש
        if hasattr(self.context, '_graphics'):
            self.context._graphics.update(now_ms)
        return None
    
    def handle_command(self, cmd: Command) -> Optional["BaseState"]:
        """במצב idle יכול לקבל פקודות move ו-jump"""
        if cmd.type == "move":
            return MoveState(self.context)
        elif cmd.type == "jump":
            return JumpState(self.context)
        return None
    
    def get_state_name(self) -> str:
        return "idle"

class MoveState(BaseState):
    """מצב תנועה עם אנימציה"""
    
    def enter(self, timestamp: int) -> None:
        super().enter(timestamp)
        print(f"🏃 נכנס למצב Move בזמן {timestamp}")
        # עדכן גרפיקה למצב move
        if hasattr(self.context, '_graphics'):
            state_cmd = Command(timestamp=timestamp, piece_id=None, type="state_change", 
                              params={"target_state": "move"})
            self.context._graphics.reset(state_cmd)
    
    def exit(self) -> None:
        print(f"🚪 יוצא ממצב Move")
    
    def update(self, now_ms: int) -> Optional["BaseState"]:
        # עדכן גרפיקה ופיזיקה
        if hasattr(self.context, '_graphics'):
            self.context._graphics.update(now_ms)
        
        # בדוק אם הפיזיקה סיימה את התנועה
        if hasattr(self.context, '_physics'):
            cmd = self.context._physics.update(now_ms)
            if cmd and cmd.type == "arrived":
                # הוסף פקודת arrived לתור המשחק
                if hasattr(self.context, '_game_queue') and self.context._game_queue:
                    self.context._game_queue.put(cmd)
                # עבור למצב מנוחה ארוכה
                return RestLongState(self.context)
        
        return None
    
    def handle_command(self, cmd: Command) -> Optional["BaseState"]:
        """במצב move לא מקבל פקודות חדשות עד שמסיים"""
        print(f"🚫 Move State: דוחה פקודה {cmd.type} - עדיין בתנועה")
        return None
    
    def can_accept_command(self, cmd: Command) -> bool:
        return False  # לא מקבל פקודות במהלך תנועה
    
    def get_state_name(self) -> str:
        return "move"

class JumpState(BaseState):
    """מצב קפיצה מיידית"""
    
    def enter(self, timestamp: int) -> None:
        super().enter(timestamp)
        print(f"🦘 נכנס למצב Jump בזמן {timestamp}")
        # עדכן גרפיקה למצב jump
        if hasattr(self.context, '_graphics'):
            state_cmd = Command(timestamp=timestamp, piece_id=None, type="state_change", 
                              params={"target_state": "jump"})
            self.context._graphics.reset(state_cmd)
    
    def exit(self) -> None:
        print(f"🚪 יוצא ממצב Jump")
    
    def update(self, now_ms: int) -> Optional["BaseState"]:
        # עדכן גרפיקה
        if hasattr(self.context, '_graphics'):
            self.context._graphics.update(now_ms)
        
        # קפיצה מיידית - עבור ישר למצב מנוחה קצרה
        return RestShortState(self.context)
    
    def handle_command(self, cmd: Command) -> Optional["BaseState"]:
        """במצב jump לא מקבל פקודות חדשות"""
        print(f"🚫 Jump State: דוחה פקודה {cmd.type} - בקפיצה")
        return None
    
    def can_accept_command(self, cmd: Command) -> bool:
        return False
    
    def get_state_name(self) -> str:
        return "jump"

class RestShortState(BaseState):
    """מצב מנוחה קצרה (2 שניות)"""
    
    REST_DURATION = 2000  # 2 שניות במילישניות
    
    def enter(self, timestamp: int) -> None:
        super().enter(timestamp)
        print(f"💤 נכנס למצב RestShort בזמן {timestamp} למשך {self.REST_DURATION/1000} שניות")
        # עדכן גרפיקה למצב מנוחה קצרה
        if hasattr(self.context, '_graphics'):
            state_cmd = Command(timestamp=timestamp, piece_id=None, type="state_change", 
                              params={"target_state": "rest_short"})
            self.context._graphics.reset(state_cmd)
    
    def exit(self) -> None:
        print(f"🚪 יוצא ממצב RestShort")
    
    def update(self, now_ms: int) -> Optional["BaseState"]:
        # עדכן גרפיקה
        if hasattr(self.context, '_graphics'):
            self.context._graphics.update(now_ms)
        
        # בדוק אם המנוחה הסתיימה
        if self.entry_time and now_ms - self.entry_time >= self.REST_DURATION:
            elapsed = (now_ms - self.entry_time) / 1000
            print(f"⏰ מנוחה קצרה הסתיימה אחרי {elapsed:.1f} שניות")
            return IdleState(self.context)
        
        return None
    
    def handle_command(self, cmd: Command) -> Optional["BaseState"]:
        """במצב מנוחה דוחה פקודות תנועה"""
        if cmd.type in ("move", "jump"):
            remaining_ms = self.REST_DURATION - (cmd.timestamp - self.entry_time) if self.entry_time else 0
            remaining_sec = max(0, remaining_ms / 1000)
            print(f"🚫 RestShort: דוחה פקודת {cmd.type} - נותרו {remaining_sec:.1f} שניות")
        return None
    
    def can_accept_command(self, cmd: Command) -> bool:
        return cmd.type not in ("move", "jump")
    
    def get_state_name(self) -> str:
        return "rest_short"

class RestLongState(BaseState):
    """מצב מנוחה ארוכה (5 שניות)"""
    
    REST_DURATION = 5000  # 5 שניות במילישניות
    
    def enter(self, timestamp: int) -> None:
        super().enter(timestamp)
        print(f"💤 נכנס למצב RestLong בזמן {timestamp} למשך {self.REST_DURATION/1000} שניות")
        # עדכן גרפיקה למצב מנוחה ארוכה
        if hasattr(self.context, '_graphics'):
            state_cmd = Command(timestamp=timestamp, piece_id=None, type="state_change", 
                              params={"target_state": "rest_long"})
            self.context._graphics.reset(state_cmd)
    
    def exit(self) -> None:
        print(f"🚪 יוצא ממצב RestLong")
    
    def update(self, now_ms: int) -> Optional["BaseState"]:
        # עדכן גרפיקה
        if hasattr(self.context, '_graphics'):
            self.context._graphics.update(now_ms)
        
        # בדוק אם המנוחה הסתיימה
        if self.entry_time and now_ms - self.entry_time >= self.REST_DURATION:
            elapsed = (now_ms - self.entry_time) / 1000
            print(f"⏰ מנוחה ארוכה הסתיימה אחרי {elapsed:.1f} שניות")
            return IdleState(self.context)
        
        return None
    
    def handle_command(self, cmd: Command) -> Optional["BaseState"]:
        """במצב מנוחה דוחה פקודות תנועה"""
        if cmd.type in ("move", "jump"):
            remaining_ms = self.REST_DURATION - (cmd.timestamp - self.entry_time) if self.entry_time else 0
            remaining_sec = max(0, remaining_ms / 1000)
            print(f"🚫 RestLong: דוחה פקודת {cmd.type} - נותרו {remaining_sec:.1f} שניות")
        return None
    
    def can_accept_command(self, cmd: Command) -> bool:
        return cmd.type not in ("move", "jump")
    
    def get_state_name(self) -> str:
        return "rest_long"
