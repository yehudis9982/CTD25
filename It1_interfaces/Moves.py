# Moves.py  – drop-in replacement
import pathlib
from typing import List, Tuple


class Moves:
    @staticmethod
    def from_file(path, dims=None):
        moves = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                dx = int(parts[0])
                dy = int(parts[1].split(":")[0])  # תומך גם ב-0:non_capture
                moves.append((dx, dy))
        return Moves(moves, dims)

    def __init__(self, moves: List[Tuple[int, int]], dims=None):
        self.moves = moves
        self.dims = dims

    def get_moves(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get all possible moves from a given position."""
        if self.dims is None:
            return [(r + dr, c + dc) for dr, dc in self.moves]
        # אם יש מגבלות לוח
        rows, cols = self.dims
        valid = []
        for dr, dc in self.moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                valid.append((nr, nc))
        return valid
