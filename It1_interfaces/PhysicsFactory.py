from Board import Board
from Physics import Physics


class PhysicsFactory:      # very light for now
    def __init__(self, board: Board): 
        """Initialize physics factory with board."""
        pass
        
    def create(self, start_cell, cfg) -> Physics:
        """Create a physics object with the given configuration."""
        pass 