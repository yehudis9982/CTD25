from Board import Board
from Command import Command
from State import State
import cv2


class Piece:
    def __init__(self, piece_id: str, init_state: State):
        """Initialize a piece with ID and initial state."""
        self.piece_id = piece_id
        self._state = init_state

    def on_command(self, cmd: Command, now_ms: int):
        """Handle a command for this piece."""
        if hasattr(self._state, "process_command"):
            new_state = self._state.process_command(cmd)
            if new_state:
                self._state = new_state
        if hasattr(self._state, "update"):
            new_state = self._state.update(now_ms)
            if new_state:
                self._state = new_state

    def reset(self, start_ms: int = 0):
        """Reset the piece to idle state."""
        if hasattr(self._state, "reset"):
            self._state.reset(Command(timestamp=start_ms, piece_id=self.piece_id, type="reset", params=None))

    def update(self, now_ms: int):
        """Update the piece state based on current time."""
        if hasattr(self._state, "update"):
            new_state = self._state.update(now_ms)
            if new_state:
                self._state = new_state

    def draw_on_board(self, board: Board, now_ms: int):
        """
        Draw the piece on the board using its graphics and physics position.
        משתמש ב-pixel_pos עבור אנימציה חלקה במקום cell
        """
        # תמיכה בשני הסוגים: NewState (graphics, physics) ו-State הישן (_graphics, _physics)
        graphics = getattr(self._state, "graphics", None) or getattr(self._state, "_graphics", None)
        physics = getattr(self._state, "physics", None) or getattr(self._state, "_physics", None)
        if graphics is not None and physics is not None:
            img = graphics.get_img()
            # השתמש במיקום הפיקסל החלק במקום תא
            pixel_pos = getattr(physics, "pixel_pos", None)
            if pixel_pos is not None:
                x, y = pixel_pos
                img.draw_on(board.img, x, y)
