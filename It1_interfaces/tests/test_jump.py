#!/usr/bin/env python3
"""
בדיקה פשוטה למנגנון הקפיצה.
נוצר תרחיש פשוט: סוס שחור קופץ מ-(1,0) ל-(3,1) - מהלך L קלאסי של סוס.
"""

import time
import pathlib
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from Command import Command
from img import Img

def test_knight_jump():
    print("🐎 בדיקת קפיצת סוס...")
    
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
    
    # צור סוס שחור ב-(1,0)
    knight = factory.create_piece("NB", (1, 0), game.user_input_queue)
    knight.piece_id = "NB_test"
    knight._state._physics.piece_id = "NB_test"
    
    # הוסף את הכלי למשחק
    game.pieces = [knight]
    
    print(f"🐎 סוס נוצר במיקום: {knight._state._physics.cell}")
    
    # שלח פקודת קפיצה למיקום (3,1) - מהלך L קלאסי של סוס
    jump_cmd = Command(type="jump", target=(3, 1), piece_id="NB_test", timestamp=int(time.time() * 1000))
    knight.on_command(jump_cmd, int(time.time() * 1000))
    
    # המתן זמן קצר לקפיצה
    print("⏱️ מחכה לקפיצה...")
    start_time = time.time()
    while time.time() - start_time < 3:  # 3 שניות
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
    
    # בדוק שהסוס הגיע למיקום הנכון
    if final_pos == (3, 1):
        print("✅ בדיקת קפיצה עברה בהצלחה! הסוס קפץ למיקום הנכון.")
        return True
    else:
        print(f"❌ בדיקת קפיצה נכשלה! צפוי: (3, 1), מתקבל: {final_pos}")
        return False

if __name__ == "__main__":
    success = test_knight_jump()
    print("🏁 סיום בדיקת קפיצה")
