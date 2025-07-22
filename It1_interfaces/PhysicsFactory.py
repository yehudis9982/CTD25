from Board import Board
from Physics import Physics


class PhysicsFactory:      # very light for now
    def __init__(self, board: Board): 
        """Initialize physics factory with board."""
        self.board = board
        
    def create(self, start_cell, cfg, piece_id: str = None) -> Physics:
        """Create a physics object with the given configuration."""
        speed = cfg.get("speed_m_per_sec", 1.0)
        return Physics(start_cell=start_cell, board=self.board, speed_m_s=speed, piece_id=piece_id)
