import pathlib, queue, time, cv2, logging
from typing import List
from img import Img
from Board import Board
from Command import Command
from Piece import Piece
from Observer.Publisher import Publisher
from Observer.ScoreTracker import ScoreTracker
from Observer.PieceCaptureEvent import PieceCaptureEvent
from Observer.MoveLogger import MoveLogger
from Observer.MoveMadeEvent import MoveMadeEvent
from Observer.WinnerTracker import WinnerTracker
from Observer.GameOverEvent import GameOverEvent
from Observer.EventType import EventType

# הגדרת לוגגר פשוטה
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InvalidBoard(Exception): ...

class Game:
    def __init__(self, pieces: List[Piece], board: Board):
        self.pieces = pieces
        self.board = board
        self.user_input_queue = queue.Queue()
        self.selected_piece_player1 = None
        self.selected_piece_player2 = None
        self.cursor_pos_player1 = [0, 7]
        self.cursor_pos_player2 = [0, 0]
        self.game_over = False
        self.winner_announced = False
        self.jumping_pieces = set()  # כלים שנמצאים בקפיצה
        
        # טעינת שמות המשתמשים
        self.player_names = self._load_player_names()
        
        observers = [ScoreTracker(), MoveLogger(), WinnerTracker()]
        self.score_tracker, self.move_logger, self.winner_tracker = observers
        self.publisher = Publisher()
        for observer in observers:
            self.publisher.subscribe(observer)

    def _load_player_names(self):
        """טוען שמות משתמשים מקובץ Names.json"""
        try:
            import json
            names_path = pathlib.Path(__file__).parent / "Names.json"
            if names_path.exists():
                with open(names_path, 'r', encoding='utf-8') as f:
                    names = json.load(f)
                    player_names = {
                        'player1': names.get('player1', 'PLAYER 1'),
                        'player2': names.get('player2', 'PLAYER 2')
                    }
                    logger.info(f"טעינת שמות שחקנים: {player_names}")
                    return player_names
            else:
                logger.warning(f"קובץ Names.json לא נמצא בנתיב: {names_path}")
        except Exception as e:
            logger.error(f"שגיאה בטעינת שמות משתמשים: {e}")
        
        default_names = {'player1': 'PLAYER 1', 'player2': 'PLAYER 2'}
        logger.info(f"שימוש בשמות ברירת מחדל: {default_names}")
        return default_names

    def game_time_ms(self) -> int:
        return int(time.monotonic() * 1000)

    def play_sound(self, sound_name):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                logger.debug("pygame mixer אותחל")
            
            sound_path = pathlib.Path(__file__).parent / "Sounds" / f"{sound_name}.mp3"
            if sound_path.exists():
                logger.debug(f"משמיע צליל: {sound_name}")
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                while not pygame.mixer.music.get_busy():
                    pygame.time.wait(10)
                if sound_name == "win":
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
            else:
                logger.warning(f"קובץ צליל לא נמצא: {sound_path}")
        except Exception as e:
            logger.error(f"שגיאה בהשמעת צליל '{sound_name}': {e}")
            pass

    def clone_board(self) -> Board:
        return self.board.clone()

    def run(self):
        logger.info("התחלת משחק שחמט")
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)
        
        logger.info(f"משחק מתחיל עם {len(self.pieces)} כלים")

        while not self.game_over:
            now = self.game_time_ms()
            for p in self.pieces:
                p.update(now)

            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)
                if self.game_over:
                    break

            self._draw()
            if not self._show():
                break

            self._resolve_collisions()
            time.sleep(1/60.0)

        if self.game_over:
            while not self.user_input_queue.empty():
                self.user_input_queue.get()
        logger.info("המשחק הסתיים")
        cv2.destroyAllWindows()

    def _process_input(self, cmd : Command):
        logger.debug(f"מעבד פקודה: {cmd.type} עבור כלי {cmd.piece_id}")
        
        if cmd.type == "arrived":
            self._handle_arrival(cmd)
            return
        elif cmd.type == "jump":
            # כשכלי מתחיל קפיצה, מוסיפים אותו לרשימת הקופצים
            self.jumping_pieces.add(cmd.piece_id)
            logger.debug(f"כלי {cmd.piece_id} מתחיל קפיצה")
        
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                piece.on_command(cmd, self.game_time_ms())
                if self._is_win() and not self.winner_announced:
                    logger.info("זוהה ניצחון במשחק")
                    self._announce_win()
                    self.winner_announced = True
                break

    def _handle_arrival(self, cmd: Command):
        arriving_piece = next((p for p in self.pieces if p.piece_id == cmd.piece_id), None)
        if not arriving_piece:
            logger.warning(f"כלי לא נמצא עבור פקודת הגעה: {cmd.piece_id}")
            return
        
        # אם הכלי היה בקפיצה, מוציאים אותו מהרשימה
        if cmd.piece_id in self.jumping_pieces:
            self.jumping_pieces.remove(cmd.piece_id)
            logger.debug(f"כלי {cmd.piece_id} סיים קפיצה")
        
        # תמיכה בשני הסוגים: State (physics) ו-State הישן (_physics)
        physics = getattr(arriving_piece._state, 'physics', None) or getattr(arriving_piece._state, '_physics', None)
        target_pos = physics.cell if physics else None
        if not target_pos:
            logger.warning(f"לא ניתן לקבוע מיקום יעד עבור כלי {cmd.piece_id}")
            return
        
        logger.debug(f"כלי {cmd.piece_id} הגיע למיקום {target_pos}")
            
        self._check_pawn_promotion(arriving_piece, target_pos)
        
        pieces_to_remove = []
        for p in self.pieces:
            if p != arriving_piece:
                # אם הכלי נמצא בקפיצה, הוא לא נחשב "נמצא" במשבצת
                if p.piece_id in self.jumping_pieces:
                    continue
                    
                p_physics = getattr(p._state, 'physics', None) or getattr(p._state, '_physics', None)
                if (p_physics and p_physics.cell == target_pos and 
                    ('W' in arriving_piece.piece_id) != ('W' in p.piece_id)):
                    pieces_to_remove.append(p)
        
        for piece in pieces_to_remove:
            self.pieces.remove(piece)
            piece_type = piece.piece_id[0]
            captured_by = "white" if 'W' in arriving_piece.piece_id else "black"
            logger.info(f"כלי {piece.piece_id} נתפס על ידי {arriving_piece.piece_id}")
            self.publisher.notify(PieceCaptureEvent(piece_type, captured_by))
            self.play_sound("keel")
        
        if pieces_to_remove and self._is_win() and not self.winner_announced:
            logger.info("ניצחון לאחר תפיסת כלי")
            self._announce_win()
            self.winner_announced = True

    def _check_pawn_promotion(self, piece, target_pos):
        if not piece.piece_id.startswith('P'):
            return
            
        col, row = target_pos
        promotion_rules = {('W', 0): "QW", ('B', 7): "QB"}
        color = 'W' if 'W' in piece.piece_id else 'B'
        
        if (color, row) in promotion_rules:
            logger.info(f"חיל {piece.piece_id} מתקדם למלכה במיקום {target_pos}")
            self._promote_pawn_to_queen(piece, promotion_rules[(color, row)], target_pos)

    def _promote_pawn_to_queen(self, pawn, queen_type, position):
        from PieceFactory import PieceFactory
        factory = PieceFactory(self.board, pathlib.Path(__file__).parent.parent / "pieces")
        
        existing_queens = [p for p in self.pieces if p.piece_id.startswith(queen_type)]
        queen_id = f"{queen_type}{len(existing_queens)}"
        
        logger.info(f"יוצר מלכה חדשה: {queen_id} במיקום {position}")
        
        new_queen = factory.create_piece(queen_type, position, self.user_input_queue)
        new_queen.piece_id = queen_id
        
        # תמיכה בשני הסוגים: State (physics) ו-State הישן (_physics)
        physics = getattr(new_queen._state, 'physics', None) or getattr(new_queen._state, '_physics', None)
        if physics:
            physics.piece_id = queen_id
        
        self.pieces.remove(pawn)
        self.pieces.append(new_queen)
        logger.info(f"חיל {pawn.piece_id} הוחלף במלכה {queen_id}")

    def _draw(self):
        display_board = self.clone_board()
        now = self.game_time_ms()
        for p in self.pieces:
            p.draw_on_board(display_board, now)
        
        if hasattr(display_board, "img"):
            info = {
                'cursors_info': {
                    'player1_cursor': self.cursor_pos_player1,
                    'player2_cursor': self.cursor_pos_player2,
                    'player1_selected': self._get_piece_position(self.selected_piece_player1),
                    'player2_selected': self._get_piece_position(self.selected_piece_player2)
                },
                'score_info': {
                    'white_score': self.score_tracker.get_score("white"),
                    'black_score': self.score_tracker.get_score("black")
                },
                'moves_info': {
                    'white_moves': self.move_logger.get_moves("white"),
                    'black_moves': self.move_logger.get_moves("black")
                },
                'player_names': self.player_names
            }
            
            winner_text = self.winner_tracker.get_winner_text()
            if winner_text:
                winner_enum = self.winner_tracker.get_winner()
                logger.info(f"Winner enum for image: {winner_enum}")
                self._draw_winner_image_on_board(display_board, winner_text, winner_enum)
            
            display_board.img.display_with_background("Chess Game", **info)

    def _draw_winner_image_on_board(self, board, winner_text, winner_enum):
        if not (hasattr(board, 'img') and hasattr(board.img, 'img')):
            return
        img = board.img.img
        h, w = img.shape[:2]
        center_x, center_y = w // 2, h // 2

        # קבע איזו תמונה להציג לפי הערך Enum
        winner_image_path = None
        winner_value = getattr(winner_enum, 'value', None)
        if winner_value == "game_over_black":
            winner_image_path = pathlib.Path(__file__).parent.parent / "Photos" / "blackWin.png"
        elif winner_value == "game_over_white":
            winner_image_path = pathlib.Path(__file__).parent.parent / "Photos" / "whiteWin.png"

        if winner_image_path and winner_image_path.exists():
            try:
                winner_img = cv2.imread(str(winner_image_path), cv2.IMREAD_UNCHANGED)
                if winner_img is not None:
                    target_width = min(400, w // 2)
                    target_height = min(300, h // 2)
                    winner_img_resized = cv2.resize(winner_img, (target_width, target_height))
                    # טיפול בערוצים: המרה ל-RGBA אם צריך
                    if img.shape[2] == 4 and winner_img_resized.shape[2] == 3:
                        winner_img_resized = cv2.cvtColor(winner_img_resized, cv2.COLOR_BGR2BGRA)
                    elif img.shape[2] == 3 and winner_img_resized.shape[2] == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                    start_x = center_x - target_width // 2
                    start_y = center_y - target_height // 2
                    end_x = start_x + target_width
                    end_y = start_y + target_height
                    start_x = max(0, start_x)
                    start_y = max(0, start_y)
                    end_x = min(w, end_x)
                    end_y = min(h, end_y)
                    img[start_y:end_y, start_x:end_x] = winner_img_resized[:end_y-start_y, :end_x-start_x]
                    return
            except Exception as e:
                logger.error(f"שגיאה בטעינת תמונת הניצחון: {e}")

        # אם לא הצלחנו להציג תמונה, נחזור לטקסט פשוט
        overlay = img.copy()
        cv2.rectangle(overlay, (center_x - 300, center_y - 75), (center_x + 300, center_y + 75), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        font = cv2.FONT_HERSHEY_SIMPLEX
        simple_text = "WINNER!" if winner_enum in (EventType.GAME_OVER_BLACK, EventType.GAME_OVER_WHITE) else "GAME OVER!"
        text_size = cv2.getTextSize(simple_text, font, 1.5, 3)[0]
        text_x, text_y = center_x - text_size[0] // 2, center_y + text_size[1] // 2
        cv2.putText(img, simple_text, (text_x + 2, text_y + 2), font, 1.5, (0, 0, 0), 5)
        cv2.putText(img, simple_text, (text_x, text_y), font, 1.5, (0, 255, 255), 3)

    def _show(self) -> bool:
        cv2.setWindowProperty("Chess Game", cv2.WND_PROP_TOPMOST, 1)
        key = cv2.waitKey(30) & 0xFF
        return not (key != 255 and key != -1 and self._handle_keyboard_input(key))

    def _handle_keyboard_input(self, key):
        if key in [27, ord('q')]:
            self.game_over = True
            return True
        
        char = chr(key).lower() if 32 <= key <= 126 else None
        hebrew_map = {1493: 'w', 215: 'w', 1513: 'a', 249: 'a', 1491: 's', 212: 's', 1499: 'd', 235: 'd'}
        char = hebrew_map.get(key, char)
        
        # Player 2 - WASD
        moves_p2 = {('w', 119, 87): (0, -1), ('s', 115, 83): (0, 1), ('a', 97, 65): (-1, 0), ('d', 100, 68): (1, 0)}
        for keys, move in moves_p2.items():
            if key in keys[1:] or char == keys[0]:
                self._move_cursor_player2(*move)
                return False
        
        if key == 32:
            self._select_piece_player2()
        
        # Player 1 - Numeric
        moves_p1 = {56: (0, -1), 50: (0, 1), 52: (-1, 0), 54: (1, 0)}
        if key in moves_p1:
            self._move_cursor_player1(*moves_p1[key])
        elif key in [53, 48, 13, 10]:
            self._select_piece_player1()
        
        return False

    def _move_cursor_player1(self, dx, dy):
        self.cursor_pos_player1 = [max(0, min(7, self.cursor_pos_player1[0] + dx)), 
                                  max(0, min(7, self.cursor_pos_player1[1] + dy))]

    def _move_cursor_player2(self, dx, dy):
        self.cursor_pos_player2 = [max(0, min(7, self.cursor_pos_player2[0] + dx)), 
                                  max(0, min(7, self.cursor_pos_player2[1] + dy))]

    def _select_piece_player1(self):
        self._select_piece_for_player(1, self.cursor_pos_player1, 'selected_piece_player1')

    def _select_piece_player2(self):
        self._select_piece_for_player(2, self.cursor_pos_player2, 'selected_piece_player2')

    def _select_piece_for_player(self, player_num, cursor_pos, selected_attr):
        x, y = cursor_pos
        selected_piece = getattr(self, selected_attr)
        
        if selected_piece is None:
            piece = self._find_piece_at_position(x, y)
            if piece and self._is_player_piece(piece, player_num):
                # בדיקה אם הכלי במנוחה לפני בחירה
                if hasattr(piece, '_state') and hasattr(piece._state, 'can_transition'):
                    if not piece._state.can_transition(self.game_time_ms()):
                        logger.debug(f"כלי {piece.piece_id} במנוחה - לא ניתן לבחור")
                        self.play_sound("fail")  # כלי במנוחה
                        return
                logger.debug(f"שחקן {player_num} בחר כלי {piece.piece_id} במיקום {cursor_pos}")
                setattr(self, selected_attr, piece)
            elif piece:
                # מנסים לבחור כלי של השחקן השני
                logger.debug(f"שחקן {player_num} מנסה לבחור כלי של יריב: {piece.piece_id}")
                self.play_sound("fail")
        else:
            current_pos = self._get_piece_position(selected_piece)
            if current_pos == (x, y):
                # בדיקה אם הכלי במנוחה לפני קפיצה
                if hasattr(selected_piece, '_state') and hasattr(selected_piece._state, 'can_transition'):
                    if not selected_piece._state.can_transition(self.game_time_ms()):
                        logger.debug(f"כלי {selected_piece.piece_id} במנוחה - לא ניתן לקפוץ")
                        self.play_sound("fail")  # כלי במנוחה
                        setattr(self, selected_attr, None)
                        return
                logger.debug(f"כלי {selected_piece.piece_id} מבצע קפיצה במקום")
                self.user_input_queue.put(Command(
                    timestamp=self.game_time_ms(),
                    piece_id=selected_piece.piece_id,
                    type="jump",
                    target=current_pos,
                    params=None
                ))
            else:
                # בדיקה אם הכלי במנוחה לפני תנועה
                if hasattr(selected_piece, '_state') and hasattr(selected_piece._state, 'can_transition'):
                    if not selected_piece._state.can_transition(self.game_time_ms()):
                        logger.debug(f"כלי {selected_piece.piece_id} במנוחה - לא ניתן לזוז")
                        self.play_sound("fail")  # כלי במנוחה
                        setattr(self, selected_attr, None)
                        return
                logger.debug(f"מנסה להזיז כלי {selected_piece.piece_id} מ-{current_pos} ל-{cursor_pos}")
                self._move_piece(selected_piece, x, y, player_num)
            setattr(self, selected_attr, None)

    def _get_piece_position(self, piece):
        if not piece:
            return None
        # תמיכה בשני הסוגים: State (physics) ו-State הישן (_physics)
        if hasattr(piece, '_state'):
            physics = getattr(piece._state, 'physics', None) or getattr(piece._state, '_physics', None)
            if physics and hasattr(physics, 'cell'):
                return physics.cell
        return getattr(piece, 'board_position', None) or (getattr(piece, 'x', None), getattr(piece, 'y', None))

    def _find_piece_at_position(self, x, y):
        return next((p for p in self.pieces if self._get_piece_position(p) == (x, y)), None)

    def _is_player_piece(self, piece, player_num):
        return ('W' in piece.piece_id) == (player_num == 1)

    def _move_piece(self, piece, new_x, new_y, player_num):
        if not self._is_valid_move(piece, new_x, new_y, player_num):
            logger.debug(f"מהלך לא חוקי: {piece.piece_id} ל-({new_x}, {new_y})")
            self.play_sound("fail")  # מהלך לא חוקי
            return
        
        current_pos = self._get_piece_position(piece)
        if not current_pos:
            logger.warning(f"לא ניתן למצוא מיקום נוכחי עבור כלי {piece.piece_id}")
            self.play_sound("fail")  # לא ניתן למצוא מיקום הכלי
            return
        
        current_x, current_y = current_pos
        blocking_position = self._check_path(current_x, current_y, new_x, new_y, piece.piece_id)
        final_x, final_y = blocking_position if blocking_position else (new_x, new_y)
        
        target_piece = self._find_piece_at_position(final_x, final_y)
        if target_piece and self._is_player_piece(target_piece, player_num):
            logger.debug(f"מנסה לתקוף כלי של אותו שחקן: {piece.piece_id} -> {target_piece.piece_id}")
            self.play_sound("fail")  # מנסים לתקוף כלי שלנו
            return
        
        start_notation = f"{chr(ord('a') + current_x)}{8 - current_y}"
        end_notation = f"{chr(ord('a') + final_x)}{8 - final_y}"
        
        if target_piece:
            logger.info(f"מהלך תקיפה: {piece.piece_id} מ-{start_notation} ל-{end_notation} (תוקף את {target_piece.piece_id})")
        else:
            logger.info(f"מהלך רגיל: {piece.piece_id} מ-{start_notation} ל-{end_notation}")
        
        self.user_input_queue.put(Command(
            timestamp=self.game_time_ms(),
            piece_id=piece.piece_id,
            type="move",
            target=(final_x, final_y),
            params=[start_notation, end_notation]
        ))
        
        from datetime import datetime
        self.publisher.notify(MoveMadeEvent(
            piece_type=piece.piece_id[0],
            start_position=start_notation,
            end_position=end_notation,
            player_color="white" if 'W' in piece.piece_id else "black",
            timestamp=datetime.now()
        ))
        
        self.play_sound("move")

    def _check_path(self, start_x, start_y, end_x, end_y, piece_type):
        if piece_type.startswith('N') or (piece_type.startswith('K') and abs(end_x - start_x) <= 1 and abs(end_y - start_y) <= 1):
            return None
        
        dx, dy = end_x - start_x, end_y - start_y
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        
        x, y = start_x + step_x, start_y + step_y
        while (x, y) != (end_x, end_y):
            if self._find_piece_at_position(x, y):
                return (x, y)
            x, y = x + step_x, y + step_y
        return None

    def _is_valid_move(self, piece, new_x, new_y, player_num):
        if not (0 <= new_x <= 7 and 0 <= new_y <= 7):
            return False
        
        current_pos = self._get_piece_position(piece)
        if not current_pos:
            return False
        
        dx, dy = new_x - current_pos[0], new_y - current_pos[1]
        
        # תמיכה בשני הסוגים: State (moves) ו-State הישן (_moves)
        moves_obj = None
        if hasattr(piece._state, 'moves'):
            moves_obj = piece._state.moves
        elif hasattr(piece._state, '_moves'):
            moves_obj = piece._state._moves
        
        if moves_obj and hasattr(moves_obj, 'valid_moves'):
            for move_dx, move_dy, move_type in moves_obj.valid_moves:
                if dx == move_dx and dy == move_dy:
                    # בדיקת חסימה בדרך
                    blocking_pos = self._check_path(*current_pos, new_x, new_y, piece.piece_id)
                    if blocking_pos and blocking_pos != (new_x, new_y):
                        return False
                    
                    # לוגיקה פשוטה: בדוק מה יש במקום היעד
                    target_piece = self._find_piece_at_position(new_x, new_y)
                    
                    # אם זה תנועת תפיסה (capture) - חייב להיות יריב
                    if move_type == "capture":
                        return target_piece and not self._is_player_piece(target_piece, player_num)
                    
                    # אם זה תנועה רגילה (non_capture או 1st) - המקום חייב להיות ריק
                    if move_type in ["non_capture", "1st"]:
                        if target_piece is not None:
                            return False
                        # בדיקה מיוחדת למהלך ראשון של חיל
                        if move_type == "1st":
                            if piece.piece_id.startswith('PW'):
                                return current_pos[1] == 6  # חיל לבן במיקום ראשוני
                            elif piece.piece_id.startswith('PB'):
                                return current_pos[1] == 1  # חיל שחור במיקום ראשוני
                        return True
                    
                    # תנועה רגילה של כלים אחרים
                    return not (target_piece and self._is_player_piece(target_piece, player_num))
        return False

    def _resolve_collisions(self):
        pass

    def _is_win(self) -> bool:
        kings = {p.piece_id for p in self.pieces if p.piece_id.startswith('K')}
        return not {'KW0', 'KB0'}.issubset(kings)

    def _announce_win(self):
        logger.info("מכריז על ניצחון")
        self.play_sound("win")
        kings = {p.piece_id for p in self.pieces if p.piece_id.startswith('K')}
        
        # קבע מי ניצח - המנצח הוא זה שהמלך שלו עדיין קיים
        winner = None
        if 'KB0' in kings and 'KW0' not in kings:
            winner = "black"  # המלך השחור קיים והלבן לא - שחור ניצח
        elif 'KW0' in kings and 'KB0' not in kings:
            winner = "white"  # המלך הלבן קיים והשחור לא - לבן ניצח
        
        # שימוש בשמות האמיתיים של השחקנים
        winner_map = {
            "black": f"🎉 {self.player_names['player2']} (שחור) ניצח! 🎉",
            "white": f"🎉 {self.player_names['player1']} (לבן) ניצח! 🎉"
        }
        winner_text = winner_map.get(winner, "🎮 המשחק נגמר! 🎮")
        logger.info(f"תוצאת המשחק: {winner_text}")
        
        # שלח GameOverEvent עם winner_text
        game_over_event = GameOverEvent(winner=winner, reason="king_captured")
        game_over_event.data["winner_text"] = winner_text
        self.publisher.notify(game_over_event)
        
        # הצג הודעת ניצחון למשך זמן קצוב ואז סיים את המשחק
        import threading
        import time
        
        def end_game_after_delay():
            time.sleep(3)  # המתן 3 שניות
            logger.info("המשחק מסתיים אחרי הודעת הניצחון")
            self.game_over = True
        
        # הפעל timer ברקע
        threading.Thread(target=end_game_after_delay, daemon=True).start()