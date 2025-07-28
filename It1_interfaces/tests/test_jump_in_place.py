#!/usr/bin/env python3
"""
בדיקה פשוטה לאנימציית קפיצה במקום.
בוחר כלי ואז לוחץ על אותו מיקום שוב כדי לראות אנימציית קפיצה.
"""

import time
import pathlib
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from Command import Command
from img import Img

def test_jump_in_place():
    print("🐎 בדיקת קפיצה במקום...")
    
    # יצירת לוח ומפעל כלים
    img = Img()
    img.read(r"c:\Users\01\Desktop\chess\CTD25\board.png")
    
    board = Board(
        cell_H_pix=103.5,
        cell_W_pix=102.75,
        cell_H_m=1,
        cell_W_m=1,
        W_cells=8,
        H_cells=8,
        img=img
    )
    pieces_root = pathlib.Path(r"c:\Users\01\Desktop\chess\CTD25\pieces")
    factory = PieceFactory(board, pieces_root)
    
    # צור משחק
    game = Game([], board)
    
    # צור סוס לבן ב-(1,7)
    knight = factory.create_piece("NW", (1, 7), game.user_input_queue)
    knight.piece_id = "NW0"
    knight._state._physics.piece_id = "NW0"
    
    # הוסף את הכלי למשחק
    game.pieces = [knight]
    
    print(f"🐎 סוס נוצר במיקום: {knight._state._physics.cell}")
    
    # סימולציה של בחירת כלי (שחקן 1)
    game.selected_piece_player1 = knight
    game.cursor_pos_player1 = (1, 7)  # מגדיר את מיקום הסמן
    print(f"✅ בחרתי את הכלי: {knight.piece_id}")
    
    # סימולציה של לחיצה על אותו מיקום (1,7)
    print("🖱️ לוחץ על אותו מיקום לקפיצה במקום...")
    game._select_piece_player1()
    
    # המתן לקפיצה
    print("⏱️ מחכה לאנימציית קפיצה...")
    start_time = time.time()
    while time.time() - start_time < 4:  # 4 שניות
        # עדכן את הכלי
        current_time = int(time.time() * 1000)
        knight.update(current_time)
        
        # עבד את התור
        while not game.user_input_queue.empty():
            cmd = game.user_input_queue.get()
            game._process_input(cmd)
        time.sleep(0.1)
    
    final_pos = knight._state._physics.cell
    print(f"🐎 מיקום סופי של הסוס: {final_pos}")
    
    # בדוק שהסוס נשאר באותו מיקום אחרי הקפיצה
    if final_pos == (1, 7):
        print("✅ בדיקת קפיצה במקום עברה בהצלחה! הסוס קפץ וחזר לאותו מיקום.")
        return True
    else:
        print(f"❌ בדיקת קפיצה במקום נכשלה! צפוי: (1, 7), מתקבל: {final_pos}")
        return False

if __name__ == "__main__":
    success = test_jump_in_place()
    print("🏁 סיום בדיקת קפיצה במקום")
