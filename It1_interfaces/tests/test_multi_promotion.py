#!/usr/bin/env python3
"""
בדיקה של הכתרה עם תנועות מרובות.
נזיז חייל פעמיים כדי להגיע לשורה 0.
"""

import time
import pathlib
from Board import Board
from Game import Game
from PieceFactory import PieceFactory
from Command import Command
from img import Img

def test_multi_move_promotion():
    print("👑 בדיקת הכתרה עם תנועות מרובות...")
    
    # יצירת לוח ומפעל כלים כמו במשחק האמיתי
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
    
    # צור חייל לבן ב-(2,2) כדי שיהיה לו מקום לזוז
    pawn = factory.create_piece("PW", (2, 2), game.user_input_queue)
    pawn.piece_id = "PW0"
    pawn._state._physics.piece_id = "PW0"
    
    # הוסף את הכלי למשחק
    game.pieces = [pawn]
    
    print(f"🔵 חייל נוצר במיקום: {pawn._state._physics.cell}")
    
    def move_and_wait(target_x, target_y, description):
        print(f"🎯 {description}: מזיז ל-({target_x}, {target_y})")
        game._move_piece(pawn, target_x, target_y, 1)
        
        # המתן לתנועה
        start_time = time.time()
        while time.time() - start_time < 6:
            current_time = int(time.time() * 1000)
            for piece in game.pieces[:]:
                piece.update(current_time)
            
            while not game.user_input_queue.empty():
                cmd = game.user_input_queue.get()
                game._process_input(cmd)
            time.sleep(0.1)
        
        current_pos = pawn._state._physics.cell if pawn in game.pieces else "הוסר"
        print(f"📍 מיקום נוכחי: {current_pos}")
        print(f"📋 כלים: {[p.piece_id for p in game.pieces]}")
        return current_pos
    
    # תנועה ראשונה: מ-(2,2) ל-(2,1)
    move_and_wait(2, 1, "תנועה 1")
    
    # תנועה שנייה: מ-(2,1) ל-(2,0) - הכתרה!
    move_and_wait(2, 0, "תנועה 2 - הכתרה")
    
    # בדוק תוצאה
    piece_ids = [p.piece_id for p in game.pieces]
    has_queen = any("QW" in piece_id for piece_id in piece_ids)
    has_original_pawn = "PW0" in piece_ids
    
    if has_queen and not has_original_pawn:
        print("✅ הכתרה הצליחה! חייל הפך למלכה.")
        return True
    elif has_original_pawn and not has_queen:
        print("❌ הכתרה נכשלה! החייל לא הפך למלכה.")
        return False
    else:
        print(f"🤔 מצב מוזר: יש מלכה={has_queen}, יש חייל מקורי={has_original_pawn}")
        return False

if __name__ == "__main__":
    success = test_multi_move_promotion()
    print("🏁 סיום בדיקת הכתרה מרובת תנועות")
