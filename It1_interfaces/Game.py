import inspect
import pathlib
import queue, threading, time, cv2, math
from typing import List, Dict, Tuple, Optional
from img     import Img
from Board import Board
from Command import Command
from Piece import Piece

class InvalidBoard(Exception): ...
# ────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        """Initialize the game with pieces and board."""
        self.pieces = pieces  # שמור כרשימה במקום כמילון
        self.board = board
        self.user_input_queue = queue.Queue()
        
        # מערכת שני שחקנים - ללא תורות
        self.selected_piece_player1 = None  # הכלי הנבחר של שחקן 1 (מקשי מספרים)
        self.selected_piece_player2 = None  # הכלי הנבחר של שחקן 2 (WASD)
        self.cursor_pos_player1 = [0, 7]  # מיקום הסמן של שחקן 1 (כלים לבנים) - התחל ליד הכלים הלבנים בשורה 7
        self.cursor_pos_player2 = [0, 0]  # מיקום הסמן של שחקן 2 (כלים שחורים) - התחל ליד הכלים השחורים בשורה 0
        
        # דגל סיום המשחק
        self.game_over = False

    # ─── helpers ─────────────────────────────────────────────────────────────
    def game_time_ms(self) -> int:
        """Return the current game time in milliseconds."""
        return int(time.monotonic() * 1000)

    def clone_board(self) -> Board:
        """
        Return a **brand-new** Board wrapping a copy of the background pixels
        so we can paint sprites without touching the pristine board.
        """
        return self.board.clone()

    def start_user_input_thread(self):
        """Start the user input thread for mouse handling."""
        self.user_input_queue = queue.Queue()
        # אפשר להפעיל thread אמיתי בעתיד

    # ─── main public entrypoint ──────────────────────────────────────────────
    def run(self):
        """Main game loop."""
        self.start_user_input_thread() # QWe2e5

        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)

        # ─────── main loop ──────────────────────────────────────────────────
        while not self.game_over:
            now = self.game_time_ms() # monotonic time ! not computer time.

            # (1) update physics & animations
            for p in self.pieces:
                p.update(now)

            # (2) handle queued Commands from mouse thread
            while not self.user_input_queue.empty(): # QWe2e5
                cmd: Command = self.user_input_queue.get()
                print(f"🎯 QUEUE DEBUG: Got command from queue: type='{cmd.type}', piece_id='{cmd.piece_id}', target={cmd.target}")
                self._process_input(cmd)
                
                # בדוק אם המשחק נגמר
                if self.game_over:
                    break

            # (3) draw current position
            self._draw()
            if not self._show():           # returns False if user closed window
                break

            # (4) detect captures
            self._resolve_collisions()
            
            # (5) שליטה בקצב פריימים - 60 FPS
            import time
            time.sleep(1/60.0)  # ~16.7ms המתנה

        # אם המשחק נגמר בגלל נצחון ולא בגלל סגירת החלון
        if self.game_over:
            print("🎮 המשחק הסתיים עקב נצחון!")
            print("🎮 Game ended due to victory!")
        else:
            print("🎮 המשחק נגמר!")
            print("🎮 Game Over!")
        cv2.destroyAllWindows()

    # ─── drawing helpers ────────────────────────────────────────────────────
    def _process_input(self, cmd : Command):
        # חפש את הכלי לפי piece_id
        print(f"🔧 מעבד פקודה: {cmd.type} עבור {cmd.piece_id} ל-{cmd.target}")
        print(f"🔍 DEBUG: cmd type is '{cmd.type}', length: {len(cmd.type) if cmd.type else 'None'}")
        print(f"🔍 DEBUG: cmd.type == 'arrived': {cmd.type == 'arrived'}")
        print(f"🔍 DEBUG: repr(cmd.type): {repr(cmd.type)}")
        print(f"🔍 DEBUG: cmd.type.strip() == 'arrived': {cmd.type.strip() == 'arrived' if cmd.type else False}")
        
        # אם זו פקודת arrived - בדוק תפיסה
        if cmd.type == "arrived" or (cmd.type and cmd.type.strip() == "arrived"):
            print(f"🏁 מעבד פקודת ARRIVED עבור {cmd.piece_id}")
            self._handle_arrival(cmd)
            return
        
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                print(f"✅ נמצא כלי {piece.piece_id}, שולח פקודה...")
                piece.on_command(cmd, self.game_time_ms())
                
                # 🏆 בדיקת תנאי נצחון אחרי כל תנועה!
                if self._is_win():
                    self._announce_win()
                    self.game_over = True  # סמן שהמשחק נגמר
                    return  # עצור את המשחק
                break
        else:
            print(f"❌ לא נמצא כלי עם ID: {cmd.piece_id}")

    def _handle_arrival(self, cmd: Command):
        """Handle piece arrival and check for captures."""
        print(f"🏁 כלי הגיע ליעד: {cmd.piece_id}")
        
        # מצא את הכלי שהגיע ליעד
        arriving_piece = None
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                arriving_piece = piece
                break
        
        if not arriving_piece:
            print(f"❌ לא נמצא כלי שהגיע: {cmd.piece_id}")
            return
        
        # קבל את המיקום של הכלי שהגיע
        target_pos = arriving_piece._state._physics.cell
        print(f"🎯 בודק תפיסה במיקום {target_pos}")
        print(f"🔍 רשימת כל הכלים והמיקומים שלהם:")
        
        # הצג את כל הכלים והמיקומים שלהם
        for piece in self.pieces:
            piece_pos = piece._state._physics.cell
            print(f"   {piece.piece_id} במיקום {piece_pos}")
        
        # חפש כלי יריב באותו מיקום
        pieces_to_remove = []
        for piece in self.pieces:
            if piece != arriving_piece:  # לא אותו כלי
                piece_pos = piece._state._physics.cell
                print(f"🔍 בודק {piece.piece_id} במיקום {piece_pos} מול {target_pos}")
                if piece_pos == target_pos:
                    # בדוק אם זה כלי יריב
                    arriving_is_white = 'W' in arriving_piece.piece_id
                    piece_is_white = 'W' in piece.piece_id
                    
                    print(f"🎯 מצאתי כלי באותו מיקום! {piece.piece_id} (לבן: {piece_is_white}) vs {arriving_piece.piece_id} (לבן: {arriving_is_white})")
                    
                    if arriving_is_white != piece_is_white:  # צבעים שונים = יריבים
                        print(f"⚔️ {arriving_piece.piece_id} תפס את {piece.piece_id} במיקום {target_pos}!")
                        pieces_to_remove.append(piece)
                        
                        # בדיקה מיוחדת למלכים
                        if piece.piece_id in ["KW0", "KB0"]:
                            print(f"🚨🚨 CRITICAL: KING CAPTURED! {piece.piece_id} was taken! 🚨🚨🚨")
                            print(f"💀 מלך נהרג: {piece.piece_id}")
                            print(f"🔥 זה יגרום לסיום המשחק!")
                    else:
                        print(f"🛡️ אותו צבע - לא תוקף: {piece.piece_id} ו-{arriving_piece.piece_id}")
        
        print(f"📋 כלים לתפיסה: {[p.piece_id for p in pieces_to_remove]}")
        
        # הסר את הכלים הנתפסים
        for piece in pieces_to_remove:
            if piece in self.pieces:
                self.pieces.remove(piece)
                print(f"🗑️ הסרתי {piece.piece_id} מרשימת הכלים")
                
                # DEBUG נוסף - ספירת מלכים אחרי הסרה
                if piece.piece_id in ["KW0", "KB0"]:
                    remaining_kings = [p.piece_id for p in self.pieces if p.piece_id in ["KW0", "KB0"]]
                    print(f"👑 מלכים שנותרו אחרי הסרת {piece.piece_id}: {remaining_kings}")
                    print(f"📊 סה'כ כלים נותרים: {len(self.pieces)}")
                    
                    # בדיקה מיידית של תנאי נצחון
                    white_kings = [p for p in self.pieces if p.piece_id == "KW0"]
                    black_kings = [p for p in self.pieces if p.piece_id == "KB0"]
                    print(f"🔍 מלכים לבנים: {len(white_kings)}, מלכים שחורים: {len(black_kings)}")
                    
                    if len(white_kings) == 0:
                        print("🏆 אין מלך לבן - שחקן 2 אמור לנצח!")
                    if len(black_kings) == 0:
                        print("🏆 אין מלך שחור - שחקן 1 אמור לנצח!")
        
        # בדוק תנאי נצחון אחרי תפיסה
        if pieces_to_remove:
            if self._is_win():
                self._announce_win()
                self.game_over = True
                self.game_over = True

    def _draw(self):
        """Draw the current game state."""
        # צור עותק נקי של הלוח לכל פריים
        display_board = self.clone_board()
        
        # ציור כל הכלים על העותק
        now = self.game_time_ms()
        for p in self.pieces:
            p.draw_on_board(display_board, now)
        
        # ציור סמנים של השחקנים
        self._draw_cursors(display_board)
        
        # הצגה
        if hasattr(display_board, "img"):
            cv2.imshow("Chess Game", display_board.img.img)

    def _draw_cursors(self, board):
        """Draw player cursors on the board."""
        print(f"Drawing cursors - Player1: {self.cursor_pos_player1}, Player2: {self.cursor_pos_player2}")
        if hasattr(board, 'img') and hasattr(board.img, 'img'):
            print("Board has img!")
            img = board.img.img
            
            # חישוב גודל משבצת
            board_height, board_width = img.shape[:2]
            cell_width = board_width // 8
            cell_height = board_height // 8
            
            # ציור סמן שחקן 1 (כחול עבה)
            x1, y1 = self.cursor_pos_player1
            top_left_1 = (x1 * cell_width, y1 * cell_height)
            bottom_right_1 = ((x1 + 1) * cell_width - 1, (y1 + 1) * cell_height - 1)
            cv2.rectangle(img, top_left_1, bottom_right_1, (255, 0, 0), 8)  # כחול BGR עבה מאוד
            print(f"Drew THICK blue cursor at {top_left_1}-{bottom_right_1}")
            
            # ציור סמן שחקן 2 (אדום עבה)
            x2, y2 = self.cursor_pos_player2
            top_left_2 = (x2 * cell_width, y2 * cell_height)
            bottom_right_2 = ((x2 + 1) * cell_width - 1, (y2 + 1) * cell_height - 1)
            cv2.rectangle(img, top_left_2, bottom_right_2, (0, 0, 255), 8)  # אדום BGR עבה מאוד
            print(f"Drew THICK red cursor at {top_left_2}-{bottom_right_2}")
            
            # סימון כלי נבחר - צריך להיות על הכלי עצמו, לא על הסמן
            if self.selected_piece_player1:
                # מצא את מיקום הכלי הנבחר של שחקן 1
                piece_pos = self._get_piece_position(self.selected_piece_player1)
                if piece_pos:
                    px, py = piece_pos
                    piece_top_left = (px * cell_width, py * cell_height)
                    piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
                    cv2.rectangle(img, piece_top_left, piece_bottom_right, (0, 255, 0), 4)  # ירוק עבה
                    print(f"Added green selection for player 1 at piece position {piece_pos}")
            
            if self.selected_piece_player2:
                # מצא את מיקום הכלי הנבחר של שחקן 2
                piece_pos = self._get_piece_position(self.selected_piece_player2)
                if piece_pos:
                    px, py = piece_pos
                    piece_top_left = (px * cell_width, py * cell_height)
                    piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
                    cv2.rectangle(img, piece_top_left, piece_bottom_right, (0, 255, 255), 4)  # צהוב עבה
                    print(f"Added yellow selection for player 2 at piece position {piece_pos}")
        else:
            print("No board img found for cursor drawing!")

    def _show(self) -> bool:
        """Show the current frame and handle window events."""
        # Make sure window is in focus
        cv2.setWindowProperty("Chess Game", cv2.WND_PROP_TOPMOST, 1)
        
        # קלט ללא חסימה - רק 30ms המתנה מקסימום
        key = cv2.waitKey(30) & 0xFF
        
        # עבד קלט אם נלחץ מקש
        if key != 255 and key != -1:
            if self._handle_keyboard_input(key):
                return False  # Exit if ESC was pressed
        
        return True

    def _handle_keyboard_input(self, key):
        """Handle keyboard input for both players."""
        print(f"\n=== KEY PRESSED: {key} ===")
        if 32 <= key <= 126:
            print(f"Character: '{chr(key)}'")
        else:
            print(f"Special key code: {key}")
        
        # Check for exit keys first
        if key == 27 or key == ord('q'):  # ESC או Q
            self.game_over = True  # סמן שהמשחק נגמר
            return True  # Signal to exit
        
        # Convert to character for easier handling
        char = None
        if 32 <= key <= 126:
            char = chr(key).lower()
        
        # Enhanced WASD detection for Player 2 (שחקן 2 שולט בכלים שחורים)
        wasd_detected = False
        
        # תמיכה מלאה במקלדת עברית! זיהוי מתקדם של מקשים עבריים
        hebrew_keys = {
            # Hebrew letter codes - ו (vav) = W
            1493: 'w', 215: 'w', 246: 'w', 1500: 'w',
            # Hebrew letter codes - ש (shin) = A  
            1513: 'a', 249: 'a', 251: 'a', 1506: 'a',
            # Hebrew letter codes - ד (dalet) = S
            1491: 's', 212: 's', 213: 's', 1504: 's',
            # Hebrew letter codes - כ (kaf) = D
            1499: 'd', 235: 'd', 237: 'd', 1507: 'd'
        }
        
        # בדיקת מקשים עבריים
        detected_hebrew = hebrew_keys.get(key)
        if detected_hebrew:
            print(f"🔥 זוהה מקש עברי: {key} -> {detected_hebrew}")
            char = detected_hebrew
        
        # W key (UP) - English W או עברית ו
        if (key in [119, 87] or char == 'w' or 
            key in [1493, 215, 246, 1500] or  # Hebrew ו (vav)
            detected_hebrew == 'w'):
            print("🔥 Player 2: Moving UP (W/ו) - WASD WORKING!")
            self._move_cursor_player2(0, -1)
            wasd_detected = True
        # S key (DOWN) - English S או עברית ד
        elif (key in [115, 83] or char == 's' or 
              key in [1491, 212, 213, 1504] or  # Hebrew ד (dalet)
              detected_hebrew == 's'):
            print("🔥 Player 2: Moving DOWN (S/ד) - WASD WORKING!")
            self._move_cursor_player2(0, 1)
            wasd_detected = True
        # A key (LEFT) - English A או עברית ש
        elif (key in [97, 65] or char == 'a' or 
              key in [1513, 249, 251, 1506] or  # Hebrew ש (shin)
              detected_hebrew == 'a'):
            print("🔥 Player 2: Moving LEFT (A/ש) - WASD WORKING!")
            self._move_cursor_player2(-1, 0)
            wasd_detected = True
        # D key (RIGHT) - English D או עברית כ
        elif (key in [100, 68] or char == 'd' or 
              key in [1499, 235, 237, 1507] or  # Hebrew כ (kaf)
              detected_hebrew == 'd'):
            print("🔥 Player 2: Moving RIGHT (D/כ) - WASD WORKING!")
            self._move_cursor_player2(1, 0)
            wasd_detected = True
        elif key == 32 or char == ' ':  # Space
            print("🔥 Player 2: Selecting piece (SPACE) - SPACE WORKING!")
            self._select_piece_player2()
            wasd_detected = True
        
        # מקשי חירום נוספים לשחקן 2 (אם WASD לא עובד)
        elif key in [255, 254, 253, 252]:  # מקשים מיוחדים כחלופה
            emergency_map = {255: 'w', 254: 's', 253: 'a', 252: 'd'}
            direction = emergency_map.get(key)
            if direction:
                print(f"🚨 Player 2: Emergency key {key} -> {direction}")
                if direction == 'w':
                    self._move_cursor_player2(0, -1)
                elif direction == 's':
                    self._move_cursor_player2(0, 1)
                elif direction == 'a':
                    self._move_cursor_player2(-1, 0)
                elif direction == 'd':
                    self._move_cursor_player2(1, 0)
                wasd_detected = True
        
        # Player 1 controls - מקשי מספרים - שחקן 1 שולט בכלים לבנים
        elif key == 56 or char == '8':  # 8 key
            print("⚡ Player 1: Moving UP (8) - NUMBERS WORKING!")
            self._move_cursor_player1(0, -1)
        elif key == 50 or char == '2':  # 2 key
            print("⚡ Player 1: Moving DOWN (2) - NUMBERS WORKING!")
            self._move_cursor_player1(0, 1)
        elif key == 52 or char == '4':  # 4 key
            print("⚡ Player 1: Moving LEFT (4) - NUMBERS WORKING!")
            self._move_cursor_player1(-1, 0)
        elif key == 54 or char == '6':  # 6 key
            print("⚡ Player 1: Moving RIGHT (6) - NUMBERS WORKING!")
            self._move_cursor_player1(1, 0)
        elif key == 53 or key == 48 or char == '5' or char == '0':  # 5 or 0 key
            print("⚡ Player 1: Selecting piece (5 or 0) - NUMBERS WORKING!")
            self._select_piece_player1()
        elif key in [13, 10, 39, 226, 249]:  # Enter - multiple codes for different systems
            print(f"⚡ Player 1: Selecting piece (Enter code: {key}) - ENTER WORKING!")
            self._select_piece_player1()
        
        else:
            if not wasd_detected:
                print(f"❓ Unknown key: {key}")
                if 32 <= key <= 126:
                    print(f"   Character: '{chr(key)}'")
                # Add ASCII codes for common keys
                key_map = {
                    119: 'w', 115: 's', 97: 'a', 100: 'd',
                    87: 'W', 83: 'S', 65: 'A', 68: 'D',
                    56: '8', 50: '2', 52: '4', 54: '6'
                }
                if key in key_map:
                    print(f"   Mapped character: '{key_map[key]}'")
        
        print("=== KEY PROCESSING COMPLETE ===\n")
        return False  # Don't exit

    def _move_cursor_player1(self, dx, dy):
        """Move player 1 cursor (numeric keys) - כלים לבנים."""
        old_pos = self.cursor_pos_player1.copy()
        new_x = max(0, min(7, self.cursor_pos_player1[0] + dx))
        new_y = max(0, min(7, self.cursor_pos_player1[1] + dy))
        self.cursor_pos_player1 = [new_x, new_y]
        print(f"⚡ שחקן 1 (מספרים): הזיז סמן מ-{old_pos} ל-{self.cursor_pos_player1}")

    def _move_cursor_player2(self, dx, dy):
        """Move player 2 cursor (WASD) - כלים שחורים."""
        old_pos = self.cursor_pos_player2.copy()
        new_x = max(0, min(7, self.cursor_pos_player2[0] + dx))
        new_y = max(0, min(7, self.cursor_pos_player2[1] + dy))
        self.cursor_pos_player2 = [new_x, new_y]
        print(f"🔥 שחקן 2 (WASD): הזיז סמן מ-{old_pos} ל-{self.cursor_pos_player2}")

    def _select_piece_player1(self):
        """Handle piece selection for player 1 (Enter key)."""
        x, y = self.cursor_pos_player1
        print(f"🎯 שחקן 1 מנסה לבחור כלי במיקום ({x}, {y})")
        print(f"PLAYER 1 SELECTION ATTEMPT AT POSITION ({x}, {y})")
        
        if self.selected_piece_player1 is None:
            # בחירת כלי חדש
            piece = self._find_piece_at_position(x, y)
            if piece and self._is_player_piece(piece, 1):
                self.selected_piece_player1 = piece
                print(f"✅ שחקן 1 בחר כלי: {piece.piece_id} במיקום ({x}, {y})")
                print(f"PLAYER 1 SELECTED PIECE: {piece.piece_id} AT ({x}, {y})")
            else:
                print(f"❌ שחקן 1: אין כלי לבן במיקום ({x}, {y})")
                print(f"PLAYER 1: NO WHITE PIECE AT ({x}, {y})")
                if piece:
                    is_white = self._is_player_piece(piece, 1)
                    print(f"כלי קיים: {piece.piece_id}, כלי לבן: {is_white}")
                    print(f"PIECE EXISTS: {piece.piece_id}, IS WHITE: {is_white}")
        else:
            # הזזת הכלי הנבחר
            print(f"🎯 שחקן 1 מזיז כלי {self.selected_piece_player1.piece_id} ל-({x}, {y})")
            print(f"PLAYER 1 MOVING PIECE {self.selected_piece_player1.piece_id} TO ({x}, {y})")
            self._move_piece(self.selected_piece_player1, x, y, 1)
            self.selected_piece_player1 = None

    def _select_piece_player2(self):
        """Handle piece selection for player 2 (Space key)."""
        x, y = self.cursor_pos_player2
        print(f"🎯 שחקן 2 מנסה לבחור כלי במיקום ({x}, {y})")
        
        if self.selected_piece_player2 is None:
            # בחירת כלי חדש
            piece = self._find_piece_at_position(x, y)
            if piece and self._is_player_piece(piece, 2):
                self.selected_piece_player2 = piece
                print(f"✅ שחקן 2 בחר כלי: {piece.piece_id} במיקום ({x}, {y})")
            else:
                print(f"❌ שחקן 2: אין כלי שחור במיקום ({x}, {y})")
                if piece:
                    is_black = self._is_player_piece(piece, 2)
                    print(f"כלי קיים: {piece.piece_id}, כלי שחור: {is_black}")
        else:
            # הזזת הכלי הנבחר
            print(f"🎯 שחקן 2 מזיז כלי {self.selected_piece_player2.piece_id} ל-({x}, {y})")
            self._move_piece(self.selected_piece_player2, x, y, 2)
            self.selected_piece_player2 = None

    def _get_piece_position(self, piece):
        """Get the current position of a piece."""
        if not piece:
            return None
            
        # בדיקה אם לכלי יש _state עם _physics עם cell
        if hasattr(piece, '_state') and hasattr(piece._state, '_physics'):
            physics = piece._state._physics
            if hasattr(physics, 'cell'):
                return physics.cell
        
        # פלטות נוספות
        if hasattr(piece, 'x') and hasattr(piece, 'y'):
            return (piece.x, piece.y)
        
        if hasattr(piece, 'board_position'):
            return piece.board_position
        
        return None

    def _get_piece_at_position(self, x, y):
        """Get piece at specific position, if any."""
        for piece in self.pieces:
            piece_pos = self._get_piece_position(piece)
            if piece_pos and piece_pos == (x, y):
                return piece
        return None

    def _find_piece_at_position(self, x, y):
        """Find piece at given board position."""
        print(f"מחפש כלי במיקום ({x}, {y})")
        
        for piece in self.pieces:
            piece_found = False
            piece_pos = None
            
            # בדיקה אם לכלי יש _state עם _physics עם cell
            if hasattr(piece, '_state') and hasattr(piece._state, '_physics'):
                physics = piece._state._physics
                if hasattr(physics, 'cell'):
                    piece_pos = physics.cell
                    if physics.cell == (x, y):
                        piece_found = True
                        print(f"מצא כלי {piece.piece_id} במיקום {piece_pos} via _state._physics.cell")
            
            # פלטות נוספות - בדיקת מיקום ישיר
            elif hasattr(piece, 'x') and hasattr(piece, 'y'):
                piece_pos = (piece.x, piece.y)
                if piece.x == x and piece.y == y:
                    piece_found = True
                    print(f"מצא כלי {piece.piece_id} במיקום {piece_pos} via x,y")
            
            elif hasattr(piece, 'board_position'):
                piece_pos = piece.board_position
                if piece.board_position == (x, y):
                    piece_found = True
                    print(f"מצא כלי {piece.piece_id} במיקום {piece_pos} via board_position")
            
            # Debug - הצג את מיקום כל כלי
            if piece_pos:
                print(f"כלי {piece.piece_id} נמצא במיקום {piece_pos}")
            else:
                print(f"כלי {piece.piece_id} - לא נמצא מיקום!")
            
            if piece_found:
                return piece
        
        print(f"לא נמצא כלי במיקום ({x}, {y})")
        return None

    def _is_player_piece(self, piece, player_num):
        """Check if piece belongs to specified player."""
        # שחקן 1 = כלים לבנים (W), שחקן 2 = כלים שחורים (B)
        # הכלים עכשיו מזוהים כ-PW0, PW1, PB0, PB1, etc.
        if player_num == 1:
            return 'W' in piece.piece_id  # כלים לבנים
        else:
            return 'B' in piece.piece_id  # כלים שחורים

    def _move_piece(self, piece, new_x, new_y, player_num):
        """Move piece to new position using Command system."""
        # בדיקה שהמהלך חוקי
        if not self._is_valid_move(piece, new_x, new_y, player_num):
            print(f"❌ מהלך לא חוקי ל-{piece.piece_id} ל-({new_x}, {new_y})")
            return
        
        # בדיקה אם יש כלי במיקום המטרה
        target_piece = self._get_piece_at_position(new_x, new_y)
        if target_piece:
            # בדוק אם זה כלי של האויב (אפשר לתפוס)
            if self._is_player_piece(target_piece, player_num):
                print(f"❌ לא ניתן לתפוס כלי של אותו שחקן: {target_piece.piece_id}")
                return
            else:
                print(f"⚔️ {piece.piece_id} תופס את {target_piece.piece_id}!")
                # בדיקה מיוחדת למלכים - DEBUG מורחב!
                if target_piece.piece_id in ["KW0", "KB0"]:
                    print(f"�🚨🚨 CRITICAL: KING CAPTURED! {target_piece.piece_id} was taken! 🚨🚨🚨")
                    print(f"💀 מלך נהרג: {target_piece.piece_id}")
                    print(f"🔥 זה אמור לגרום לסיום המשחק מיד!")
                    
                # לא מוחקים את הכלי כאן - זה יקרה ב-_handle_arrival כשהכלי יגיע!
        
        # יצירת פקודת תנועה - המערכת הקיימת תטפל בהכל!
        move_cmd = Command(
            timestamp=self.game_time_ms(),
            piece_id=piece.piece_id,
            type="move",
            target=(new_x, new_y),
            params=None
        )
        
        # הוספת הפקודה לתור - State.process_command יטפל במכונת המצבים
        self.user_input_queue.put(move_cmd)
        
        print(f"🎯 שחקן {player_num}: שלח פקודת תנועה ל-{piece.piece_id} ל-({new_x}, {new_y})")
        print(f"PLAYER {player_num}: Sent move command for {piece.piece_id} to ({new_x}, {new_y})")
        # ללא החלפת תור - כל שחקן יכול לזוז מתי שהוא רוצה

    def _is_valid_move(self, piece, new_x, new_y, player_num):
        """Check if move is valid based on piece type and rules."""
        # בדיקה בסיסית - בגבולות הלוח
        if not (0 <= new_x <= 7 and 0 <= new_y <= 7):
            return False
        
        # מיקום נוכחי של הכלי
        current_pos = self._get_piece_position(piece)
        if not current_pos:
            return False
        
        current_x, current_y = current_pos
        
        # חישוב ההפרש
        dx = new_x - current_x
        dy = new_y - current_y
        
        # בדיקה אם יש כלי במיקום המטרה
        target_piece = self._get_piece_at_position(new_x, new_y)
        is_capture = target_piece is not None
        
        # קריאת הנתונים מקובץ התנועות של הכלי
        if hasattr(piece._state, '_moves') and hasattr(piece._state._moves, 'valid_moves'):
            valid_moves = piece._state._moves.valid_moves
            print(f"🔍 בודק תנועה: {piece.piece_id} מ-({current_x},{current_y}) ל-({new_x},{new_y}), הפרש: ({dx},{dy})")
            print(f"🔍 תנועות אפשריות: {valid_moves}")
            
            # בדיקה לכל תנועה אפשרית - רק קואורדינטות, בלי סוגי תנועה
            for move_dx, move_dy, move_type in valid_moves:
                # קבצי התנועות של חילים: צריך להפוך את הכיוון
                # החילים הלבנים והשחורים הפוכים במערכת הקואורדינטות
                if piece.piece_id.startswith('P'):  # חילים - הפך כיוון
                    # הקובץ אומר (0,-1) וזה צריך להישאר (0,-1)
                    actual_dx = move_dx  # השאר כמו שזה
                    actual_dy = move_dy  # השאר כמו שזה
                else:  # כל שאר הכלים - use as is
                    actual_dx = move_dx
                    actual_dy = move_dy
                
                print(f"🔍 בודק תנועה ({move_dx},{move_dy},{move_type}) -> מתורגם: ({actual_dx},{actual_dy})")
                
                # בדיקה אם התנועה תואמת - רק קואורדינטות!
                if dx == actual_dx and dy == actual_dy:
                    print(f"✅ תנועה תואמת! הפרש ({dx},{dy}) = קואורדינטות ({actual_dx},{actual_dy})")
                    print(f"✅ תנועה חוקית!")
                    return True
            
            print(f"❌ לא נמצאה תנועה תואמת")
            return False
        else:
            print(f"❌ אין נתוני תנועות לכלי {piece.piece_id}")
            return False

    # ─── capture resolution ────────────────────────────────────────────────
    def _resolve_collisions(self):
        """Resolve piece collisions and captures."""
        pass  # לממש לוגיקת תפיסות בהמשך

    # ─── board validation & win detection ───────────────────────────────────
    def _is_win(self) -> bool:
        """Check if the game has ended."""
        # בדיקה אם אחד המלכים נהרג
        white_king_alive = False
        black_king_alive = False
        
        print("🔍 בודק תנאי נצחון...")
        for piece in self.pieces:
            print(f"   כלי קיים: {piece.piece_id}")
            if piece.piece_id == "KW0":  # מלך לבן
                white_king_alive = True
                print("   👑 מלך לבן עדיין חי!")
            elif piece.piece_id == "KB0":  # מלך שחור
                black_king_alive = True
                print("   👑 מלך שחור עדיין חי!")
        
        print(f"מלך לבן חי: {white_king_alive}, מלך שחור חי: {black_king_alive}")
        
        # אם אחד המלכים נהרג - המשחק נגמר
        if not white_king_alive or not black_king_alive:
            print("🏆 תנאי נצחון התקיים!")
            return True
            
        print("✅ המשחק ממשיך...")
        return False

    def _announce_win(self):
        """Announce the winner."""
        print("🎺 מכריז על הנצחון!")
        # בדיקה מי ניצח
        white_king_alive = False
        black_king_alive = False
        
        for piece in self.pieces:
            if piece.piece_id == "KW0":  # מלך לבן
                white_king_alive = True
            elif piece.piece_id == "KB0":  # מלך שחור
                black_king_alive = True
        
        if not white_king_alive:
            print("🏆 שחקן 2 (שחור) ניצח! המלך הלבן נהרג!")
            print("🏆 PLAYER 2 (BLACK) WINS! White King was captured!")
            print("🏆 THE WINNER IS PLAYER 2 (BLACK)!")
        elif not black_king_alive:
            print("🏆 שחקן 1 (לבן) ניצח! המלך השחור נהרג!")
            print("🏆 PLAYER 1 (WHITE) WINS! Black King was captured!")
            print("🏆 THE WINNER IS PLAYER 1 (WHITE)!")
        else:
            print("🎮 המשחק נגמר!")
            print("🎮 Game Over!")
