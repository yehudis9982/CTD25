import queue, threading, time, cv2
from typing import List
from Board import Board
from Command import Command
from Piece import Piece

class InvalidBoard(Exception): ...

class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        """Initialize the game with pieces and board."""
        self.pieces = pieces
        self.board = board
        self.user_input_queue = queue.Queue()
        self.game_over = False

    def game_time_ms(self) -> int:
        """Return the current game time in milliseconds."""
        return int(time.monotonic() * 1000)

    def clone_board(self) -> Board:
        """Return a copy of the board for drawing."""
        return self.board.clone()

    def run(self):
        """Main game loop."""
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)

        while not self.game_over:
            now = self.game_time_ms()

            # Update physics & animations
            for p in self.pieces:
                p.update(now)

            # Handle queued Commands
            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)
                
                if self.game_over:
                    break

            # Draw and show
            self._draw()
            if not self._show():
                break

            # Frame rate control
            time.sleep(1/60.0)

        print("🎮 Game Over!")
        cv2.destroyAllWindows()

    def _process_input(self, cmd: Command):
        """Process input commands."""
        if cmd.type == "arrived":
            self._handle_arrival(cmd)
            return
        
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                piece.on_command(cmd, self.game_time_ms())
                
                if self._is_win():
                    self._announce_win()
                    self.game_over = True
                    return
                break

    def _handle_arrival(self, cmd: Command):
        """Handle piece arrival and check for captures."""
        arriving_piece = None
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                arriving_piece = piece
                break
        
        if not arriving_piece:
            return
        
        target_pos = arriving_piece._state._physics.cell
        
        # Check for captures
        pieces_to_remove = []
        for piece in self.pieces:
            if piece != arriving_piece:
                piece_pos = piece._state._physics.cell
                if piece_pos == target_pos:
                    arriving_is_white = 'W' in arriving_piece.piece_id
                    piece_is_white = 'W' in piece.piece_id
                    
                    if arriving_is_white != piece_is_white:  # Different colors
                        pieces_to_remove.append(piece)
        
        # Remove captured pieces
        for piece in pieces_to_remove:
            if piece in self.pieces:
                self.pieces.remove(piece)
        
        # Check win condition after capture
        if pieces_to_remove and self._is_win():
            self._announce_win()
            self.game_over = True

    def _draw(self):
        """Draw the current game state."""
        display_board = self.clone_board()
        
        now = self.game_time_ms()
        for p in self.pieces:
            p.draw_on_board(display_board, now)
        
        if hasattr(display_board, "img"):
            cv2.imshow("Chess Game", display_board.img.img)

    def _show(self) -> bool:
        """Show the current frame and handle window events."""
        key = cv2.waitKey(30) & 0xFF
        
        if key == 27 or key == ord('q'):  # ESC or Q
            self.game_over = True
            return False
        
        return True

    def _is_win(self) -> bool:
        """Check if the game has ended."""
        white_king_alive = any(p.piece_id == "KW0" for p in self.pieces)
        black_king_alive = any(p.piece_id == "KB0" for p in self.pieces)
        
        return not white_king_alive or not black_king_alive

    def _announce_win(self):
        """Announce the winner."""
        white_king_alive = any(p.piece_id == "KW0" for p in self.pieces)
        black_king_alive = any(p.piece_id == "KB0" for p in self.pieces)
        
        if not white_king_alive:
            print("🏆 BLACK WINS! White King captured!")
        elif not black_king_alive:
            print("🏆 WHITE WINS! Black King captured!")
        else:
            print("🎮 Game Over!")
