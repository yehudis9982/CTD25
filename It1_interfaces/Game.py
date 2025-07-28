import pathlib, queue, time, cv2
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
                    return {
                        'player1': names.get('player1', 'PLAYER 1'),
                        'player2': names.get('player2', 'PLAYER 2')
                    }
        except Exception as e:
            print(f"⚠️ לא ניתן לטעון שמות משתמשים: {e}")
        return {'player1': 'PLAYER 1', 'player2': 'PLAYER 2'}

    def game_time_ms(self) -> int:
        return int(time.monotonic() * 1000)

    def play_sound(self, sound_name):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound_path = pathlib.Path(r"c:\Users\01\Desktop\chess (3)\chess\CTD25\Sounds") / f"{sound_name}.mp3"
            if sound_path.exists():
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                while not pygame.mixer.music.get_busy():
                    pygame.time.wait(10)
                if sound_name == "win":
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
            else:
                print(f"⚠️ לא נמצא קובץ צליל: {sound_path}")
        except Exception as e:
            print(f"⚠️ שגיאה בהשמעת צליל: {e}")
            pass

    def clone_board(self) -> Board:
        return self.board.clone()

    def run(self):
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)

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
        cv2.destroyAllWindows()

    def _process_input(self, cmd : Command):
        if cmd.type == "arrived":
            self._handle_arrival(cmd)
            return
        elif cmd.type == "jump":
            # כשכלי מתחיל קפיצה, מוסיפים אותו לרשימת הקופצים
            self.jumping_pieces.add(cmd.piece_id)
        
        for piece in self.pieces:
            if piece.piece_id == cmd.piece_id:
                piece.on_command(cmd, self.game_time_ms())
                if self._is_win() and not self.winner_announced:
                    self._announce_win()
                    self.winner_announced = True
                break

    def _handle_arrival(self, cmd: Command):
        arriving_piece = next((p for p in self.pieces if p.piece_id == cmd.piece_id), None)
        if not arriving_piece:
            return
        
        # אם הכלי היה בקפיצה, מוציאים אותו מהרשימה
        if cmd.piece_id in self.jumping_pieces:
            self.jumping_pieces.remove(cmd.piece_id)
        
        # תמיכה בשני הסוגים: NewState (physics) ו-State הישן (_physics)
        physics = getattr(arriving_piece._state, 'physics', None) or getattr(arriving_piece._state, '_physics', None)
        target_pos = physics.cell if physics else None
        if not target_pos:
            return
            
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
            self.publisher.notify(PieceCaptureEvent(piece_type, captured_by))
            self.play_sound("keel")
        
        if pieces_to_remove and self._is_win() and not self.winner_announced:
            self._announce_win()
            self.winner_announced = True

    def _check_pawn_promotion(self, piece, target_pos):
        if not piece.piece_id.startswith('P'):
            return
            
        col, row = target_pos
        promotion_rules = {('W', 0): "QW", ('B', 7): "QB"}
        color = 'W' if 'W' in piece.piece_id else 'B'
        
        if (color, row) in promotion_rules:
            self._promote_pawn_to_queen(piece, promotion_rules[(color, row)], target_pos)

    def _promote_pawn_to_queen(self, pawn, queen_type, position):
        from PieceFactory import PieceFactory
        factory = PieceFactory(self.board, pathlib.Path(r"c:\Users\01\Desktop\chess\CTD25\pieces"))
        
        existing_queens = [p for p in self.pieces if p.piece_id.startswith(queen_type)]
        queen_id = f"{queen_type}{len(existing_queens)}"
        
        new_queen = factory.create_piece(queen_type, position, self.user_input_queue)
        new_queen.piece_id = queen_id
        
        # תמיכה בשני הסוגים: NewState (physics) ו-State הישן (_physics)
        physics = getattr(new_queen._state, 'physics', None) or getattr(new_queen._state, '_physics', None)
        if physics:
            physics.piece_id = queen_id
        
        self.pieces.remove(pawn)
        self.pieces.append(new_queen)

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
                self._draw_winner_text_on_board(display_board, winner_text)
            
            display_board.img.display_with_background("Chess Game", **info)

    def _draw_winner_text_on_board(self, board, winner_text):
        if not (hasattr(board, 'img') and hasattr(board.img, 'img')):
            return
            
        img = board.img.img
        h, w = img.shape[:2]
        overlay = img.copy()
        center_x, center_y = w // 2, h // 2
        
        cv2.rectangle(overlay, (center_x - 300, center_y - 75), (center_x + 300, center_y + 75), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(winner_text, font, 1.5, 3)[0]
        text_x, text_y = center_x - text_size[0] // 2, center_y + text_size[1] // 2
        
        cv2.putText(img, winner_text, (text_x + 2, text_y + 2), font, 1.5, (0, 0, 0), 5)
        cv2.putText(img, winner_text, (text_x, text_y), font, 1.5, (0, 255, 255), 3)
        
        sub_text = "Game continues - Press ESC to exit"
        sub_size = cv2.getTextSize(sub_text, font, 0.8, 2)[0]
        sub_x = center_x - sub_size[0] // 2
        cv2.putText(img, sub_text, (sub_x + 1, text_y + 51), font, 0.8, (0, 0, 0), 3)
        cv2.putText(img, sub_text, (sub_x, text_y + 50), font, 0.8, (255, 255, 255), 2)

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
                        self.play_sound("fail")  # כלי במנוחה
                        return
                setattr(self, selected_attr, piece)
            elif piece:
                # מנסים לבחור כלי של השחקן השני
                self.play_sound("fail")
        else:
            current_pos = self._get_piece_position(selected_piece)
            if current_pos == (x, y):
                # בדיקה אם הכלי במנוחה לפני קפיצה
                if hasattr(selected_piece, '_state') and hasattr(selected_piece._state, 'can_transition'):
                    if not selected_piece._state.can_transition(self.game_time_ms()):
                        self.play_sound("fail")  # כלי במנוחה
                        setattr(self, selected_attr, None)
                        return
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
                        self.play_sound("fail")  # כלי במנוחה
                        setattr(self, selected_attr, None)
                        return
                self._move_piece(selected_piece, x, y, player_num)
            setattr(self, selected_attr, None)

    def _get_piece_position(self, piece):
        if not piece:
            return None
        # תמיכה בשני הסוגים: NewState (physics) ו-State הישן (_physics)
        if hasattr(piece, '_state'):
            physics = getattr(piece._state, 'physics', None) or getattr(piece._state, '_physics', None)
            if physics and hasattr(physics, 'cell'):
                # print(f"🎯 מיקום {piece.piece_id}: {physics.cell}")  # disable this debug
                return physics.cell
        return getattr(piece, 'board_position', None) or (getattr(piece, 'x', None), getattr(piece, 'y', None))

    def _find_piece_at_position(self, x, y):
        return next((p for p in self.pieces if self._get_piece_position(p) == (x, y)), None)

    def _is_player_piece(self, piece, player_num):
        return ('W' in piece.piece_id) == (player_num == 1)

    def _move_piece(self, piece, new_x, new_y, player_num):
        if not self._is_valid_move(piece, new_x, new_y, player_num):
            self.play_sound("fail")  # מהלך לא חוקי
            return
        
        current_pos = self._get_piece_position(piece)
        if not current_pos:
            self.play_sound("fail")  # לא ניתן למצוא מיקום הכלי
            return
        
        current_x, current_y = current_pos
        blocking_position = self._check_path(current_x, current_y, new_x, new_y, piece.piece_id)
        final_x, final_y = blocking_position if blocking_position else (new_x, new_y)
        
        target_piece = self._find_piece_at_position(final_x, final_y)
        if target_piece and self._is_player_piece(target_piece, player_num):
            self.play_sound("fail")  # מנסים לתקוף כלי שלנו
            return
        
        start_notation = f"{chr(ord('a') + current_x)}{8 - current_y}"
        end_notation = f"{chr(ord('a') + final_x)}{8 - final_y}"
        
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
        
        # תמיכה בשני הסוגים: NewState (moves) ו-State הישן (_moves)
        moves_obj = None
        if hasattr(piece._state, 'moves'):
            moves_obj = piece._state.moves
        elif hasattr(piece._state, '_moves'):
            moves_obj = piece._state._moves
        
        if moves_obj and hasattr(moves_obj, 'valid_moves'):
            for move_dx, move_dy, _ in moves_obj.valid_moves:
                if dx == move_dx and dy == move_dy:
                    blocking_pos = self._check_path(*current_pos, new_x, new_y, piece.piece_id)
                    return not (blocking_pos and blocking_pos != (new_x, new_y))
        return False

    def _resolve_collisions(self):
        pass

    def _is_win(self) -> bool:
        kings = {p.piece_id for p in self.pieces if p.piece_id.startswith('K')}
        return not {'KW0', 'KB0'}.issubset(kings)

    def _announce_win(self):
        self.play_sound("win")
        kings = {p.piece_id for p in self.pieces if p.piece_id.startswith('K')}
        
        # שימוש בשמות האמיתיים של השחקנים
        winner_map = {
            frozenset(['KB0']): f"{self.player_names['player2']} (BLACK) WINS!",
            frozenset(['KW0']): f"{self.player_names['player1']} (WHITE) WINS!"
        }
        winner_text = winner_map.get(frozenset(kings), "GAME OVER!")
        self.winner_tracker.set_winner_text(winner_text)