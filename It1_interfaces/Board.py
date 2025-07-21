from dataclasses import dataclass

from img import Img

@dataclass
class Board:
    cell_H_pix: int
    cell_W_pix: int
    cell_H_m: int
    cell_W_m: int
    W_cells: int
    H_cells: int
    img: Img

    # convenience, not required by dataclass
    def clone(self) -> "Board":
        """Clone the board with a copy of the image."""
        pass