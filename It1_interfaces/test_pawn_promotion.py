#!/usr/bin/env python3
"""
בדיקה פשוטה להכתרת חיילים.
זז חייל לבן לשורה 0 ובודק שהוא נהפך למלכה.
"""

import time
import pathlib
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from Command import Command
from img import Img

def test_pawn_promotion():
    print("👑 בדיקת הכתרת חיילים...")
    
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
    
    # צור חייל לבן ב-(1,3) - קרוב לשורה 0
    pawn = factory.create_piece("PW", (1, 3), game.user_input_queue)
    pawn.piece_id = "PW_test"
    pawn._state._physics.piece_id = "PW_test"
    
    # הוסף את הכלי למשחק
    game.pieces = [pawn]
    
    print(f"🔵 חייל נוצר במיקום: {pawn._state._physics.cell}")
    print(f"📋 כלים לפני הכתרה: {[p.piece_id for p in game.pieces]}")
    
    # הזז את החייל לשורה 0 (הכתרה) - מ-(1,3) ל-(0,3)
    move_cmd = Command(type="move", target=(0, 3), piece_id="PW_test", timestamp=int(time.time() * 1000))
    pawn.on_command(move_cmd, int(time.time() * 1000))
    
    # המתן לתנועה ולהכתרה
    print("⏱️ מחכה לתנועה ולהכתרה...")
    start_time = time.time()
    while time.time() - start_time < 6:  # 6 שניות
        # עדכן את הכלי
        current_time = int(time.time() * 1000)
        for piece in game.pieces[:]:  # copy the list since it might change
            piece.update(current_time)
        
        # עבד את התור
        while not game.user_input_queue.empty():
            cmd = game.user_input_queue.get()
            game._process_input(cmd)
        time.sleep(0.1)
    
    print(f"📋 כלים אחרי הכתרה: {[p.piece_id for p in game.pieces]}")
    
    # בדוק שיש מלכה חדשה ולא חייל
    piece_ids = [p.piece_id for p in game.pieces]
    has_queen = any("QW" in piece_id for piece_id in piece_ids)
    has_pawn = "PW_test" in piece_ids
    
    if has_queen and not has_pawn:
        print("✅ בדיקת הכתרה עברה בהצלחה! החייל הפך למלכה.")
        
        # בדוק את מיקום המלכה
        for piece in game.pieces:
            if "QW" in piece.piece_id:
                queen_pos = piece._state._physics.cell
                print(f"👑 המלכה החדשה {piece.piece_id} נמצאת במיקום: {queen_pos}")
                if queen_pos == (0, 3):
                    print("✅ המלכה במיקום הנכון!")
                    return True
                else:
                    print(f"❌ המלכה במיקום שגוי! צפוי: (0, 3), מתקבל: {queen_pos}")
                    return False
    else:
        print(f"❌ בדיקת הכתרה נכשלה! יש מלכה: {has_queen}, יש חייל: {has_pawn}")
        print(f"כלים: {piece_ids}")
        return False

if __name__ == "__main__":
    success = test_pawn_promotion()
    print("🏁 סיום בדיקת הכתרה")
