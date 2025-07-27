import inspect
import pathlib
import queue, threading, time, cv2, math
from typing import List, Dict, Tuple, Optional
from img     import Img
from Board import Board
from Command import Command
from Piece import Piece
# Observer imports
from Observer.Publisher import Publisher
from Observer.ScoreTracker import ScoreTracker
from Observer.PieceCaptureEvent import PieceCaptureEvent
from Observer.MoveLogger import MoveLogger
from Observer.MoveMadeEvent import MoveMadeEvent
from Observer.WinnerTracker import WinnerTracker

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
        self.winner_announced = False  # דגל שמונע הכרזת ניצחון חוזרת
        
        # Observer pattern - ניקוד ותיעוד מהלכים
        self.publisher = Publisher()
        self.score_tracker = ScoreTracker()
        self.move_logger = MoveLogger()
        self.winner_tracker = WinnerTracker()
        self.publisher.subscribe(self.score_tracker)
        self.publisher.subscribe(self.move_logger)
        self.publisher.subscribe(self.winner_tracker)

    # ─── helpers ─────────────────────────────────────────────────────────────
    def game_time_ms(self) -> int:
        """Return the current game time in milliseconds."""
        return int(time.monotonic() * 1000)

    def play_sound(self, sound_name):
        """Play a sound file from the Sounds directory."""
        try:
            import pygame
            # אתחול pygame mixer אם עוד לא נעשה
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            sound_path = pathlib.Path(r"C:\Users\01\Desktop\chess\CTD25\Sounds") / f"{sound_name}.mp3"
            
            if sound_path.exists():
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                
                # חכה שהמוזיקה תתחיל להתנגן
                while not pygame.mixer.music.get_busy():
                    pygame.time.wait(10)
                
                # חכה שהמוזיקה תסתיים (רק עבור קול נצחון)
                if sound_name == "win":
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
            
        except ImportError:
            # אם pygame לא מותקן, נסה עם winsound (Windows built-in)
            try:
                import winsound
                sound_path = pathlib.Path(r"C:\Users\01\Desktop\chess\CTD25\Sounds") / f"{sound_name}.mp3"
                if sound_path.exists():
                    # winsound לא תומך ב-MP3, אז נשמיע צליל מערכת
                    winsound.PlaySound("SystemDefault", winsound.SND_ALIAS)
            except ImportError:
                # אם גם winsound לא זמין, פשוט נדפיס הודעה
                print(f"🔊 Playing sound: {sound_name}")
        except Exception as e:
            print(f"Error playing sound: {e}")

    def clone_board(self) -> Board:
        """
        Return a **brand-new** Board wrapping a copy of the background pixels
        so we can paint sprites without touching the pristine board.
        """
        return self.board.clone()

    def start_user_input_thread(self):
        """Start the user input thread for mouse handling."""
        # התור כבר נוצר בקונסטרקטור - אל תדרוס אותו!
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
            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
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
            # בדוק אם יש קומנדים שלא עובדו בתור
            while not self.user_input_queue.empty():
                cmd = self.user_input_queue.get()
        else:
            pass
        cv2.destroyAllWindows()

    # ─── drawing helpers ────────────────────────────────────────────────────
    def _process_input(self, cmd : Command):
        if cmd.type == "arrived":
            self._handle_arrival(cmd)
            return
        
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                piece.on_command(cmd, self.game_time_ms())
                
                # 🏆 בדיקת תנאי נצחון אחרי כל תנועה!
                if self._is_win() and not self.winner_announced:
                    self._announce_win()
                    self.winner_announced = True  # מנע הכרזות נוספות
                    # המשחק יכול להמשיך גם אחרי נצחון
                    # self.game_over = True  # לא מפסיק את המשחק
                    # return  # לא עוצר את המשחק
                break
        else:
            pass

    def _handle_arrival(self, cmd: Command):
        """Handle piece arrival and check for captures."""
        # מצא את הכלי שהגיע ליעד
        arriving_piece = None
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                arriving_piece = piece
                break
        
        if not arriving_piece:
            return
        
        # קבל את המיקום של הכלי שהגיע
        target_pos = arriving_piece._state._physics.cell
        
        # בדוק הכתרת חיילים לפני בדיקת תפיסה
        self._check_pawn_promotion(arriving_piece, target_pos)
        
        # חפש כלי יריב באותו מיקום
        pieces_to_remove = []
        for piece in self.pieces:
            if piece != arriving_piece:  # לא אותו כלי
                piece_pos = piece._state._physics.cell
                if piece_pos == target_pos:
                    # בדוק אם זה כלי יריב
                    arriving_is_white = 'W' in arriving_piece.piece_id
                    piece_is_white = 'W' in piece.piece_id
                    
                    if arriving_is_white != piece_is_white:  # צבעים שונים = יריבים
                        pieces_to_remove.append(piece)
        
        # הסר את הכלים הנתפסים
        for piece in pieces_to_remove:
            if piece in self.pieces:
                self.pieces.remove(piece)
                
                # פרסם אירוע תפיסה
                piece_type = piece.piece_id[0]  # P, R, N, B, Q, K
                captured_by = "white" if 'W' in arriving_piece.piece_id else "black"
                capture_event = PieceCaptureEvent(piece_type, captured_by)
                self.publisher.notify(capture_event)
                
                # השמע קול תפיסה
                self.play_sound("keel")
        
        # בדוק תנאי נצחון אחרי תפיסה
        if pieces_to_remove:
            if self._is_win() and not self.winner_announced:
                self._announce_win()
                self.winner_announced = True  # מנע הכרזות נוספות
                # המשחק יכול להמשיך גם אחרי נצחון
                # self.game_over = True  # לא מפסיק את המשחק

    def _check_pawn_promotion(self, piece, target_pos):
        """Check if a pawn should be promoted to queen."""
        # בדוק אם זה חייל
        if not piece.piece_id.startswith('P'):
            return  # לא חייל - אין הכתרה
            
        col, row = target_pos  # target_pos הוא (x, y) = (col, row)
        is_white_pawn = 'W' in piece.piece_id
        is_black_pawn = 'B' in piece.piece_id
        
        # בדוק אם החייל הגיע לשורה המתאימה להכתרה
        should_promote = False
        new_piece_type = None
        
        if is_white_pawn and row == 0:  # חייל לבן הגיע לשורה 0
            should_promote = True
            new_piece_type = "QW"
        elif is_black_pawn and row == 7:  # חייל שחור הגיע לשורה 7
            should_promote = True
            new_piece_type = "QB"
            
        if should_promote:
            self._promote_pawn_to_queen(piece, new_piece_type, target_pos)

    def _promote_pawn_to_queen(self, pawn, queen_type, position):
        """Replace a pawn with a queen at the given position."""
        # צור מלכה חדשה
        pieces_root = pathlib.Path(r"c:\Users\01\Desktop\chess\CTD25\pieces")
        from PieceFactory import PieceFactory
        factory = PieceFactory(self.board, pieces_root)
        
        # יצירת ID ייחודי למלכה החדשה
        existing_queens = [p for p in self.pieces if p.piece_id.startswith(queen_type)]
        queen_id = f"{queen_type}{len(existing_queens)}"
        
        # צור מלכה חדשה במיקום הנדרש
        new_queen = factory.create_piece(queen_type, position, self.user_input_queue)
        new_queen.piece_id = queen_id
        new_queen._state._physics.piece_id = queen_id
        
        # הסר את החייל הישן והוסף את המלכה החדשה
        if pawn in self.pieces:
            self.pieces.remove(pawn)
            
        self.pieces.append(new_queen)

    def _draw(self):
        """Draw the current game state."""
        # צור עותק נקי של הלוח לכל פריים
        display_board = self.clone_board()
        
        # ציור כל הכלים על העותק
        now = self.game_time_ms()
        for p in self.pieces:
            p.draw_on_board(display_board, now)
        
        # הצגה עם רקע ומידע סמנים
        if hasattr(display_board, "img"):
            cursors_info = {
                'player1_cursor': self.cursor_pos_player1,
                'player2_cursor': self.cursor_pos_player2,
                'player1_selected': self._get_piece_position(self.selected_piece_player1) if self.selected_piece_player1 else None,
                'player2_selected': self._get_piece_position(self.selected_piece_player2) if self.selected_piece_player2 else None
            }
            
            # הוסף מידע ניקוד
            score_info = {
                'white_score': self.score_tracker.get_score("white"),
                'black_score': self.score_tracker.get_score("black")
            }
            
            # הוסף מידע מהלכים
            moves_info = {
                'white_moves': self.move_logger.get_moves("white"),
                'black_moves': self.move_logger.get_moves("black")
            }
            
            # ציור טקסט ניצחון על הלוח אם יש מנצח - לפני הצגה!
            winner_text = self.winner_tracker.get_winner_text()
            if winner_text:
                self._draw_winner_text_on_board(display_board, winner_text)
            
            display_board.img.display_with_background("Chess Game", 
                                                     cursors_info=cursors_info, 
                                                     score_info=score_info,
                                                     moves_info=moves_info)

    def _draw_cursors(self, board):
        """Draw player cursors on the board."""
        if hasattr(board, 'img') and hasattr(board.img, 'img'):
            img = board.img.img
            
            # חישוב גודל משבצת
            board_height, board_width = img.shape[:2]
            cell_width = board_width // 8
            cell_height = board_height // 8
            
            # ציור סמן שחקן 1 (אדום זוהר) - מקשי מספרים
            x1, y1 = self.cursor_pos_player1
            top_left_1 = (x1 * cell_width, y1 * cell_height)
            bottom_right_1 = ((x1 + 1) * cell_width - 1, (y1 + 1) * cell_height - 1)
            cv2.rectangle(img, top_left_1, bottom_right_1, (0, 0, 255), 8)  # אדום זוהר BGR עבה מאוד
            
            # ציור סמן שחקן 2 (ירוק זוהר) - WASD
            x2, y2 = self.cursor_pos_player2
            top_left_2 = (x2 * cell_width, y2 * cell_height)
            bottom_right_2 = ((x2 + 1) * cell_width - 1, (y2 + 1) * cell_height - 1)
            cv2.rectangle(img, top_left_2, bottom_right_2, (0, 255, 0), 8)  # ירוק זוהר BGR עבה מאוד
            
            # סימון כלי נבחר - צריך להיות על הכלי עצמו, לא על הסמן
            if self.selected_piece_player1:
                # מצא את מיקום הכלי הנבחר של שחקן 1
                piece_pos = self._get_piece_position(self.selected_piece_player1)
                if piece_pos:
                    px, py = piece_pos
                    piece_top_left = (px * cell_width, py * cell_height)
                    piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
                    cv2.rectangle(img, piece_top_left, piece_bottom_right, (0, 255, 255), 4)  # צהוב זוהר עבה
            
            if self.selected_piece_player2:
                # מצא את מיקום הכלי הנבחר של שחקן 2
                piece_pos = self._get_piece_position(self.selected_piece_player2)
                if piece_pos:
                    px, py = piece_pos
                    piece_top_left = (px * cell_width, py * cell_height)
                    piece_bottom_right = ((px + 1) * cell_width - 1, (py + 1) * cell_height - 1)
                    cv2.rectangle(img, piece_top_left, piece_bottom_right, (255, 0, 255), 4)  # ורוד/מגנטה זוהר עבה

    def _draw_winner_text_on_board(self, board, winner_text):
        """Draw winner text overlay on the board."""
        if not hasattr(board, 'img') or not hasattr(board.img, 'img'):
            return
            
        img = board.img.img
        height, width = img.shape[:2]
        
        # יצירת רקע שקוף למסך הניצחון
        overlay = img.copy()
        
        # רקע שחור חצי שקוף למרכז הלוח
        center_x, center_y = width // 2, height // 2
        box_width, box_height = 600, 150
        
        # ציור רקע שחור לטקסט
        cv2.rectangle(overlay, 
                     (center_x - box_width//2, center_y - box_height//2),
                     (center_x + box_width//2, center_y + box_height//2),
                     (0, 0, 0), -1)
        
        # מיזוג הרקע החצי שקוף עם התמונה המקורית
        alpha = 0.8  # שקיפות - ככל שהמספר גבוה יותר, כך הרקע פחות שקוף
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        
        # הגדרות הטקסט
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.5
        color = (0, 255, 255)  # צהוב זוהר
        thickness = 3
        
        # חישוב מיקום הטקסט למרכז
        text_size = cv2.getTextSize(winner_text, font, font_scale, thickness)[0]
        text_x = center_x - text_size[0] // 2
        text_y = center_y + text_size[1] // 2
        
        # ציור הטקסט עם קו חיצוני שחור לבולטות
        cv2.putText(img, winner_text, (text_x + 2, text_y + 2), font, font_scale, (0, 0, 0), thickness + 2)
        cv2.putText(img, winner_text, (text_x, text_y), font, font_scale, color, thickness)
        
        # הוספת טקסט נוסף למטה
        sub_text = "Game continues - Press ESC to exit"
        sub_font_scale = 0.8
        sub_thickness = 2
        sub_color = (255, 255, 255)  # לבן
        
        sub_text_size = cv2.getTextSize(sub_text, font, sub_font_scale, sub_thickness)[0]
        sub_text_x = center_x - sub_text_size[0] // 2
        sub_text_y = text_y + 50
        
        cv2.putText(img, sub_text, (sub_text_x + 1, sub_text_y + 1), font, sub_font_scale, (0, 0, 0), sub_thickness + 1)
        cv2.putText(img, sub_text, (sub_text_x, sub_text_y), font, sub_font_scale, sub_color, sub_thickness)

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
            char = detected_hebrew
        
        # W key (UP) - English W או עברית ו
        if (key in [119, 87] or char == 'w' or 
            key in [1493, 215, 246, 1500] or  # Hebrew ו (vav)
            detected_hebrew == 'w'):
            self._move_cursor_player2(0, -1)
            wasd_detected = True
        # S key (DOWN) - English S או עברית ד
        elif (key in [115, 83] or char == 's' or 
              key in [1491, 212, 213, 1504] or  # Hebrew ד (dalet)
              detected_hebrew == 's'):
            self._move_cursor_player2(0, 1)
            wasd_detected = True
        # A key (LEFT) - English A או עברית ש
        elif (key in [97, 65] or char == 'a' or 
              key in [1513, 249, 251, 1506] or  # Hebrew ש (shin)
              detected_hebrew == 'a'):
            self._move_cursor_player2(-1, 0)
            wasd_detected = True
        # D key (RIGHT) - English D או עברית כ
        elif (key in [100, 68] or char == 'd' or 
              key in [1499, 235, 237, 1507] or  # Hebrew כ (kaf)
              detected_hebrew == 'd'):
            self._move_cursor_player2(1, 0)
            wasd_detected = True
        elif key == 32 or char == ' ':  # Space
            self._select_piece_player2()
            wasd_detected = True
        
        # מקשי חירום נוספים לשחקן 2 (אם WASD לא עובד)
        elif key in [255, 254, 253, 252]:  # מקשים מיוחדים כחלופה
            emergency_map = {255: 'w', 254: 's', 253: 'a', 252: 'd'}
            direction = emergency_map.get(key)
            if direction:
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
            self._move_cursor_player1(0, -1)
        elif key == 50 or char == '2':  # 2 key
            self._move_cursor_player1(0, 1)
        elif key == 52 or char == '4':  # 4 key
            self._move_cursor_player1(-1, 0)
        elif key == 54 or char == '6':  # 6 key
            self._move_cursor_player1(1, 0)
        elif key == 53 or key == 48 or char == '5' or char == '0':  # 5 or 0 key
            self._select_piece_player1()
        elif key in [13, 10, 39, 226, 249]:  # Enter - multiple codes for different systems
            self._select_piece_player1()
        
        return False  # Don't exit

    def _move_cursor_player1(self, dx, dy):
        """Move player 1 cursor (numeric keys) - כלים לבנים."""
        old_pos = self.cursor_pos_player1.copy()
        new_x = max(0, min(7, self.cursor_pos_player1[0] + dx))
        new_y = max(0, min(7, self.cursor_pos_player1[1] + dy))
        self.cursor_pos_player1 = [new_x, new_y]

    def _move_cursor_player2(self, dx, dy):
        """Move player 2 cursor (WASD) - כלים שחורים."""
        old_pos = self.cursor_pos_player2.copy()
        new_x = max(0, min(7, self.cursor_pos_player2[0] + dx))
        new_y = max(0, min(7, self.cursor_pos_player2[1] + dy))
        self.cursor_pos_player2 = [new_x, new_y]

    def _select_piece_player1(self):
        """Handle piece selection for player 1 (Enter key)."""
        x, y = self.cursor_pos_player1
        
        if self.selected_piece_player1 is None:
            # בחירת כלי חדש
            piece = self._find_piece_at_position(x, y)
            if piece and self._is_player_piece(piece, 1):
                self.selected_piece_player1 = piece
        else:
            # בדיקה אם מנסים להזיז לאותו מיקום (אנימציית קפיצה במקום)
            current_pos = self._get_piece_position(self.selected_piece_player1)
            if current_pos == (x, y):
                # בצע אנימציית קפיצה לאותו מיקום
                jump_cmd = Command(
                    timestamp=self.game_time_ms(),
                    piece_id=self.selected_piece_player1.piece_id,
                    type="jump",
                    target=current_pos,  # קפיצה לאותו מיקום
                    params=None
                )
                self.user_input_queue.put(jump_cmd)
                self.selected_piece_player1 = None
                return
            
            # הזזת הכלי הנבחר למיקום חדש
            self._move_piece(self.selected_piece_player1, x, y, 1)
            self.selected_piece_player1 = None

    def _select_piece_player2(self):
        """Handle piece selection for player 2 (Space key)."""
        x, y = self.cursor_pos_player2
        
        if self.selected_piece_player2 is None:
            # בחירת כלי חדש
            piece = self._find_piece_at_position(x, y)
            if piece and self._is_player_piece(piece, 2):
                self.selected_piece_player2 = piece
        else:
            # בדיקה אם מנסים להזיז לאותו מיקום (אנימציית קפיצה במקום)
            current_pos = self._get_piece_position(self.selected_piece_player2)
            if current_pos == (x, y):
                # בצע אנימציית קפיצה לאותו מיקום
                jump_cmd = Command(
                    timestamp=self.game_time_ms(),
                    piece_id=self.selected_piece_player2.piece_id,
                    type="jump",
                    target=current_pos,  # קפיצה לאותו מיקום
                    params=None
                )
                self.user_input_queue.put(jump_cmd)
                self.selected_piece_player2 = None
                return
            
            # הזזת הכלי הנבחר למיקום חדש
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
        for piece in self.pieces:
            # בדיקה אם לכלי יש _state עם _physics עם cell
            if hasattr(piece, '_state') and hasattr(piece._state, '_physics'):
                physics = piece._state._physics
                if hasattr(physics, 'cell'):
                    if physics.cell == (x, y):
                        return piece
            
            # פלטות נוספות - בדיקת מיקום ישיר
            elif hasattr(piece, 'x') and hasattr(piece, 'y'):
                if piece.x == x and piece.y == y:
                    return piece
            
            elif hasattr(piece, 'board_position'):
                if piece.board_position == (x, y):
                    return piece
        
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
            return
        
        # מיקום נוכחי של הכלי
        current_pos = self._get_piece_position(piece)
        if not current_pos:
            return
        
        current_x, current_y = current_pos
        
        # בדיקת נתיב - האם יש כלים בדרך (רק אחרי שהתנועה תקינה!)
        blocking_position = self._check_path(current_x, current_y, new_x, new_y, piece.piece_id)
        
        # אם יש כלי חוסם בדרך, עדכן את מיקום היעד למיקום של הכלי החוסם
        final_x, final_y = new_x, new_y
        if blocking_position:
            final_x, final_y = blocking_position
        
        # בדיקה אם יש כלי במיקום המטרה הסופי
        target_piece = self._get_piece_at_position(final_x, final_y)
        if target_piece:
            # בדוק אם זה כלי של האויב (אפשר לתפוס)
            if self._is_player_piece(target_piece, player_num):
                return
        
        # יצירת פקודת תנועה - כל הכלים יכולים לזוז בתנועה חלקה
        command_type = "move"
        
        # המרת קואורדינטות לפורמט שח
        start_notation = f"{chr(ord('a') + current_x)}{8 - current_y}"
        end_notation = f"{chr(ord('a') + final_x)}{8 - final_y}"
        
        move_cmd = Command(
            timestamp=self.game_time_ms(),
            piece_id=piece.piece_id,
            type=command_type,
            target=(final_x, final_y),  # שימוש במיקום המעודכן
            params=[start_notation, end_notation]  # מיקומי התחלה וסיום
        )
        
        # פרסם אירוע מהלך מיד
        piece_type = piece.piece_id[0]  # P, R, N, B, Q, K
        player_color = "white" if 'W' in piece.piece_id else "black"
        
        from datetime import datetime
        move_event = MoveMadeEvent(
            piece_type=piece_type,
            start_position=start_notation,
            end_position=end_notation,
            player_color=player_color,
            timestamp=datetime.now()
        )
        self.publisher.notify(move_event)
        
        # השמע קול מהלך
        self.play_sound("move")
        
        # הוספת הפקודה לתור - State.process_command יטפל במכונת המצבים
        self.user_input_queue.put(move_cmd)

    def _check_path(self, start_x, start_y, end_x, end_y, piece_type):
        """Check if path is clear and return first blocking piece position if any."""
        # סוסים יכולים לקפוץ מעל כלים
        if piece_type.startswith('N'):  # Knight - no path checking
            return None
        
        dx = end_x - start_x
        dy = end_y - start_y
        
        # מלכים יכולים לזוז משבצת אחת בכל כיוון - אין צורך בבדיקת נתיב
        if piece_type.startswith('K') and abs(dx) <= 1 and abs(dy) <= 1:
            return None
        
        # חישוב כיוון התנועה
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        
        # בדיקת נתיב - בלי לכלול את נקודות ההתחלה והסיום
        current_x = start_x + step_x
        current_y = start_y + step_y
        
        while current_x != end_x or current_y != end_y:
            # בדיקה אם יש כלי במשבצת הנוכחית
            blocking_piece = self._get_piece_at_position(current_x, current_y)
            if blocking_piece:
                return (current_x, current_y)  # מחזיר את מיקום הכלי החוסם
            
            # מעבר למשבצת הבאה
            current_x += step_x
            current_y += step_y
        
        return None  # נתיב פנוי

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
        
        # קריאת הנתונים מקובץ התנועות של הכלי - קודם נבדוק אם התנועה חוקית
        if hasattr(piece._state, '_moves') and hasattr(piece._state._moves, 'valid_moves'):
            valid_moves = piece._state._moves.valid_moves
            
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
                
                # בדיקה אם התנועה תואמת - רק קואורדינטות!
                if dx == actual_dx and dy == actual_dy:
                    # כעת, אחרי שאנחנו יודעים שהתנועה חוקית לפי הקבצים, נבדוק נתיב
                    blocking_position = self._check_path(current_x, current_y, new_x, new_y, piece.piece_id)
                    
                    # אם יש כלי חוסם בדרך ואנחנו לא מנסים לזוז למיקום שלו
                    if blocking_position and blocking_position != (new_x, new_y):
                        return False
                    
                    return True
            
            return False
        else:
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
        
        for piece in self.pieces:
            if piece.piece_id == "KW0":  # מלך לבן
                white_king_alive = True
            elif piece.piece_id == "KB0":  # מלך שחור
                black_king_alive = True
        
        # אם אחד המלכים נהרג - המשחק נגמר
        return not white_king_alive or not black_king_alive

    def _announce_win(self):
        """Announce the winner."""
        
        # השמע קול נצחון
        self.play_sound("win")
        
        # בדיקה מי ניצח
        white_king_alive = False
        black_king_alive = False
        
        for piece in self.pieces:
            if piece.piece_id == "KW0":  # מלך לבן
                white_king_alive = True
            elif piece.piece_id == "KB0":  # מלך שחור
                black_king_alive = True
        
        if not white_king_alive:
            winner_text = "PLAYER 2 (BLACK) WINS!"
            self.winner_tracker.set_winner_text(winner_text)
            print("🏆 שחקן 2 (שחור) ניצח! המלך הלבן נהרג!")
            print("🏆 PLAYER 2 (BLACK) WINS! White King was captured!")
            print("🎮 המשחק ממשיך...")
        elif not black_king_alive:
            winner_text = "PLAYER 1 (WHITE) WINS!"
            self.winner_tracker.set_winner_text(winner_text)
            print("🏆 שחקן 1 (לבן) ניצח! המלך השחור נהרג!")
            print("🏆 PLAYER 1 (WHITE) WINS! Black King was captured!")
            print("🎮 המשחק ממשיך...")
        else:
            winner_text = "GAME OVER!"
            self.winner_tracker.set_winner_text(winner_text)
            print("🎮 המשחק נגמר!")
