from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from typing import Dict, Optional
import time


class State:
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics, game_queue=None):
        self.moves, self.graphics, self.physics = moves, graphics, physics
        self._game_queue = game_queue  # תור פקודות של המשחק
        self.transitions: Dict[str, "State"] = {}
        self.cooldown_end_ms = 0
        self.name: Optional[str] = None
        self._last_cmd: Optional[Command] = None

    def __repr__(self):
        return f"State({self.name})"

    # configuration ------------
    def set_transition(self, event: str, target: "State"):
        self.transitions[event] = target

    # runtime -------------------
    def reset(self, cmd: Command):
        # החלף לאנימציה של המצב הנוכחי
        if hasattr(self.graphics, 'switch_to_state') and self.name:
            self.graphics.switch_to_state(self.name)
        else:
            self.graphics.reset(cmd)
            
        self.physics.reset(cmd)
        self._last_cmd = cmd
        
        # הגדר cooldown לפי סוג הפקודה
        if cmd.type == "move":
            self.cooldown_end_ms = getattr(cmd, 'timestamp', 0) + 5000  # 5 שניות
        elif cmd.type == "jump":
            self.cooldown_end_ms = getattr(cmd, 'timestamp', 0) + 2000  # 2 שניות

    def can_transition(self, now_ms: int) -> bool:           # customise per state
        return now_ms >= self.cooldown_end_ms

    def get_state_after_command(self, cmd: Command, now_ms: int) -> "State":
        nxt = self.transitions.get(cmd.type)

        # ── internal transition fired by Physics.update() ─────────────────
        if cmd.type == "arrived" and nxt:

            # 1️⃣ choose rest length according to the *previous* action
            if self.name == "move":
                rest_ms = 5000  # long rest after Move
            elif self.name == "jump":
                rest_ms = 2000  # short rest after Jump
            else:  # long_rest → idle, idle → idle, …
                rest_ms = 0

            # 2️⃣ restart graphics of the next state
            if hasattr(nxt.graphics, 'switch_to_state') and nxt.name:
                nxt.graphics.switch_to_state(nxt.name)
            else:
                nxt.graphics.reset(cmd)

            # 3️⃣ arm the Physics timer *only if* we have to wait
            if rest_ms:
                p = nxt.physics
                if hasattr(p, 'start_ms'):
                    p.start_ms = now_ms  # timer starts *now*
                if hasattr(p, 'duration_ms'):
                    p.duration_ms = rest_ms
                if hasattr(p, 'wait_only'):
                    p.wait_only = True

                nxt.cooldown_end_ms = now_ms + rest_ms
                
                # וודא שהגרפיקה רצה במהלך ה-rest
                nxt.graphics.running = True
            else:
                nxt.cooldown_end_ms = 0
                # אם אין rest, וודא שהגרפיקה של idle רצה
                nxt.graphics.running = True

            return nxt

        if nxt is None:
            return self                      # stay put

        # ✅ בדיקת cooldown רק לפקודות חיצוניות (לא arrived)
        if cmd.type != "arrived" and not self.can_transition(now_ms):
            return self  # לא מעבירים פקודה במהלך cooldown

        # if cooldown expired, perform the transition
        if self.can_transition(now_ms):
            nxt.reset(cmd)                   # this starts the travel
            return nxt

        # cooldown not finished → refresh current physics/graphics
        self.reset(cmd)
        return self

    def update(self, now_ms: int) -> "State":
        internal = self.physics.update(now_ms)
        if internal:
            # אם זו פקודת arrived, הוסף אותה לתור של המשחק
            if internal.type == "arrived" and self._game_queue is not None:
                self._game_queue.put(internal)
            return self.get_state_after_command(internal, now_ms)
        self.graphics.update(now_ms)
        return self

    def get_command(self) -> Optional[Command]:
        return self._last_cmd

    # מתודות תואמות למבנה הישן
    def process_command(self, cmd: Command) -> "State":
        """תואמות עם הממשק הישן"""
        return self.get_state_after_command(cmd, getattr(cmd, 'timestamp', 0))

    @property
    def state(self) -> str:
        """תואמות עם הממשק הישן"""
        return self.name or "unknown"
    
    def _transition(self, event: str, now_ms: int):
        """תואמות עם הממשק הישן"""
        return self.get_state_after_command(
            Command(now_ms, None, event, []), now_ms
        )
