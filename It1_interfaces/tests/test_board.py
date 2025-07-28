import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
import pytest
from It1_interfaces.Board import Board

class MockImg:
    def __init__(self, arr=None):
        self.img = arr

def test_board_clone():
    arr = np.ones((10, 10, 3), dtype=np.uint8)
    img = MockImg(arr)
    board = Board(
        cell_H_pix=32,
        cell_W_pix=32,
        cell_H_m=1,
        cell_W_m=1,
        W_cells=8,
        H_cells=8,
        img=img
    )
    clone = board.clone()
    # בדוק שהשיבוט הוא Board חדש
    assert clone is not board
    # בדוק שהשיבוט כולל MockImg חדש
    assert clone.img is not board.img
    # בדוק שהמערך הועתק (ולא אותו אובייקט)
    assert np.array_equal(clone.img.img, board.img.img)
    assert clone.img.img is not board.img.img
    # שינוי בשיבוט לא משפיע על המקור
    clone.img.img[0,0,0] = 99
    assert board.img.img[0,0,0] != 99