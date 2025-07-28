from typing import Optional
from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from StatePattern import BaseState, IdleState

class StateContext:
    """
    Context class שמנהל את המצבים באמצעות State Pattern
    מחליף את המחלקה State הישנה
    """
    
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics, game_queue=None):
        self._moves = moves
        self._graphics = graphics
        self._physics = physics
        self._game_queue = game_queue
        
        # התחל במצב idle
        self._current_state: BaseState = IdleState(self)
        self._current_state.enter(0)
        
        self._last_cmd: Optional[Command] = None
    
    def reset(self, cmd: Command):
        """איפוס המצב עם פקודה חדשה"""
        print(f"🔧 StateContext.reset: קיבל פקודה {cmd.type}")
        self._last_cmd = cmd
        
        # איפוס הפיזיקה
        self._physics.reset(cmd)
        
        # אם זו פקודת תנועה, עבור למצב המתאים
        if cmd.type in ("move", "jump"):
            new_state = self._current_state.handle_command(cmd)
            if new_state:
                self._transition_to_state(new_state, getattr(cmd, "timestamp", 0))
        
        # איפוס הגרפיקה
        self._graphics.reset(cmd)
    
    def update(self, now_ms: int) -> "StateContext":
        """עדכן את המצב הנוכחי"""
        # בקש מהמצב הנוכחי להתעדכן ולבדוק אם צריך לעבור למצב אחר
        new_state = self._current_state.update(now_ms)
        
        if new_state:
            self._transition_to_state(new_state, now_ms)
        
        return self
    
    def process_command(self, cmd: Command) -> "StateContext":
        """עבד פקודה חדשה"""
        print(f"🔧 StateContext.process_command: מעבד פקודה {cmd.type}")
        
        # בדוק אם המצב הנוכחי יכול לקבל את הפקודה
        if not self._current_state.can_accept_command(cmd):
            print(f"🚫 המצב {self._current_state.get_state_name()} לא יכול לקבל פקודה {cmd.type}")
            return self
        
        # תן למצב הנוכחי לטפל בפקודה
        new_state = self._current_state.handle_command(cmd)
        
        if new_state:
            # טפל בפקודות מיוחדות לפני המעבר
            if cmd.type == "move":
                self._physics.reset(cmd)
            elif cmd.type == "jump":
                # עדכן מיקום מיידי לקפיצה
                if hasattr(self._physics, 'cell') and cmd.target:
                    old_pos = self._physics.cell
                    self._physics.cell = cmd.target
                    print(f"🎯 StateContext: עדכון מיקום מ-{old_pos} ל-{self._physics.cell}")
            
            self._transition_to_state(new_state, getattr(cmd, "timestamp", 0))
            self._last_cmd = cmd
        
        return self
    
    def _transition_to_state(self, new_state: BaseState, timestamp: int):
        """בצע מעבר למצב חדש"""
        old_state_name = self._current_state.get_state_name()
        
        # יצא מהמצב הנוכחי
        self._current_state.exit()
        
        # עבור למצב החדש
        self._current_state = new_state
        self._current_state.enter(timestamp)
        
        new_state_name = self._current_state.get_state_name()
        print(f"🔄 מעבר מצב: {old_state_name} -> {new_state_name}")
    
    # שיטות תאימות לממשק הישן
    def get_command(self) -> Optional[Command]:
        """החזר את הפקודה האחרונה (תאימות)"""
        return self._last_cmd
    
    def can_transition(self, now_ms: int) -> bool:
        """בדוק אם ניתן לעבור מצב (תאימות)"""
        return True
    
    @property
    def state(self) -> str:
        """קבל את שם המצב הנוכחי (תאימות)"""
        return self._current_state.get_state_name()
    
    @state.setter
    def state(self, value: str):
        """הגדר מצב (תאימות - לא מומלץ להשתמש)"""
        print(f"⚠️ שימוש ישן ב-state setter: {value}")
    
    # Properties לגישה לרכיבים פנימיים
    @property
    def moves(self):
        return self._moves
    
    @property
    def graphics(self):
        return self._graphics
    
    @property
    def physics(self):
        return self._physics
