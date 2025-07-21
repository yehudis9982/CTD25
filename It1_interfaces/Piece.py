from CTD25.It1_interfaces.Board import Board
from CTD25.It1_interfaces.Command import Command
from CTD25.It1_interfaces.State import State
import cv2


class Piece:
    def __init__(self, piece_id: str, init_state: State):
        """Initialize a piece with ID and initial state."""
        self.piece_id = piece_id
        self._state = init_state

    def on_command(self, cmd: Command, now_ms: int):
        """Handle a command for this piece."""
        if hasattr(self._state, "process_command"):
            self._state = self._state.process_command(cmd)
        if hasattr(self._state, "update"):
            self._state.update(now_ms)

    def reset(self, start_ms: int = 0):
        """Reset the piece to idle state."""
        if hasattr(self._state, "reset"):
            self._state.reset(Command(timestamp=start_ms, piece_id=self.piece_id, type="reset", params=None))

    def update(self, now_ms: int):
        """Update the piece state based on current time."""
        if hasattr(self._state, "update"):
            self._state.update(now_ms)

    def draw_on_board(self, board: Board, now_ms: int):
        """
        Draw the piece on the board using its graphics and physics position.
        מניח של-state יש _graphics (עם get_img) ו-_physics (עם cell)
        """
        graphics = getattr(self._state, "_graphics", None)
        physics = getattr(self._state, "_physics", None)
        if graphics is not None and physics is not None:
            img = graphics.get_img()
            cell = getattr(physics, "cell", None)
            if cell is not None:
                x, y = board.cell_to_pixel(cell)
                img.draw_on(board.img, x, y)
            print(f"מצייר {self.piece_id} ב-{cell}")
