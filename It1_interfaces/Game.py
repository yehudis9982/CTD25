import inspect
import pathlib
import queue, threading, time, cv2, math
from typing import List, Dict, Tuple, Optional
from CTD25.It1_interfaces.img     import Img
from CTD25.It1_interfaces.Board import Board
from CTD25.It1_interfaces.Command import Command
from CTD25.It1_interfaces.Piece import Piece

class InvalidBoard(Exception): ...
# ────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        """Initialize the game with pieces, board, and optional event bus."""
        self.pieces = { p.piece_id : p for p in pieces}
        self.board = board
        self.user_input_queue = queue.Queue()

    # ─── helpers ─────────────────────────────────────────────────────────────
    def game_time_ms(self) -> int:
        """Return the current game time in milliseconds."""
        return int(time.monotonic() * 1000)

    def clone_board(self) -> Board:
        """
        Return a **brand-new** Board wrapping a copy of the background pixels
        so we can paint sprites without touching the pristine board.
        """
        if hasattr(self.board, "copy"):
            return self.board.copy()
        return self.board  # fallback

    def start_user_input_thread(self):
        """Start the user input thread for mouse handling."""
        self.user_input_queue = queue.Queue()
        # אפשר להפעיל thread אמיתי בעתיד

    # ─── main public entrypoint ──────────────────────────────────────────────
    def run(self):
        """Main game loop."""
        self.start_user_input_thread() # QWe2e5

        start_ms = self.game_time_ms()
        for p in self.pieces.values():
            p.reset(start_ms)

        # ─────── main loop ──────────────────────────────────────────────────
        while not self._is_win():
            now = self.game_time_ms() # monotonic time ! not computer time.

            # (1) update physics & animations
            for p in self.pieces.values():
                p.update(now)

            # (2) handle queued Commands from mouse thread
            while not self.user_input_queue.empty(): # QWe2e5
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)

            # (3) draw current position
            self._draw()
            if not self._show():           # returns False if user closed window
                break

            # (4) detect captures
            self._resolve_collisions()

        self._announce_win()
        cv2.destroyAllWindows()

    # ─── drawing helpers ────────────────────────────────────────────────────
    def _process_input(self, cmd : Command):
        if cmd.piece_id in self.pieces:
            self.pieces[cmd.piece_id].on_command(cmd, self.game_time_ms())

    def _draw(self):
        """Draw the current game state."""
        # נניח של-board יש draw או img
        if hasattr(self.board, "draw"):
            self.board.draw()
        # ציור כל הכלים
        for p in self.pieces.values():
            p.draw_on_board(self.board, self.game_time_ms())
        # הצגה (אם יש board.img)
        if hasattr(self.board, "img"):
            cv2.imshow("Game", self.board.img)

    def _show(self) -> bool:
        """Show the current frame and handle window events."""
        key = cv2.waitKey(1)
        # סגור חלון אם לוחצים על ESC
        if key == 27:
            return False
        return True

    # ─── capture resolution ────────────────────────────────────────────────
    def _resolve_collisions(self):
        """Resolve piece collisions and captures."""
        pass  # לממש לוגיקת תפיסות בהמשך

    # ─── board validation & win detection ───────────────────────────────────
    def _is_win(self) -> bool:
        """Check if the game has ended."""
        return False  # לממש תנאי ניצחון בהמשך

    def _announce_win(self):
        """Announce the winner."""
        print("Game Over!")
