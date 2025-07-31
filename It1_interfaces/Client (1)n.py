import socket
import json
import threading
import logging
import pathlib
import cv2
import time
from typing import Dict, List, Optional

from img import Img
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from Command import Command

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChessClient:
    def __init__(self, host='217.194.157.58', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.game = None
        self.game_over = False
        
        self._init_game()
    
    def _init_game(self):
        """אתחול המשחק המקורי בלקוח"""
        img = Img()
        img.read(pathlib.Path(__file__).parent.parent / "board.png")
        
        if img.img is None:
            logger.error("לא ניתן לטעון את תמונת הלוח")
            raise RuntimeError("Board image failed to load!")
        
        board = Board(
            cell_H_pix=103.5,
            cell_W_pix=102.75,
            cell_H_m=1,
            cell_W_m=1,
            W_cells=8,
            H_cells=8,
            img=img
        )
        
        pieces_root = pathlib.Path(__file__).parent.parent / "pieces"
        factory = PieceFactory(board, pieces_root)
        
        start_positions = [
            ("RB", (0, 0)), ("NB", (1, 0)), ("BB", (2, 0)), ("QB", (3, 0)), 
            ("KB", (4, 0)), ("BB", (5, 0)), ("NB", (6, 0)), ("RB", (7, 0)),
            ("PB", (0, 1)), ("PB", (1, 1)), ("PB", (2, 1)), ("PB", (3, 1)), 
            ("PB", (4, 1)), ("PB", (5, 1)), ("PB", (6, 1)), ("PB", (7, 1)),
            ("PW", (0, 6)), ("PW", (1, 6)), ("PW", (2, 6)), ("PW", (3, 6)), 
            ("PW", (4, 6)), ("PW", (5, 6)), ("PW", (6, 6)), ("PW", (7, 6)),
            ("RW", (0, 7)), ("NW", (1, 7)), ("BW", (2, 7)), ("QW", (3, 7)), 
            ("KW", (4, 7)), ("BW", (5, 7)), ("NW", (6, 7)), ("RW", (7, 7)),
        ]
        
        pieces = []
        piece_counters = {}
        
        for p_type, cell in start_positions:
            if p_type not in piece_counters:
                piece_counters[p_type] = 0
            unique_id = f"{p_type}{piece_counters[p_type]}"
            piece_counters[p_type] += 1
            
            piece = factory.create_piece(p_type, cell, None)
            piece.piece_id = unique_id
            
            if hasattr(piece._state, 'physics'):
                piece._state.physics.piece_id = unique_id
            elif hasattr(piece._state, '_physics'):
                piece._state._physics.piece_id = unique_id
                
            pieces.append(piece)
        
        self.game = Game(pieces, board)
        
        # הוסף מהלכים דמו לבדיקה
        self._add_demo_moves()
        
        logger.info("לקוח אותחל עם משחק מלא")
    
    def connect_to_server(self):
        """התחברות לשרת"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"התחבר לשרת {self.host}:{self.port}")
            
            receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            receive_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"שגיאה בהתחברות לשרת: {e}")
            return False
    
    def _receive_messages(self):
        """קבלת הודעות מהשרת"""
        try:
            while self.connected:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                try:
                    message = json.loads(data)
                    self._process_server_message(message)
                except json.JSONDecodeError:
                    logger.error(f"הודעה לא תקינה מהשרת: {data}")
                    
        except Exception as e:
            logger.error(f"שגיאה בקבלת הודעות: {e}")
        finally:
            self.connected = False
    
    def _process_server_message(self, message):
        """עיבוד הודעה מהשרת"""
        msg_type = message.get('type')
        
        if msg_type == 'game_state':
            game_data = message.get('data')
            if game_data:
                self._sync_game_state(game_data)
                
        elif msg_type == 'moves_update':
            moves_data = message.get('data')
            if moves_data:
                self._sync_moves_and_score(moves_data)
                
        elif msg_type == 'error':
            logger.warning(f"שגיאה מהשרת: {message.get('message')}")
    
    def _sync_game_state(self, server_state):
        """סנכרון מצב המשחק עם השרת"""
        server_pieces = {p['id']: p for p in server_state.get('pieces', [])}
        
        for piece in self.game.pieces:
            if piece.piece_id in server_pieces:
                server_piece = server_pieces[piece.piece_id]
                server_pos = tuple(server_piece['position'])
                current_pos = self.game._get_piece_position(piece)
                
                if current_pos != server_pos:
                    logger.info(f"מזיז כלי {piece.piece_id} מ-{current_pos} ל-{server_pos}")
                    cmd = Command(
                        timestamp=self.game.game_time_ms(),
                        piece_id=piece.piece_id,
                        type="move",
                        target=server_pos,
                        params=None
                    )
                    self.game.user_input_queue.put(cmd)
        
        cursors = server_state.get('cursors', {})
        self.game.cursor_pos_player1 = cursors.get('player1', [0, 7])
        self.game.cursor_pos_player2 = cursors.get('player2', [0, 0])
        
        selected = server_state.get('selected', {})
        self.game.selected_piece_player1 = self._find_piece_by_position(selected.get('player1'))
        self.game.selected_piece_player2 = self._find_piece_by_position(selected.get('player2'))
    
    def _sync_moves_and_score(self, moves_data):
        """סנכרון טבלת מהלכים וניקוד מהשרת"""
        logger.info(f"מעדכן מהלכים וניקוד מהשרת: {moves_data}")
        
        if 'moves' in moves_data:
            moves = moves_data['moves']
            self.game.move_logger.moves['white'] = moves.get('white', [])
            self.game.move_logger.moves['black'] = moves.get('black', [])
            logger.info(f"עודכנו מהלכים: white={len(self.game.move_logger.moves['white'])}, black={len(self.game.move_logger.moves['black'])}")
        
        if 'scores' in moves_data:
            scores = moves_data['scores']
            self.game.score_tracker.score['white'] = scores.get('white', 0)
            self.game.score_tracker.score['black'] = scores.get('black', 0)
            logger.info(f"עודכן ניקוד: white={self.game.score_tracker.score['white']}, black={self.game.score_tracker.score['black']}")
    
    def _find_piece_by_position(self, position):
        """מצא כלי לפי מיקום"""
        if not position:
            return None
        for piece in self.game.pieces:
            if self.game._get_piece_position(piece) == tuple(position):
                return piece
        return None
    
    def send_keyboard_input(self, key):
        """שלח קלט מקלדת לשרת"""
        if not self.connected:
            return False
        
        message = {
            'type': 'keyboard_input',
            'key': key
        }
        
        try:
            self.socket.send(json.dumps(message).encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"שגיאה בשליחת קלט: {e}")
            return False
    
    def run(self, standalone=False):
        """הפעלת הלקוח"""
        if not standalone and not self.connect_to_server():
            logger.info("לא ניתן להתחבר לשרת, עובר למצב עצמאי")
            standalone = True
        
        logger.info("הלקוח מתחיל לרוץ")
        if standalone:
            logger.info("מצב עצמאי - טבלת מהלכים וניקוד מוצגים")
            logger.info("שחקן 1 (לבן): מקשי מספרים - 8,2,4,6 לתנועה, 5/0/Enter לבחירה")
            logger.info("שחקן 2 (שחור): WASD לתנועה, רווח לבחירה")
            logger.info("לחץ ESC או Q ליציאה")
        
        start_ms = self.game.game_time_ms()
        for p in self.game.pieces:
            p.reset(start_ms)
        
        while (self.connected or standalone) and not self.game.game_over:
            now = self.game.game_time_ms()
            
            for p in self.game.pieces:
                p.update(now)
            
            while not self.game.user_input_queue.empty():
                cmd = self.game.user_input_queue.get()
                self.game._process_input(cmd)
            
            self._draw_game()
            
            if not self._handle_input():
                break
                
            time.sleep(1/60.0)
        
        logger.info("הלקוח נסגר")
        cv2.destroyAllWindows()
    
    def _handle_input(self) -> bool:
        """טיפול בקלט מהמקלדת"""
        try:
            cv2.setWindowProperty("Chess Game", cv2.WND_PROP_TOPMOST, 1)
        except cv2.error:
            pass
            
        key = cv2.waitKey(30) & 0xFF
        
        if key == 255 or key == -1:
            return True
        
        if key in [27, ord('q')]:
            return False
        
        if self.connected:
            self.send_keyboard_input(key)
        else:
            self.game._handle_keyboard_input(key)
        
        return True
    
    def _draw_game(self):
        """ציור המשחק עם כל המידע הנדרש"""
        display_board = self.game.clone_board()
        now = self.game.game_time_ms()
        for p in self.game.pieces:
            p.draw_on_board(display_board, now)
        
        if hasattr(display_board, "img"):
            white_moves = self.game.move_logger.get_moves("white")
            black_moves = self.game.move_logger.get_moves("black")
            
            info = {
                'cursors_info': {
                    'player1_cursor': self.game.cursor_pos_player1,
                    'player2_cursor': self.game.cursor_pos_player2,
                    'player1_selected': self.game._get_piece_position(self.game.selected_piece_player1),
                    'player2_selected': self.game._get_piece_position(self.game.selected_piece_player2)
                },
                'score_info': {
                    'white_score': self.game.score_tracker.get_score("white"),
                    'black_score': self.game.score_tracker.get_score("black")
                },
                'moves_info': {
                    'white_moves': white_moves,
                    'black_moves': black_moves
                },
                'player_names': self.game.player_names
            }
            
            winner_text = self.game.winner_tracker.get_winner_text()
            if winner_text:
                winner_enum = self.game.winner_tracker.get_winner()
                self.game._draw_winner_image_on_board(display_board, winner_text, winner_enum)
            
            display_board.img.display_with_background("Chess Game", **info)
    
    def _add_demo_moves(self):
        """הוסף מהלכים דמו לבדיקה"""
        demo_moves = [
            {"move": "P e2 -> e4", "time": "14:30:15"},
            {"move": "N g1 -> f3", "time": "14:30:45"},
            {"move": "B f1 -> c4", "time": "14:31:12"}
        ]
        
        demo_black_moves = [
            {"move": "P e7 -> e5", "time": "14:30:30"},
            {"move": "N b8 -> c6", "time": "14:31:00"}
        ]
        
        self.game.move_logger.moves['white'] = demo_moves
        self.game.move_logger.moves['black'] = demo_black_moves
        self.game.score_tracker.score['white'] = 3
        self.game.score_tracker.score['black'] = 1
        
        logger.info(f"הוספו מהלכים דמו: white={len(demo_moves)}, black={len(demo_black_moves)}")
    
    def disconnect(self):
        """התנתקות מהשרת"""
        self.connected = False
        if self.socket:
            self.socket.close()

if __name__ == "__main__":
    import sys
    
    standalone_mode = '--standalone' in sys.argv or '-s' in sys.argv
    
    client = ChessClient()
    try:
        client.run(standalone=standalone_mode)
    except KeyboardInterrupt:
        logger.info("הלקוח נסגר על ידי המשתמש")
    finally:
        client.disconnect()