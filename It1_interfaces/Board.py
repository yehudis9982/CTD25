from dataclasses import dataclass

from img import Img  # ייבוא מוחלט במקום יחסי

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
        ממיר מיקום תא (עמודה, שורה) למיקום בפיקסלים על המסך.
        cell = (x, y) כשמערכת הקואורדינטות היא (עמודה, שורה)
        """
        x, y = cell  # x=עמודה, y=שורה
        pixel_x = int(x * self.cell_W_pix)
        pixel_y = int(y * self.cell_H_pix)
        return pixel_x, pixel_y
