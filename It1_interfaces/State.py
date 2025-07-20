from Command import Command
from Moves import Moves
from Graphics import Graphics
from Physics import Physics
from typing import Dict
import time


class State:
    def __init__(self, moves: Moves, graphics: Graphics, physics: Physics):
        """Initialize state with moves, graphics, and physics components."""
        pass

    def set_transition(self, event: str, target: "State"):
        """Set a transition from this state to another state on an event."""
        pass

    def reset(self, cmd: Command):
        """Reset the state with a new command."""
        pass

    def can_transition(self, now_ms: int) -> bool:           # customise per state
        """Check if the state can transition."""
        pass

    def get_state_after_command(self, cmd: Command, now_ms: int) -> "State":
        """Get the next state after processing a command."""
        pass

    def update(self, now_ms: int) -> "State":
        """Update the state based on current time."""
        pass

    def get_command(self) -> Command:
        """Get the current command for this state."""
        pass