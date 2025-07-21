from typing import Tuple, Optional
from Command import Command
from Board import Board


class Physics:

    def __init__(self, start_cell: Tuple[int, int],
                 board: Board, speed_m_s: float = 1.0):
        """Initialize physics with starting cell, board, and speed."""
        pass

    def reset(self, cmd: Command):
        """Reset physics state with a new command."""
        pass

    def update(self, now_ms: int) -> Command:
        """Update physics state based on current time."""
        pass

    def can_be_captured(self) -> bool:
        """Check if this piece can be captured."""
        pass

    def can_capture(self) -> bool:
        """Check if this piece can capture other pieces."""
        pass

    def get_pos(self) -> Tuple[int, int]:
        """
        Current pixel-space upper-left corner of the sprite in world coordinates (in meters).
        """
        pass

class IdlePhysics(Physics):
    ...

class MovePhysics(Physics):
    ...

