import pathlib
from typing import Dict, Tuple
import json
from Board import Board
from GraphicsFactory import GraphicsFactory
from Moves import Moves
from PhysicsFactory import PhysicsFactory
from Piece import Piece

class PieceFactory:
    def __init__(self, board: Board, pieces_root: pathlib.Path):
        """Initialize piece factory with board and 
        generates the library of piece templates from the pieces directory.."""
        self.board = board
        self.pieces_root = pieces_root
        self.gfx_factory = GraphicsFactory()
        self.physics_factory = PhysicsFactory(board)

    def _build_state_machine(self, piece_dir: pathlib.Path, cell: Tuple[int, int], piece_id: str, game_queue=None):
        """בנה state machine מקבצי הקונפיגורציה - גרסה פשוטה"""
        # טען moves.txt
        moves_path = piece_dir / "moves.txt"
        moves = Moves.from_file(moves_path)

        # טען רק את state idle כמו במקור, אבל עם שימוש בקונפיגורציה
        states_dir = piece_dir / "states"
        idle_dir = states_dir / "idle"
        
        if not idle_dir.exists():
            raise ValueError(f"תיקיית idle לא קיימת עבור {piece_dir.name}")
        
        # טען קונפיגורציה של idle
        config_path = idle_dir / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
        else:
            config = {"physics": {}, "graphics": {}}
        
        sprites_dir = idle_dir / "sprites"

        graphics = self.gfx_factory.load(
            sprites_dir=sprites_dir,
            cfg=config.get("graphics", {}),
            board=self.board
        )
        physics = self.physics_factory.create(
            start_cell=cell,
            cfg=config.get("physics", {}),
            piece_id=piece_id
        )
        
        # השתמש במבנה State הישן
        from State import State
        return State(moves, graphics, physics, game_queue)

    def create_piece(self, p_type: str, cell: Tuple[int, int], game_queue=None) -> Piece:
        """Create a piece of the specified type at the given cell."""
        piece_dir = self.pieces_root / p_type
        state = self._build_state_machine(piece_dir, cell, p_type, game_queue)
        return Piece(piece_id=p_type, init_state=state)
