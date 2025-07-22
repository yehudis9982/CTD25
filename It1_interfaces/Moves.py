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
                # קובץ התנועות כתוב כ-dy,dx ולא dx,dy
                dy = int(parts[0])
                dx_part = parts[1].split(":")
                dx = int(dx_part[0])
                move_type = dx_part[1] if len(dx_part) > 1 else "normal"
                moves.append((dx, dy, move_type))  # שומרים כ-dx,dy
        return Moves(moves, dims)

    def __init__(self, moves: List[Tuple[int, int, str]], dims=None):
        self.moves = moves
        self.dims = dims
        # שמירת רשימה נוספת עם סוגי התנועות
        self.valid_moves = moves

    def get_moves(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get all possible moves from a given position (basic moves only)."""
        if self.dims is None:
            return [(r + dr, c + dc) for dr, dc, _ in self.moves]
        # אם יש מגבלות לוח
        rows, cols = self.dims
        valid = []
        for dr, dc, _ in self.moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                valid.append((nr, nc))
        return valid
