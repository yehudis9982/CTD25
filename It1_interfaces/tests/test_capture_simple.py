#!/usr/bin/env python3
"""
בדיקה פשוטה למנגנון התפיסה.
נוצר תרחיש פשוט: חייל לבן זזה למיקום של חייל שחור ובודק שהחייל השחור נמחק.
"""

import time
import pathlib
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from Command import Command
from img import Img

def test_simple_capture():
    print("🎯 בדיקת תפיסה פשוטה...")
    
    # יצירת לוח ומפעל כלים
    from img import Img
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
    
    # צור שני חיילים: לבן ב-(1,1) ושחור ב-(1,2)
    white_pawn = factory.create_piece("PW", (1, 1), game.user_input_queue)
    white_pawn.piece_id = "PW_test"
    white_pawn._state._physics.piece_id = "PW_test"
    
    black_pawn = factory.create_piece("PB", (1, 2), game.user_input_queue) 
    black_pawn.piece_id = "PB_test"
    black_pawn._state._physics.piece_id = "PB_test"
    
    # הוסף את הכלים למשחק
    game.pieces = [white_pawn, black_pawn]
    
    print(f"📋 כלים לפני התפיסה: {[p.piece_id for p in game.pieces]}")
    
    # הזז את החייל הלבן למיקום החייל השחור
    move_cmd = Command(type="move", target=(1, 2), piece_id="PW_test", timestamp=int(time.time() * 1000))
    white_pawn.on_command(move_cmd, int(time.time() * 1000))
    
    # המתן למשך זמן מספיק לתנועה ולהגעה (5 שניות)
    print("⏱️ מחכה לתנועה ולתפיסה...")
    start_time = time.time()
    while time.time() - start_time < 6:  # 6 שניות
        # עדכן את כל הכלים
        current_time = int(time.time() * 1000)
        for piece in game.pieces[:]:  # copy the list since it might change
            piece.update(current_time)
        
        # עבד את התור - loop שמעבד פקודות
        while not game.user_input_queue.empty():
            cmd = game.user_input_queue.get()
            game._process_input(cmd)
        time.sleep(0.1)
    
    print(f"📋 כלים אחרי התפיסה: {[p.piece_id for p in game.pieces]}")
    
    # בדוק שהחייל השחור נמחק
    piece_ids = [p.piece_id for p in game.pieces]
    if "PB_test" not in piece_ids and "PW_test" in piece_ids:
        print("✅ בדיקת תפיסה עברה בהצלחה! החייל השחור נמחק.")
        return True
    else:
        print("❌ בדיקת תפיסה נכשלה! החייל השחור לא נמחק.")
        print(f"כלים שנותרו: {piece_ids}")
        return False

if __name__ == "__main__":
    success = test_simple_capture()
    print("🏁 סיום בדיקה")
