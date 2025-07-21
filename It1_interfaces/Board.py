from dataclasses import dataclass

from CTD25.It1_interfaces.img import Img  # ייבוא מוחלט במקום יחסי

@dataclass
class Board:
    cell_H_pix: int
    cell_W_pix: int
    cell_H_m: int
    cell_W_m: int
    W_cells: int
    H_cells: int
    img: Img

    def clone(self) -> "Board":
        new_img = Img()
        new_img.img = self.img.img.copy() if self.img.img is not None else None
        return Board(
            cell_H_pix=self.cell_H_pix,
            cell_W_pix=self.cell_W_pix,
            cell_H_m=self.cell_H_m,
            cell_W_m=self.cell_W_m,
            W_cells=self.W_cells,
            H_cells=self.H_cells,
            img=new_img
        )

    def cell_to_pixel(self, cell: tuple[int, int]) -> tuple[int, int]:
        """
        ממיר מיקום תא (שורה, עמודה) למיקום בפיקסלים על המסך.
        """
        row, col = cell
        x = int(col * self.cell_W_pix)
        y = int(row * self.cell_H_pix)
        return x, y