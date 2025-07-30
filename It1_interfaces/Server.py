import socket
import json
import threading
import logging
from typing import Dict, List, Optional
import pathlib
import queue
import time

from img import Img
from Board import Board
from Game import Game
from Command import Command
from PieceFactory import PieceFactory

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChessServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.clients = {}
        self.game = None
        
        self._init_game()
    
    def _init_game(self):
        """אתחול המשחק - רק לוגיקה ללא גרפיקה"""
        img = Img()
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
            
            piece = factory.create_piece(p_type, cell, queue.Queue())
            piece.piece_id = unique_id
            
            if hasattr(piece._state, 'physics'):
                piece._state.physics.piece_id = unique_id
            elif hasattr(piece._state, '_physics'):
                piece._state._physics.piece_id = unique_id
                
            pieces.append(piece)
        
        self.game = Game(pieces, board)
        logger.info(f"השרת אותחל עם {len(pieces)} כלים")
    
    def start_server(self):
        """הפעלת השרת"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(2)
        
        logger.info(f"השרת מאזין על {self.host}:{self.port}")
        
        game_thread = threading.Thread(target=self._game_loop, daemon=True)
        game_thread.start()
        
        while True:
            try:
                client_socket, address = self.socket.accept()
                logger.info(f"לקוח חדש התחבר: {address}")
                
                client_id = f"player_{len(self.clients) + 1}"
                self.clients[client_id] = client_socket
                
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, client_id),
                    daemon=True
                )
                client_thread.start()
                
                self._send_game_state(client_socket)
                
            except Exception as e:
                logger.error(f"שגיאה בקבלת לקוח: {e}")
    
    def _handle_client(self, client_socket, client_id):
        """טיפול בלקוח ספציפי"""
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    message = json.loads(data)
                    self._process_client_message(message, client_id)
                except json.JSONDecodeError:
                    logger.error(f"הודעה לא תקינה מ-{client_id}: {data}")
                    
        except Exception as e:
            logger.error(f"שגיאה בטיפול בלקוח {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            client_socket.close()
            logger.info(f"לקוח {client_id} התנתק")
    
    def _process_client_message(self, message, client_id):
        """עיבוד הודעה מלקוח"""
        msg_type = message.get('type')
        
        if msg_type == 'keyboard_input':
            key = message.get('key')
            self._simulate_keyboard_input(key, client_id)
    
    def _simulate_keyboard_input(self, key, client_id):
        """סימולציה של קלט מקלדת במשחק"""
        char = chr(key).lower() if 32 <= key <= 126 else None
        hebrew_map = {1493: 'w', 215: 'w', 1513: 'a', 249: 'a', 1491: 's', 212: 's', 1499: 'd', 235: 'd'}
        char = hebrew_map.get(key, char)
        
        if client_id == "player_1":  # שחקן 1 - לבן - מקשי מספרים
            moves_p1 = {56: (0, -1), 50: (0, 1), 52: (-1, 0), 54: (1, 0)}
            if key in moves_p1:
                self.game._move_cursor_player1(*moves_p1[key])
            elif key in [53, 48, 13, 10]:
                self.game._select_piece_player1()
        
        elif client_id == "player_2":  # שחקן 2 - שחור - WASD
            moves_p2 = {('w', 119, 87): (0, -1), ('s', 115, 83): (0, 1), ('a', 97, 65): (-1, 0), ('d', 100, 68): (1, 0)}
            for keys, move in moves_p2.items():
                if key in keys[1:] or char == keys[0]:
                    self.game._move_cursor_player2(*move)
                    return
            
            if key == 32:
                self.game._select_piece_player2()
    
    def _game_loop(self):
        """לולאת המשחק - רק לוגיקה"""
        logger.info("לולאת המשחק התחילה")
        start_ms = self.game.game_time_ms()
        
        for p in self.game.pieces:
            p.reset(start_ms)
        
        while not self.game.game_over:
            now = self.game.game_time_ms()
            
            for p in self.game.pieces:
                p.update(now)
            
            while not self.game.user_input_queue.empty():
                cmd = self.game.user_input_queue.get()
                self.game._process_input(cmd)
                if self.game.game_over:
                    break
            
            self._broadcast_game_state()
            time.sleep(1/60.0)
    
    def _broadcast_game_state(self):
        """שלח מצב המשחק לכל הלקוחות"""
        game_state = self._get_game_state()
        message = json.dumps({
            'type': 'game_state',
            'data': game_state
        })
        
        for client_id, client_socket in list(self.clients.items()):
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                del self.clients[client_id]
    
    def _send_game_state(self, client_socket):
        """שלח מצב המשחק ללקוח ספציפי"""
        game_state = self._get_game_state()
        message = json.dumps({
            'type': 'game_state',
            'data': game_state
        })
        try:
            client_socket.send(message.encode('utf-8'))
        except:
            pass
    
    def _get_game_state(self) -> dict:
        """קבל מצב המשחק - רק מיקומים"""
        pieces_state = []
        
        for piece in self.game.pieces:
            pos = self.game._get_piece_position(piece)
            if pos:
                pieces_state.append({
                    'id': piece.piece_id,
                    'position': pos,
                    'type': piece.piece_id[:-1] if piece.piece_id[-1].isdigit() else piece.piece_id
                })
        
        return {
            'pieces': pieces_state,
            'cursors': {
                'player1': self.game.cursor_pos_player1,
                'player2': self.game.cursor_pos_player2
            },
            'selected': {
                'player1': self.game._get_piece_position(self.game.selected_piece_player1),
                'player2': self.game._get_piece_position(self.game.selected_piece_player2)
            },
            'score': {
                'white': self.game.score_tracker.get_score("white"),
                'black': self.game.score_tracker.get_score("black")
            },
            'moves': {
                'white': self.game.move_logger.get_moves("white"),
                'black': self.game.move_logger.get_moves("black")
            },
            'game_over': self.game.game_over,
            'winner': self.game.winner_tracker.get_winner_text() if self.game.winner_announced else None,
            'player_names': self.game.player_names
        }

if __name__ == "__main__":
    server = ChessServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        logger.info("השרת נסגר")