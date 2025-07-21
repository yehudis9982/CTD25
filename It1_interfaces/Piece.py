from Board import Board
from Command import Command
from State import State
import cv2


class Piece:
    def __init__(self, piece_id: str, init_state: State):
        """Initialize a piece with ID and initial state."""
        self._state = init_state
        pass

    def on_command(self, cmd: Command, now_ms: int):
        """Handle a command for this piece."""
        if self.is_command_possible(cmd):
            self._state = self._state.process_command(cmd)
            self._state.update(now_ms)
        pass

    def reset(self, start_ms: int):
        self._state.reset()
        """Reset the piece to idle state."""
        pass

    def update(self, now_ms: int):
        """Update the piece state based on current time."""
        pass

    def draw_on_board(self, board, now_ms: int):
        """Draw the piece on the board with cooldown overlay."""
        pass
