from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from State import State
from typing import Dict
import time


class State:
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics):
        self._graphics = graphics
        self._physics = physics
        self.transitions = {}
        """Initialize state with moves, graphics, and physics components."""
        pass

    def set_transition(self, event: str, target: State):
        """Set a transition from this state to another state on an event."""
        # event= "Move"
        self.transitions[event] = target
        pass

    def reset(self, cmd: Command):
        """Reset the state with a new command."""
        self._graphics.reset()
        self._physics.reset()
        pass

    def update(self, now_ms: int) -> State:
        """Update the state based on current time."""
        self._graphics.reset(now_ms)
        cmd = self._physics.reset(now_ms)
        if cmd is not None:
            return self.process_command(cmd)

        return self

    def process_command(self, cmd: Command, now_ms: int) -> State:
        """Get the next state after processing a command."""
        # Command = QBMe5e8
        # transitions = {
        #     "Move" : state_move
        #     "Jump" : state_jmp
        # }
        res = self.transitions[cmd.type]
        if res is None:
            return None

        res.reset(cmd.timestamp)
        return res


    def can_transition(self, now_ms: int) -> bool:           # customise per state
        """Check if the state can transition."""
        pass


    def get_command(self) -> Command:
        """Get the current command for this state."""
        pass